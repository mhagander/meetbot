from twisted.python import log

from stages import BaseStage
from main import Main

class WaitOp(BaseStage):
    def __init__(self, *args, **kwargs):
        super(WaitOp, self).__init__(*args, **kwargs)
        self.nag()

    def tick(self):
        self.nag()

    def nag(self):
        self.announce("Please make me op so I can do my work!")

    def modeChanged(self, user, channel, set, modes, args):
        if channel == self.bot.channel and set == True and modes == 'o' and self.bot.nickname in args:
            log.msg("Received op")
            self.announce("Thank you!")

            # Configure channel mode, now that we are op
            log.msg("Configuring channel to be invite only")
            self.bot.mode(self.bot.channel, True, "i")

            log.msg("Fetching current userlist, to kick people")
            self.bot.names(self.bot.channel).addCallback(self.got_names)

    def got_names(self, nicklist):
        log.msg("Current nicks in channel: %s" % nicklist)
        for n in nicklist:
            if not n: continue # Sometimes we get the empty string included
            if n == '@{0}'.format(self.bot.nickname): continue
            if n.startswith('@'):
                if n[1:] in self.bot.operators:
                    self.bot.initialops.append(n[1:])
                    continue
                n = n[1:] # Strip the @ part from op, so we can kick them

            # Else kick this person out so we can get the registry going
            log.msg("Kicking %s out of the channel to prepare for meeting." % n)
            self.bot.kick(self.bot.channel, n, "This channel is now under bot control. Please knock to get an invite and re-join. Apologies for the annoyance.")
        for p in self.bot.initialops:
            log.msg("Not kicking {0} who is an approved op".format(p))
            self.announce("{0}: you are listed as an approved op, so you don't get kicked :P".format(p))

        self.bot.setStage(Main)
