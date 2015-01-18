from twisted.python import log
from twisted.internet import reactor

from stages import BaseStage

from waitop import WaitOp

class PreJoin(BaseStage):
    def joined(self, channel):
        # Joined a channel, check if it's ours
        log.msg("Joined channel %s, waiting for op" % channel)
        self.bot.setStage(WaitOp)

    def joinFailed(self, command, params):
        # Failed to join the channel - let's go for a retry, but
        # log it first

        if command == 'ERR_INVITEONLYCHAN':
            log.msg("Failed to join channel - set to invite only!")
        else:
            log.msg("Failed to join channel!")

        log.msg("Going to retry in 30 seconds")

        def _retry_join():
            log.msg("Retrying join to %s" % self.bot.channel)
            self.bot.join(self.bot.channel)

        reactor.callLater(30, _retry_join)
