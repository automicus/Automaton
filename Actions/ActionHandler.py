from Schedule import schedule
from configuration import var_directory
from functools import partial
import inspect
import os
import traceback
from copy import copy


def action(log, target, *args):
    try:
        target(*args)
    except Exception as e:
        # print exception and traceback
        directory = os.path.join(var_directory, 'workspace')
        tb = traceback.format_exc()
        tb = tb.replace(directory, 'WORKSPACE').split('\n')
        tb = tb[0:1] + tb[-4:-1]
        esig = str(type(e)) + ': ' + str(e)
        log.error('Workspace runtime error.')
        log.continuation(esig)
        for line in tb:
            log.continuation(line)
        return None


class actionHandler(object):

    def __init__(self, log, loc_str):
        self.log = log
        self._watchedVars = []
        self._watchedIds = []
        self.schedule = schedule(self.log, loc_str)
        self.log.info('Action Handler created at location: ' +
                      self.schedule.loc.name + ', ' + self.schedule.loc.region)

    def isAlive(self):
        if self.schedule._timer is not None:
            return self.schedule._timer.isAlive()
        else:
            return False

    def stop(self):
        if self.schedule._timer is not None:
            self.schedule._timer.cancel()
            self.schedule._timer = None

    def clear(self):
        for var in self._watchedVars:
            var.unbind()
        self._watchedVars = []
        self._watchedIds = []
        self.stop()
        self.schedule.clear()

    def scanModule(self, mod, scanned_mods=[], layer=None):
        if layer is None:
            layer = 0

        for item in dir(mod):
            child = getattr(mod, item)
            if inspect.ismodule(child) and child not in scanned_mods:
                scanned_mods.append(child)

                try:
                    ev = getattr(child, '_e')
                    ev = copy(ev)
                    self.importModuleData(child, **ev)
                except AttributeError:
                    self.scanModule(child, scanned_mods, layer + 1)

        if layer == 0:
            self.schedule.start()

    def importModuleData(self, mod, name='', target=None, times=None,
                         events=None, triggers=None):
        # find target function
        if target is None:
            target = 'main'
        try:
            fun = getattr(mod, target)
            part = partial(action, self.log, fun)
        except AttributeError:
            self.log.error('Action Handler could not map event (' + str(name) +
                           '). Could not find target (' + target + ').')
        else:

            # map events
            if events is not None:
                for event in events:
                    var = event[0]
                    act = event[1]
                    args = event[2:]
                    var.bindEvent(act, part, *args)
                    if var._id not in self._watchedIds:
                        self._watchedVars.append(var)
                        self._watchedIds.append(var._id)

            # map triggers
            if triggers is not None:
                for trigger in triggers:
                    trigger.bindTrigger(part)
                    if var._id not in self._watchedIds:
                        self._watchedVars.append(trigger)
                        self._watchedIds.append(trigger._id)

            # schedule events
            if times is not None:
                for time in times:
                    self.schedule.append(name, time, part)

            self.log.info('Action Handler setup ' + str(name))
