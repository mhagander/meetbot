from twisted.python import log

class BaseStage(object):
    def __init__(self, bot):
        self.bot = bot

    def signedOn(self):
        log.msg("Unhandled signedOn at stage %s" % self.__class__)

    def joined(self, channel):
        log.msg("Unhandled joined at stage %s" % self.__class__)

    def noticed(self, user, channel, msg):
        log.msg("Unhandled noticed at stage %s" % self.__class__)

    def privmsg(self, *args):
        log.msg("Unhandled privmsg at stage %s" % self.__class__)

    def tick(self): pass
    def userJoined(self, user, channel): pass
    def userLeft(self, user, channel): pass
    def modeChanged(self, user, channel, set, modes, args):
        print("Mode for {} in {} changed, set {}, modes {}".format(user, channel, set, modes))

    def msg(self, user, msg):
        if not isinstance(msg, str):
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
