from KwStrTime import Time
from threading import Thread, Timer
import astral
import datetime


class Event(object):

    def __init__(self, e, obj, dtstamp=None):
        self.e = e
        self.obj = obj
        if dtstamp is not None:
            self.dtstamp = dtstamp
        else:
            self.dtstamp = datetime.datetime.now()


class schedule(list):

    def __init__(self, log, loc_str):
        super(schedule, self).__init__()
        # create component
        self.log = log
        self._timer = None
        # lookup location
        self.loc_str = loc_str
        lkp = astral.GoogleGeocoder()
        try:
            self.loc = lkp[loc_str]
        except:
            self.loc = lkp['Greenwich, England']

    def clear(self):
        super(schedule, self).__init__()

    def now(self):
        return datetime.datetime.today().replace(tzinfo=self.loc.tz)

    def fireItems(self):
        # find events that need to fire
        now = self.now()
        pending = [event for event in self if event[1] <= now]
        # fire events
        for action in pending:
            e = Event('sched', action[1].kw_str, now)
            action[1].calc()
            t = Thread(target=action[2], args=[e])
            t.daemon = True
            t.start()
        # restart
        self._lastFire = now
        self._timer = None
        self.start()

    def sort(self):
        super(schedule, self).sort(key=self._sortkey)

    def _sortkey(self, row):
        return row[1]

    def append(self, name, t_str, fun):
        t = Time(t_str, self.loc_str, self.loc)
        super(schedule, self).append((name, t, fun))

    def start(self):
        if len(self) > 0:
            self.sort()
            if self._timer is not None:
                self._timer.cancel()
            self._timer = Timer(self.time2next(), self.fireItems)
            self._timer.daemon = True
            self._timer.start()
            self.log.info('Action Handler Next scheduled event in ' +
                          str(self.time2next()) + ' seconds.')

    def time2next(self):
        # find next entry
        dt_min = self.now()
        for entry in self:
            dt_min = min(dt_min, entry[1])

        # return difference in seconds
        return (dt_min.datetime - self.now()).total_seconds() + 0.005
