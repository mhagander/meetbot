
class BaseStage(object):
    def __init__(self, bot):
        self.bot = bot

    def signedOn(self): pass
    def joined(self): pass
    def noticed(self): pass
    def privmsg(self, *args): pass
    def tick(self): pass
    def userJoined(self, user, channel): pass
    def userLeft(self, user, channel): pass
    def modeChanged(self, user, channel, set, modes, args): pass

    def msg(self, channel, msg):
        if hasattr(msg, '__iter__'):
            for m in msg:
                self.bot.msg(channel, m)
        else:
            self.bot.msg(channel, msg)


    def announce(self, msg):
        self.bot.announce(msg)

    def channelnotice(self, msg):
        self.bot.channelnotice(msg)
