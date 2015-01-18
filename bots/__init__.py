from twisted.words.protocols import irc
from twisted.internet import task
from twisted.internet import defer
from twisted.python import log

from initial import Initial

class IrcBot(irc.IRCClient):
    def __init__(self, config):
        self.config = config

        self.nickname = config.get('irc', 'nick')
        self.channel = config.get('meeting', 'channel')
        self.operators = config.options('operators')
        self.initialops = []

        self.stage = Initial(self)

        # A ticker for regular tasks to happen on
        self.ticker = task.LoopingCall(self.tick)
        self.ticker.start(10)

        self._namescallback = {}

    def setStage(self, stageclass):
        self.stage = stageclass(self)

    def tick(self):
        self.stage.tick()

    def signedOn(self):
        self.stage.signedOn()

    def joined(self, channel):
        self.stage.joined(channel)

    def noticed(self, user, channel, msg):
        self.stage.noticed(user, channel, msg)

    def privmsg(self, user, channel, msg):
        self.stage.privmsg(user, channel, msg)

    def userJoined(self, user, channel):
        self.stage.userJoined(user, channel)

    def userLeft(self, user, channel):
        self.stage.userLeft(user, channel)

    def userQuit(self, user, channel):
        self.stage.userLeft(user, channel)

    def userKicked(self, kickee, channel, kicker, message):
        self.stage.userLeft(kickee, channel)

    def userRenamed(self, oldname, newname):
        self.stage.userRenamed(oldname, newname)

    def modeChanged(self, user, channel, set, modes, args):
        self.stage.modeChanged(user, channel, set, modes, args)

    def irc_unknown(self, prefix, command, params):
        if command.startswith("ERR_"):
            log.msg("Received unknown error: %s/%s/%s" % (prefix, command, params))

    # Callables that do something
    def announce(self, msg):
        if hasattr(msg, '__iter__'):
            for m in msg:
                log.msg("SEND: %s" % m)
                self.msg(self.channel, m)
        else:
            log.msg("SEND: %s" % msg)
            self.msg(self.channel, msg)

    def channelnotice(self, msg):
        if hasattr(msg, '__iter__'):
            for m in msg:
                log.msg("ANNOUNCE: %s" % m)
                self.notice(self.channel, m)
        else:
            log.msg("ANNOUNCE: %s" % msg)
            self.notice(self.channel, msg)


    # Implement the names() command, to get list of users in channel
    def names(self, channel):
        d = defer.Deferred()
        if channel not in self._namescallback:
            self._namescallback[channel] = ([], [])

        self._namescallback[channel][0].append(d)
        self.sendLine("NAMES %s" % channel)
        return d

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2].lower()
        nicklist = params[3].split(' ')

        if channel not in self._namescallback:
            return

        n = self._namescallback[channel][1]
        n += nicklist

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1].lower()
        if channel not in self._namescallback:
            return

        callbacks, namelist = self._namescallback[channel]

        for cb in callbacks:
            cb.callback(namelist)

        del self._namescallback[channel]
