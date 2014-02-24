from datetime import datetime
from threading import Thread


class Event(object):
    def __init__(self, e, obj, dtstamp=None):
        self.e = e
        self.obj = obj
        if dtstamp is not None:
            self.dtstamp = dtstamp
        else:
            self.dtstamp = datetime.now()


class ReadOnlyException(Exception):
    def __str__(self):
        return 'ReadOnlyException(' + \
            'This value is read only and can not be edited.)'


class EventBindException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return 'EventBindException(' + self._msg + ')'


class MonitoredDict(object):

    def __init__(self):
        self._collection = {}

    def __setitem__(self, key, val):
        if key in self._collection.keys():
            self._collection[key].value = val
        else:
            self._collection[key] = MonitoredValue(val)

    def __getitem__(self, key):
        return self._collection[key]

    # iteration functions
    def __iter__(self):
        return self._collection.__iter__()

    def iteritems(self):
        return self._collection.iteritems()

    def itervalues(self):
        return self._collection.itervalues()

    def keys(self):
        return self._collection.keys()
    properties = keys

    def addValue(self, key, val):
        self._collection[key] = MonitoredValue(val)

    def addTrigger(self, key):
        self._collection[key] = MonitoredTrigger()

    def bindEvent(self, key, e, fun, *args):
        self._collection[key].bindEvent(e, fun, *args)

    def bindTrigger(self, key, fun):
        self._collection[key].bindTrigger(fun)

    def bindReporter(self, key, fun):
        self._collection[key].reporter = fun

    def set(self, key, val):
        if key in self._collection.keys():
            self._collection[key].set(val)
        else:
            self._collection[key] = MonitoredValue(val)


class MonitoredValue(object):

    events = ['changed',
              'changedUp',
              'changedDown',
              'changedTo',
              'changedToBetween']

    _event_nargs = [0, 0, 0, 1, 2]

    def __init__(self, initial=None, reporter=None):
        self._val = initial
        self._hooks = {}
        self.reporter = reporter
        self._id = datetime.now().isoformat()
        for event in self.events:
            self._hooks[event] = []

    def __getattr__(self, name):
        try:
            return super(MonitoredValue, self).__getattribute__(name)
        except AttributeError:
            return getattr(self._val, name)

    def __dir__(self):
        out = dir(self._val) + \
            ['value', 'set', 'raiseEvents', 'bindEvent', 'unbind']
        return sorted(out)

    def __int__(self):
        return int(self._val)

    def __float__(self):
        return float(self._val)

    @property
    def value(self):
        return self._val

    @value.setter
    def value(self, val):
        if self.reporter is not None:
            if self._val is not val:
                self.reporter(val)
                self.set(val)
        else:
            raise ReadOnlyException()

    def set(self, val):
        old_val = self._val
        self._val = val

        # value changed?
        if old_val != self._val:
            self.raiseEvents('changed')

            # changed up or down?
            if self._val > old_val:
                self.raiseEvents('changedUp')
            else:
                self.raiseEvents('changedDown')

            # changed to and changed between
            self.raiseEvents('changedTo')
            self.raiseEvents('changedToBetween')

    def raiseEvents(self, e):
        for hook in self._hooks[e]:
            if len(hook) == 1:
                target = hook[0](Event(e, self))
            elif len(hook) == 2 and hook[1] == self.value:
                target = hook[0](Event(e, self))
            elif len(hook) == 3 and hook[1] <= self.value and \
                    hook[2] >= self.value:
                target = hook[0](Event(e, self))
            t = Thread(target=target)
            t.daemon = True
            t.start()

    def bindEvent(self, e, fun, *args):
        if e in self.events:
            ind = self.events.index(e)
            nargs = self._event_nargs[ind]
            if len(args) == nargs:
                hook = tuple([fun] + list(args[:nargs]))
                self._hooks[e].append(hook)
            else:
                raise(EventBindException(
                    'Not enough arguments supplied for hook ' + e))
        else:
            raise(EventBindException('No such event: ' + e))

    def unbind(self):
        self._hooks = {}
        for event in self.events:
            self._hooks[event] = []


class MonitoredTrigger(object):

    def __init__(self):
        self._val = False
        self._hooks = []
        self._id = datetime.now().isoformat()

    def __getattr__(self, name):
        try:
            return super(MonitoredTrigger, self).__getattribute__(name)
        except AttributeError:
            return getattr(self._val, name)

    def __dir__(self):
        out = dir(self._val) + \
            ['value', 'set', 'raiseEvent', 'bindEvent', 'unbind']
        return sorted(out)

    def __int__(self):
        return int(self._val)

    def __float__(self):
        return float(self._val)

    @property
    def value(self):
        return self._val

    @value.setter
    def value(self, val):
        self.set(bool(val))

    def set(self, val):
        self._val = val
        if self._val:
            self.raiseTriggers()

    def raiseTriggers(self):
        for hook in self._hooks:
            if len(hook) == 1:
                target = hook(Event(None, self))
            elif len(hook) == 2 and hook[1] == self.value:
                target = hook(Event(None, self))
            elif len(hook) == 3 and hook[1] <= self.value and \
                    hook[2] >= self.value:
                target = hook(Event(None, self))
            t = Thread(target=target)
            t.daemon = True
            t.start()
        self.value = False

    def bindTrigger(self, fun):
        self._hooks.append(fun)

    def unbind(self):
        self._hooks = []
