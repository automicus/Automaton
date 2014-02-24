# Levels:
#   0: debug
#   1: info
#   2: warning
#   3: error
#   4: critical
#   5: none

from datetime import datetime
import sys

class logger(object):

    levels = {'debug': 0,
        'info': 1,
        'warning': 2,
        'error': 3,
        'critical': 4,
        'nolog': 5}

    def __init__(self, fname, file_lvl, screen_lvl):
        if type(file_lvl) is str:
            file_lvl = self.levels[file_lvl]
        if type(screen_lvl) is str:
            screen_lvl = self.levels[screen_lvl]

        self._file = logFile(open(fname, 'w'), file_lvl)
        self._screen = logFile(sys.stdout, screen_lvl)
        self._lastLvl = 1

    def _getTimeStamp(self):
        return datetime.now()

    def _write(self, msg, lvl, noheader=False):
        stamp = self._getTimeStamp()
        self._file.write(stamp, msg, lvl, noheader)
        self._screen.write(stamp, msg, lvl, noheader)

    def setLevels(self, file_lvl, screen_lvl):
        if type(file_lvl) is str:
            file_lvl = self.levels[file_lvl]
        if type(screen_lvl) is str:
            screen_lvl = self.levels[screen_lvl]

        self._file.setLevel(file_lvl)
        self._screen.setLevel(screen_lvl)

    def debug(self, msg):
        self._write(msg, 0)
        self._lastLvl = 0

    def info(self, msg):
        self._write(msg, 1)
        self._lastLvl = 1

    def warning(self, msg):
        self._write(msg, 2)
        self._lastLvl = 2

    def error(self, msg):
        self._write(msg, 3)
        self._lastLvl = 3

    def critical(self, msg):
        self._write(msg, 4)
        self._lastLvl = 4

    def continuation(self, msg):
        self._write(msg, self._lastLvl, noheader=True)


class logFile(object):

    def __init__(self, f, lvl):
        self._f = f
        self._lvl = lvl

    def setLevel(self, lvl):
        self._lvl = lvl

    def write(self, stamp, msg, lvl, noheader=False):
        if lvl >= self._lvl:
            output = '[' + stamp.isoformat() + ']    '
            output += str(lvl) + '    '
            if noheader:
                output = ' ' * len(output)
            self._f.write(output + msg + '\n')
