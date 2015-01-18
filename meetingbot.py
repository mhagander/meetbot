#!/usr/bin/env python
#
# Simple meeting-controlling IRC bot
#


from twisted.internet import reactor, protocol

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

    # XXX: This should not be hardcoded, and it should use connectSSL
    if config.has_option('irc', 'ssl') and config.getint('irc', 'ssl') == 1:
        print "NO SSL YET, STEAL ELSEWHERE"
    else:
        reactor.connectTCP(config.get('irc', 'server'),
                           config.getint('irc', 'port'),
                           IrcBotFactory())
    reactor.run()
