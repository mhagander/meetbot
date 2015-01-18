import datetime
import time
import shlex
import urllib

import simplejson
import twisted.web.client
from twisted.python import log

from stages import BaseStage

class Poll(object):
    def __init__(self, question, length, options, maxvotes):
        self.question = question
        self.options = options
        self.length = length
        self.starttime = time.time()
        self.endtime = self.starttime + self.length*60
        self.lastnotify = self.starttime
        self.maxvotes = maxvotes
        self.votes = {}

    def time_to_notify(self):
         return (time.time() - self.lastnotify > 30)

    def status_text(self):
        t = self.endtime - time.time()
        return "poll '%s' closes in %s at %s (%s votes cast so far)" % (
            self.question,
            datetime.timedelta(seconds=int(t)),
            time.strftime("%H:%M:%S", time.localtime(self.endtime)),
            len(self.votes),
            )

    def notify_text(self):
        self.lastnotify = time.time()
        return "Reminder: %s" % self.status_text()

    def close_text(self):
        yield "Total votes cast %s (%s eligible)" % (len(self.votes), self.maxvotes)
        for i in range(0,len(self.options)):
            n = len([v for v in self.votes.values() if v==i+1])
            yield "{0}: {1} votes ({2}%)".format(
                self.options[i],
                n,
                int(n*100/len(self.votes)),
                )
        yield '--'

    def time_to_close(self):
        if len(self.votes) >= self.maxvotes:
            # Everybody has voted, no point in keeping it open any longer
            return True
        return (time.time() >= self.endtime)

    def get_option_strings(self):
        return ['"!vote %s" to vote "%s"' % (i+1, self.options[i]) for i in range(0,len(self.options))]

    def make_vote(self, user, vote):
        try:
            v = int(vote)
            if v < 1 or v > len(self.options)+1:
                return "Vote must be a number between 1 and {0}".format(len(self.options)+1)

            update = self.votes.has_key(user)
            self.votes[user] = v

            log.msg("User {0}, '{1}' has been {2} to {3}".format(
                user,
                self.question,
                update and 'updated to' or 'cast as',
                self.options[v-1]))

            return "Your vote for '{0}' has been {1} {2}".format(
                self.question,
                update and 'updated to' or 'cast as',
                self.options[v-1])
        except ValueError:
            return "Vote has to be a number!"
        except Exception, ex:
            self.log("Exception when casting vote for %s: %s" % (user, ex))
            return "Unknown error occurred with voting. Sorry, please try again!"

