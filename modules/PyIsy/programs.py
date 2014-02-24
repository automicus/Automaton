
from xml.dom import minidom
from time import sleep
from ISYtypes import MonitoredDict
from datetime import datetime

_change2update_interval = 0.5
_thread_sleeptime = 0.75

class programs(object):

    pids = []
    pnames = []
    pparents = []
    pobjs = []
    ptypes = []

    def __init__(self, parent, root=None, pids=None, pnames=None, \
        pparents=None, pobjs=None, ptypes=None, xml=None):
        
        self.parent = parent
        self.root = root

        if pids is not None and pnames is not None and pparents is not None \
            and pobjs is not None and ptypes is not None:
            
            self.pids = pids
            self.pnames = pnames
            self.pparents = pparents
            self.pobjs = pobjs
            self.ptypes = ptypes
            
        elif xml is not None:
            self.parse(xml)

    def parse(self, xml):
        try:
            xmldoc = minidom.parseString(xml)
        except:
            self.parent.log.error('ISY Could not parse programs, poorly formatted XML.')
        else:
            # get nodes
            features = xmldoc.getElementsByTagName('program')
            for feature in features:
                pid = feature.attributes['id'].value
                pname = feature.getElementsByTagName('name')[0].firstChild.toxml()
                try:
                    pparent = feature.attributes['parentId'].value
                except:
                    pparent = None

                if feature.attributes['folder'].value == 'true':
                    ptype = 'folder'
                    pobj = folder(self, pid)
                
                else:
                    ptype = 'program'
                    plastrun = feature.getElementsByTagName('lastRunTime')[0].firstChild
                    if plastrun is None:
                        plastrun = datetime(1, 1, 1, 0, 0)
                    else:
                        val = plastrun.toxml()
                        plastrun = datetime.strptime(val, '%Y/%m/%d %I:%M:%S %p')
                    plastfin = feature.getElementsByTagName('lastFinishTime')[0].firstChild
                    if plastfin is None:
                        plastfin = datetime(1, 1, 1, 0, 0)
                    else:
                        val = plastfin.toxml()
                        plastfin = datetime.strptime(val, '%Y/%m/%d %I:%M:%S %p')
                    if feature.attributes['enabled'].value == 'true':
                        penabled = True
                    else:
                        penabled = False
                    pobj = program(self, pid, penabled, plastrun, plastfin)

                if pid in self.pids:
                    self.getByID(pid).update(data = pobj)
                else:
                    self.insert(pid, pname, pparent, pobj, ptype)

            self.parent.log.debug('ISY Loaded/Updated Programs')

    def _upmsg(self, xml):
        xmldoc = minidom.parseString(xml)
        pid = xmldoc.getElementsByTagName('id')[0].firstChild.toxml().zfill(4)
        pobj = self.getByID(pid)

        if '<s>' in xml: 
            status = xmldoc.getElementsByTagName('s')[0].firstChild.toxml()
            if status == '21':
                pobj.set('ranThen', True)
            elif status == '31':
                pobj.set('ranElse', True)

        if '<r>' in xml:
            plastrun = xmldoc.getElementsByTagName('r')[0].firstChild.toxml()
            pobj.set('lastRun', datetime.strptime(plastrun, '%y%m%d %H:%M:%S'))

        if '<f>' in xml:
            plastfin = xmldoc.getElementsByTagName('f')[0].firstChild.toxml()
            pobj.set('lastFinished', datetime.strptime(plastfin, '%y%m%d %H:%M:%S'))

        if '<on />' in xml or '<off />' in xml:
            pobj.set('enabled', '<on />' in xml)

        self.parent.log.debug('ISY Updated Program: ' + pid)
                    
    def insert(self, pid, pname, pparent, pobj, ptype):
        self.pids.append(pid)
        self.pnames.append(pname)
        self.pparents.append(pparent)
        self.ptypes.append(ptype)
        self.pobjs.append(pobj)
    
    def __getitem__(self, val):
        try:
            self.pids.index(val)
            fun = self.getByID
        except:
            try:
                self.pnames.index(val)
                fun = self.getByName
            except:
                val = int(val)
                fun = self.getByInd
        
        try:
            return fun(val)
        except:
            return None

    def __setitem__(self, val):
        return None

    def getByName(self, val):
        for i in xrange(len(self.pids)):
            if self.pparents[i] == self.root and self.pnames[i] == val:
                return self.getByInd(i)

    def getByID(self, nid):
        i = self.pids.index(nid)
        return self.getByInd(i, forceObj=True)

    def getByInd(self, i, forceObj=False):
        if self.ptypes[i] == 'folder' and not forceObj:
            return nodes(self.pids[i], self.parent, self.pids, self.pnames, self.pparents, self.pobjs, self.ptypes)
        else:
            return self.pobjs[i]
   

