#!/usr/bin/env python
#
# Simple meeting-controlling IRC bot
#

import sys

from twisted.internet import reactor, protocol, ssl
from twisted.python import log

from ConfigParser import ConfigParser

from bots.chanlog import chanlog
from bots import IrcBot

config = ConfigParser()

class IrcBotFactory(protocol.ReconnectingClientFactory):
    initialDelay = 10

    def buildProtocol(self, addr):
        return IrcBot(config)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Factory: connection failed (%s)" % reason)
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def clientConnectionLost(self, connector, reason):
        log.msg("Factory: connection lost")
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

if __name__=="__main__":
    if len(sys.argv) == 1:
        print "Reading configuration from meetingbot.ini"
        config.read('meetingbot.ini')
    elif len(sys.argv) == 2:
        print "Reading configuration from %s" % sys.argv[1]
        config.read(sys.argv[1])

    # Always log to stdout, as we expect this to run interactively. However,
    # if a logfile is configured, log to that as well.
    log.startLogging(sys.stdout)
    log.msg('Started stdout logging')
    if config.has_option('log', 'logfile'):
        log.startLogging(open(config.get('log', 'logfile'), 'a'))
        log.msg('Started logging to %s' % config.get('log', 'logfile'))
    else:
        log.msg('No log file configured, only logging to stdout')
    if config.has_option('log', 'chanlog'):
        chanlog.open(config.get('log', 'chanlog'))


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
