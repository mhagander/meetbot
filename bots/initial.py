from twisted.python import log

from .stages import BaseStage

from .prejoin import PreJoin

class Initial(BaseStage):
    def signedOn(self):
        log.msg("Signed on, setting my mode to allow DMs")
        self.bot.sendLine("MODE {} -R".format(self.bot.config.get('irc', 'nick')))

        if self.bot.config.has_option('irc', 'nickservpwd'):
            # Authenticate with nickserv, then wait for that to actually
            # complete.
            log.msg("Sending authentication message to nickserv...")
            self.msg("nickserv", "identify %s %s" % (
                self.bot.config.get('irc', 'nick'),
                self.bot.config.get('irc', 'nickservpwd')))
        else:
            log.msg("Signed on. Nickserv authentication is disabled.")
            self.join_channel()

    def join_channel(self):
        log.msg("Attempting to join %s." % self.bot.channel)

        self.bot.setStage(PreJoin)
        self.bot.join(self.bot.channel)

    def noticed(self, user, channel, msg):
        if user.startswith('NickServ!NickServ@services'):
            # Message from nickserv! Could be our auth completion
            if msg.startswith('You are now identified'):
                log.msg("Nickserv confirms login.")
                self.join_channel()
                return
            log.msg("Message from nickserv: %s" % msg)
        else:
            log.msg("Noticed in %s by %s: %s" % (channel, user, msg))