class folder(MonitoredDict):
    
    def __init__(self, parent, pid):
        super(folder, self).__init__()
        self.noupdate = False
        self.parent = parent
        self._id = pid
        self.desc = 'folder'

        self.addTrigger('ranThen')
        self.addTrigger('ranElse')
            
    def update(self, waitTime=0, data=None):
        if not self.noupdate:
            if data is not None:
                self.set('status', data['status'])
            else:
                self.parent.update(waitTime)

    def run(self):
        response = self.parent.parent.conn.programRun(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not run program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY ran program: ' + self._id)
            self.update(_change2update_interval)

    def runThen(self):
        response = self.parent.parent.conn.programRunThen(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not run then in program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY ran then in program: ' + self._id)
            self.update(_change2update_interval)

    def runElse(self):
        response = self.parent.parent.conn.programRunElse(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not run else in program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY ran else in program: ' + self._id)
            self.update(_change2update_interval)    

    def stop(self):
        response = self.parent.parent.conn.programStop(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not stop program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY stopped program: ' + self._id)
            self.update(_change2update_interval)
    
class program(folder):

    def __init__(self, parent, pid, enabled, lastrun, lastfinish):
        super(program, self).__init__(parent, pid)
        self.desc = 'program'

        self['lastRun'] = lastrun
        self['lastFinished'] = lastfinish
        self['enabled'] = enabled
        self.bindReporter('enabled', self.__report_enabled__)

    def __report_enabled__(self, val):
        self.noupdate = True
        fun = self.enable if val else self.disable
        fun()
        self.noupdate = False

    def update(self, waitTime=0, data=None):
        if not self.noupdate:
            if data is not None:
                prunning = (data['lastRun'] >= self['lastUpdate']) or data['running']
                self.set('status', data['status'])
                self.set('lastUpdate', data['lastUpdate'])
                self.set('lastRun', data['lastRun'])
                self.set('lastFinished', data['lastFinished'])
                self.set('enabled', data['enabled'])
                self.set('runAtStartup', data['runAtStartup'])
                self.set('running', prunning)
            else:
                self.parent.update(waitTime)

    def enable(self):
        response = self.parent.parent.conn.programEnable(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not enable program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY enabled program: ' + self._id)
            self.update(_change2update_interval)   

    def disable(self):
        response = self.parent.parent.conn.programDisable(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not disable program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY disabled program: ' + self._id)
            self.update(_change2update_interval) 

    def enableRunAtStartup(self):
        response = self.parent.parent.conn.programEnableRunAtStartup(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not enable run at startup for program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY enabled run at startup for program: ' + self._id)
            self.update(_change2update_interval) 

    def disableRunAtStartup(self):
        response = self.parent.parent.conn.programDisableRunAtStartup(self._id)

        if response is None:
            self.parent.parent.log.warning('ISY could not disable run at startup for program: ' + self._id)
        else:
            self.parent.parent.log.info('ISY disabled run at startup for program: ' + self._id)
            self.update(_change2update_interval) 