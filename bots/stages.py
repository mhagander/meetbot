from twisted.python import log

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

    def msg(self, user, msg):
        if hasattr(msg, '__iter__'):
            for m in msg:
                log.msg("SENDUSER: {0}: {1}".format(user, m))
                self.bot.msg(user, m)
        else:
            log.msg("SENDUSER: {0}: {1}".format(user, msg))
            self.bot.msg(user, msg)


    def announce(self, msg):
        self.bot.announce(msg)

    def channelnotice(self, msg):
        self.bot.channelnotice(msg)
