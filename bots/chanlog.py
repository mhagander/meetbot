from datetime import datetime

class ChannelLog(object):
    def __init__(self):
        self.logfile = None

    def open(self, filename):
        self.logfile = open(filename, 'a')
        self.log('**system**', '*** opening logfile')

    def log(self, user, line):
        self.logfile.write(u"{0:%Y-%m-%d %H:%M:%S} | {1} | {2}\n".format(datetime.now(), user, line))
        self.logfile.flush()


chanlog = ChannelLog()