class Main(BaseStage):
    def __init__(self, bot):
        super(Main, self).__init__(bot)
        self.activepoll = None
        self.isrunning = False

        # Start by adding entries for all our operators
        self.users = {}
        for o in self.bot.operators:
            n = self.bot.config.get('operators', o)
            self.users[o] = {'username':n, 'name': n, 'secret': '', 'active': o in self.bot.initialops}
        self.announce("Entering main bot running mode")

    def noticed(self, user, channel, msg):
        log.msg("Noticed: %s/%s/%s" % (user, channel, msg))

    def privmsg(self, user, channel, msg):
        # If channel starts with #, it's a regular IRC message.
        # If channel doesn't, then it's a private msg
        if channel == self.bot.channel:
            log.msg("CHANNEL: %s" % msg)
        elif channel.startswith('#'):
            log.msg("Received message on unknown channel %s: %s" % (channel, msg))
            return # Don't process that
        elif channel == self.bot.nickname and not msg.startswith('!'):
            log.msg("Received '{0}' from {1}, instructed about prefix".format(msg, user))
            self.msg(user, "All commands must be prefixed with an exclamation mark (!). Use !help for information")

        # Trim out part of the username
        user = user.split('!')[0]

        if msg.startswith('!'):
            s = shlex.split(msg[1:])
            cmd = s.pop(0)
            if cmd == 'hello':
                self.msg(user, 'Hi there')
            if hasattr(self, 'cmd_%s' % cmd):
                proc = getattr(self, 'cmd_%s' % cmd)
                if hasattr(proc, 'oponly'):
                    # Operator only command
                    if not user in self.bot.operators:
                        log.msg('User {0} tried to execute oponly command {1}!'.format(user, cmd))
                        self.msg(user, "Sorry, command restricted to operators!")
                        return
                if not hasattr(proc, 'public'):
                    # This user must be in the channel to be ok!
                    if not self.users.has_key(user):
                        log.msg('User {0} tried to execute command {1} without being in channel'.format(user, cmd))
                        self.msg(user, "Sorry, command not available unless you have joined the channel!")
                        return
                if hasattr(proc, 'paramcount'):
                    if proc.paramcount[0] and len(s) < proc.paramcount[0]:
                        return self.help_command(user, cmd, 'not enough parameters')
                    if proc.paramcount[1] and len(s) > proc.paramcount[1]:
                        return self.help_command(user, cmd, 'too many parameters')
                getattr(self, 'cmd_%s' % cmd)(user, channel, s)
            else:
                self.msg(user, 'Unknown command %s' % cmd)

    def help_command(self, user, command, reason=None):
        if reason:
            self.msg(user, 'Syntax error: %s' % reason)
        if hasattr(self, 'cmd_%s' % command):
            c = getattr(self,'cmd_%s' % command)
            if hasattr(c, 'oponly') and not user in self.bot.operators:
                self.msg(user, "Access denied")
            else:
                self.msg(user, "Syntax: %s" % c.syntax)
        else:
            self.msg(user, 'Unknown command %s' % command)

    def cmd_help(self, user, channel, s):
        op = (user in self.bot.operators)
        if len(s) == 0:
            self.msg(user, "List of commands:")
            for a in dir(self):
                if a.startswith("cmd_"):
                    a = getattr(self, a)
                    if hasattr(a, 'oponly') and not op:
                        continue
                    if hasattr(a, 'syntax'):
                        self.msg(user, getattr(a, 'syntax'))
            self.msg(user, "End of list of commands")
        else:
            self.help_command(user, s[0])
    cmd_help.syntax = '!help <command>'
    cmd_help.paramcount = (0,1)

    def cmd_beginmeeting(self, user, channel, s):
        self.isrunning = True
        self.channelnotice("This meeting is now starting.")
    cmd_beginmeeting.syntax = '!beginmeeting'
    cmd_beginmeeting.paramcount = (0,0)
    cmd_beginmeeting.oponly = True

    def cmd_closemeeting(self, user, channel, s):
        if self.activepoll:
            return self.msg(user, "This meeting has an open poll, so it cannot be closed.")
        self.isrunning = False
        self.channelnotice("This meeting is now finished.")
    cmd_closemeeting.syntax = '!closemeeting'
    cmd_closemeeting.paramcount = (0,0)
    cmd_closemeeting.oponly = True

    def cmd_startpoll(self, user, channel, s):
        if not self.isrunning:
            return self.msg(user, "This meeting is not active, so we cannot start a poll!")

        if self.activepoll:
            return self.msg(user, "There is already an active poll, cannot start a new one")

        poll = Poll(s[0], int(s[1]), s[2:], len([u for u in self.users.values() if u['active']]))
        self.channelnotice("Poll is starting for question '%s'" % poll.question)
        self.announce("To vote, send commands:")
        self.announce(poll.get_option_strings())
        self.announce("Voting begins...")
        self.activepoll = poll

    cmd_startpoll.syntax = '!startpoll <question> <minutes> <option1> <option2>[ <option3>...]'
    cmd_startpoll.paramcount = (4, None)
    cmd_startpoll.oponly = True

    def cmd_abortpoll(self, user, channel, s):
        if not self.activepoll:
            return self.msg(user, "There is no active poll to vote on!")

        if not s[0] == 'REALLY':
            return self.msg(user, "You must specify the parameter REALLY (literally) to confirm you really want to abort..")

        self.channelnotice("Current poll (%s) is being aborted!" % self.activepoll.question)
        self.announce("All votes cast have been removed.")
        self.activepoll = None
        self.msg(user, "Poll aborted")
    cmd_abortpoll.syntax = '!abortpoll REALLY'
    cmd_abortpoll.paramcount = (1,1)
    cmd_abortpoll.oponly = True

    def cmd_vote(self, user, channel, s):
        if not self.activepoll:
            return self.msg(user, "There is no active poll to vote on!")
        self.msg(user, self.activepoll.make_vote(user, s[0]))
        if self.activepoll.time_to_close():
            self.channelnotice("Voting on '%s' is now closed." % self.activepoll.question)
            self.announce(self.activepoll.close_text())
            self.activepoll = None
    cmd_vote.syntax = '!vote <option number>'
    cmd_vote.paramcount = (1,1)

    def cmd_status(self, user, channel, s):
        if self.isrunning:
            self.msg(user, "This meeting is currently active, and not accepting new attendees.")
        else:
            self.msg(user, "This meeting is not yet active")

        if self.activepoll:
            self.msg(user, "Active poll: %s" % self.activepoll.status_text())
        else:
            self.msg(user, "No active poll")
    cmd_status.syntax = '!status'
    cmd_status.paramcount = (0,0)
    cmd_status.oponly = True

    def cmd_knock(self, user, channel, s):
        # First thing we do is check if this user already knocked for this meeting
        if self.users.has_key(user):
            if self.users[user]['secret'] == s[0]:
                self.msg(user, "You are already registered for this meeting. Welcome back in!")
                self.bot.invite(user, self.bot.channel)
                return
            else:
                self.msg(user, "You are already registered for this meeting, but with a different secret key. That should not happen...")
                return

        if self.isrunning:
            self.msg(user, "This meeting has already started and no new attendees can join at this time. Sorry.")
            return

        url = "{0}?{1}".format(self.bot.config.get('meeting', 'authurl'), urllib.urlencode({
            's': s[0],
            'm': self.bot.config.getint('meeting', 'meetingid'),
            }))

        def _ok(val):
            try:
                r = simplejson.loads(val)
                # Ok, this user was found
                if r.has_key('err'):
                    self.msg(user, "Could not authenticate you: %s" % r['err'])
                    return

                # Now see if we already have this user with a different nick
                for n, u in self.users.items():
                    if r['username'] == u['username']:
                        self.msg(user, "You are already registered for this meeting with nick %s. Please use the same nick if you reconnect!" % n)
                        return

                # New user, better let them in then
                self.users[user] = r
                self.users[user]['secret'] = s[0]
                self.msg(user, "You are now properly identified, and welcome to join the meeting!")
                self.msg(user, "To do so, please join channel %s" % self.bot.channel)
                self.bot.invite(user, self.bot.channel)
                log.msg("Invited %s to the channel" % user)
            except Exception, e:
                self.msg(user, "Failed to talk to authentication server. Sorry, can't let you in at this point.")
                log.msg("Exception parsing auth callback data: %s" % e)

        def _err(err):
            self.msg(user, "Failed to contact authentication server. Sorry, can't let you in at this point.")
            log.msg("Failed in auth call to %s, err was: %s" % (url, err))

        log.msg('Initiating fetch of authentication url %s' % url)
        twisted.web.client.getPage(url).addCallbacks(callback=_ok, errback=_err)

    cmd_knock.syntax = '!knock <secret>'
    cmd_knock.paramcount = (1,1)
    cmd_knock.public = True

    def tick(self):
        # A timer tick!
        if self.activepoll:
            # Is it time to close?
            if self.activepoll.time_to_close():
                self.channelnotice("Voting on '%s' is now closed." % self.activepoll.question)
                self.announce(self.activepoll.close_text())
                self.activepoll = None
            # Might need to notify people about this!
            elif self.activepoll.time_to_notify():
                self.announce(self.activepoll.notify_text())


    # Keep track of users in the channel!
    def userJoined(self, user, channel):
        if channel != self.bot.channel:
            log.msg("User %s joined %s, why was I told?" % (user, channel))
            return

        # All users should've (a) knocked on the door, and (b) been invited. If they are not
        # in our hash, kick them immediately
        if not self.users.has_key(user):
            log.msg("Kicking user %s who just joined - not in registry!" % user)
            self.bot.kick(self.bot.channel, user, "User is not registered. Please knock first.")
            return

        self.users[user]['active'] = True
        self.announce("Welcome %s (%s)!" % (self.users[user]['name'], user))

    def userLeft(self, user, channel):
        if not self.users.has_key(user):
            log.msg("User %s left channel %s, but was not in my registry!" % (user, channel))
            return
        self.users[user]['active'] = False

    def userRenamed(self, user, channel):
        self.bot.kick(self.bot.channel, user, "Sorry, you cannot change nick while in a meeting. Our tracking of who said what would be lost. Please rejoin with your former nick.")
