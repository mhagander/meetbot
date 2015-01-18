#!/usr/bin/env python
#
# Simple meeting-controlling IRC bot
#


from twisted.internet import reactor, protocol, ssl

from ConfigParser import ConfigParser

from bots import IrcBot

config = ConfigParser()

class IrcBotFactory(protocol.ReconnectingClientFactory):
    initialDelay = 10

    def buildProtocol(self, addr):
        return IrcBot(config)

    def clientConnectionFailed(self, connector, reason):
        print "Factory: connection failed (%s)" % reason
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        print "Factory: connection lost"
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

if __name__=="__main__":
    config.read('meetingbot.ini')

    if config.has_option('irc', 'ssl') and config.getint('irc', 'ssl') == 1:
        reactor.connectSSL(config.get('irc', 'server'),
                           config.getint('irc', 'port'),
                           IrcBotFactory(),
                           ssl.ClientContextFactory())
    else:
        reactor.connectTCP(config.get('irc', 'server'),
                           config.getint('irc', 'port'),
                           IrcBotFactory())
    reactor.run()
