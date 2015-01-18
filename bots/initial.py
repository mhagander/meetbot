from twisted.python import log

from stages import BaseStage

from prejoin import PreJoin

class Initial(BaseStage):
    def signedOn(self):
        log.msg("Signed on. Now attempting to join %s." % self.bot.channel)

        # Should be set to authenticate instead, but now we will
        # just join the channel
        self.bot.setStage(PreJoin)
        self.bot.join(self.bot.channel)
