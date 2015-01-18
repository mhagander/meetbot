from stages import BaseStage

from waitop import WaitOp

class PreJoin(BaseStage):
    def joined(self, channel):
        # Joined a channel, check if it's ours
        print "Joined channel %s, waiting for op" % channel
        self.bot.setStage(WaitOp)
