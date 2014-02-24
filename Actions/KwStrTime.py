from datetime import datetime, timedelta
import astral
import re


class dt_test(datetime):
    def __getattribute__(self, name):
        print 'DT TEST __getattribute__: ' + name
        return super(dt_test, self).__getattribute__(name)

    def __getattr__(self, name):
        print 'DT TEST __getattr__: ' + name
        return super(dt_test, self).__getattr__(name)


class Time(object):

    _keywords = ['dusk', 'dawn', 'solar_noon', 'sunrise', 'sunset']
    _valfuns = ['__add__', '__eq__', '__format__', '__ge__', '__gt__',
                '__hash__', '__le__', '__lt__', '__ne__', '__radd__',
                '__rsub__', '__sizeof__', '__sub__', 'astimezone', 'combine',
                'ctime', 'date', 'day', 'dst', 'fromordinal', 'fromtimestamp',
                'hour', 'isocalendar', 'isoformat', 'isoweekday', 'max',
                'microsecond', 'min', 'minute', 'month', 'now', 'replace',
                'resolution', 'second', 'strftime', 'strptime', 'time',
                'timetuple', 'timetz', 'toordinal', 'tzinfo', 'tzname',
                'utcfromtimestamp', 'utcnow', 'utcoffset',
                'utctimetuple', 'weekday', 'year']

    def __init__(self, kw_str, loc_str, loc=None):
        # store strings
        self._kw_str = kw_str
        self._loc_str = loc_str
        # lookup location
        if loc is None:
            lkp = astral.GoogleGeocoder()
            self.loc = lkp[loc_str]
        else:
            self.loc = loc
        # evaluate string
        self._val = None
        self.calc()

    def __getattr__(self, name):
        print 'TIME __getattr__: ' + name
        #if name in self._valfuns and self._val is not None:
        #    return getattr(self._val, name)
        #else:
        #    return super(Time, self).__getattribute__(name)
        return getattr(self._val, name)

    def __getattribute__(self, name):
        print 'TIME __getattribute__: ' + name
        return super(Time, self).__getattribute__(name)

    def __dir__(self):
        #out = self._valfuns + ['kw_str', 'calc', '__init__',
        #                       '__getattr__', '__str__', '__repr__',
        #                       '__dir__']
        #return sorted(out)
        return sorted(dir(self._val) +
                      ['kw_str', 'loc_str', 'datetime',
                       'today', 'tomorrow', 'calc'])

    def __str__(self):
        return self.kw_str + ' [' + self.strftime('%c') + ']'

    def __repr__(self):
        return 'KwStrTime.Time(' + self.__str__() + ', ' + self.loc_str + ')'

    @property
    def kw_str(self):
        return self._kw_str

    @kw_str.setter
    def kw_str(self, kw_str):
        self._kw_str = kw_str
        self.calc()

    @property
    def loc_str(self):
        return self._loc_str

    @loc_str.setter
    def loc_str(self, loc_str):
        self._loc_str = loc_str
        # lookup location
        lkp = astral.GoogleGeocoder()
        self.loc = lkp[loc_str]

    @property
    def datetime(self):
        return self._val

    def today(self):
        return datetime.today().replace(tzinfo=self.loc.tz)

    def tomorrow(self):
        return self.today() + timedelta(days=1)

    def calc(self):
        dt = self.today()
        value = self._calc(dt)
        if value < dt:
            value = self._calc(self.tomorrow())
        self._val = value

    def _calc(self, dt=None):
        # extract keyword time
        kw_dt = self.__parse_kw__(dt)
        # extract string time
        str_dt = self.__parse_tstr__(dt)
        # parse operator
        op = -1 if '-' in self.kw_str else 1

        # parse results
        if kw_dt is None and str_dt is None:
            # invalid entry
            raise ValueError('Invalid string:' + self.kw_str)
        elif kw_dt is not None:
            # keyword entry
            value = kw_dt
            if str_dt is not None:
                delta = timedelta(hours=str_dt.hour,
                                  minutes=str_dt.minute,
                                  seconds=str_dt.second)
                value += (op * delta)
        else:
            # time string entry
            value = str_dt
        return value

    def __parse_kw__(self, dt=None):
        # get datetime for solar calcs
        if dt is None:
            dt = self.today()

        for key in self._keywords:
            if self.kw_str.startswith(key):
                # get solar function
                sol_fun = getattr(self.loc, key)
                # get next solar event
                return sol_fun(dt)

    def __parse_tstr__(self, dt=None):
        # get datetime to build time off of
        if dt is None:
            dt = self.today()

        # find time in string
        s = re.search('[0-9]*[0-9]:[0-9][0-9]:[0-9][0-9]', self.kw_str)
        if s is not None:
            # parse string
            t_str = s.string[s.start():s.end()]
            time = datetime.strptime(t_str, '%H:%M:%S')
            # get next event
            event = time.replace(year=dt.year,
                                 month=dt.month,
                                 day=dt.day,
                                 tzinfo=dt.tzinfo)
            return event
