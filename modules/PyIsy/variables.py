
from xml.dom import minidom
from time import sleep
from ISYtypes import MonitoredDict
from datetime import datetime

_change2update_interval = 0.5
_thread_sleeptime = 0.75

class variables(object):

    vids = []
    vnames = []
    vobjs = []
    vtypes = []

    def __init__(self, parent, root=None, vids=None, vnames=None, \
        vobjs=None, vtypes=None, xml=None):
        
        self.parent = parent
        self.root = root

        if vids is not None and vnames is not None \
            and vobjs is not None and vtypes is not None:
            
            self.vids = vids
            self.vnames = vnames
            self.vobjs = vobjs
            self.vtypes = vtypes
            
        elif xml is not None:
            self.parse(xml)

    def parse(self, xmls):
        try:
            xmldocs = [minidom.parseString(xml) for xml in xmls]
        except:
            self.parent.log.error('ISY Could not parse variables, poorly formatted XML.')
        else:
            vlastup = datetime.now()

            # parse definitions
            for ind in xrange(2):
                features = xmldocs[ind].getElementsByTagName('e')
                for feature in features:
                    self.vids.append(int(feature.attributes['id'].value))
                    self.vnames.append(feature.attributes['name'].value)
                    self.vtypes.append(ind+1)

            # parse values
            self.vobjs = [None] * len(self.vids)
            for ind in xrange(2,4):
                features = xmldocs[ind].getElementsByTagName('var')
                if len(features) > 0:
                    vtype = ind-1
                    start_search_ind = self.vtypes.index(vtype)
                    for feature in features:
                        vid = int(feature.attributes['id'].value)
                        init = int(feature.getElementsByTagName('init')[0].firstChild.toxml())
                        val = int(feature.getElementsByTagName('val')[0].firstChild.toxml())
                        ts_raw = feature.getElementsByTagName('ts')[0].firstChild.toxml()
                        ts = datetime.strptime(ts_raw, '%Y%m%d %H:%M:%S')
                        ind = self.vids.index(vid, start_search_ind)
                        self.vobjs[ind] = variable(self, vid, vtype, init, val, ts)

            self.parent.log.debug('ISY Loaded Variables')

    def _upmsg(self, xml):
        xmldoc = minidom.parseString(xml)
        vtype = int(xmldoc.getElementsByTagName('var')[0].attributes['type'].value)
        vid = int(xmldoc.getElementsByTagName('var')[0].attributes['id'].value)
        vobj = self[vtype][vid]

        if '<init>' in xml:
            vobj.set('init', int(xmldoc.getElementsByTagName('init')[0].firstChild.toxml()))
        else:
            vobj.set('val', int(xmldoc.getElementsByTagName('val')[0].firstChild.toxml()))
            ts_raw = xmldoc.getElementsByTagName('ts')[0].firstChild.toxml()
            vobj.set('ts', datetime.strptime(ts_raw, '%Y%m%d %H:%M:%S'))

        self.parent.log.debug('ISY Updated Variable: ' + str(vid))
                    
    def __getitem__(self, val):
        if self.root is None:
            if val in [1, 2]:
                return variables(self.parent, val, self.vids, self.vnames, self.vobjs, self.vtypes)
            else:
                self.parent.log.error('ISY Unknown variable type: ' + str(val))

        else:
            if type(val) is int:
                search_arr = self.vids
            else:
                search_arr = self.vnames

            notFound = True
            ind = -1
            while notFound:
                try:
                    ind = search_arr.index(val, ind+1)
                    if self.vtypes[ind] == self.root:
                        notFound = False
                except ValueError:
                    break
            if notFound:
                return None
            else:
                return self.vobjs[ind]

    def __setitem__(self, val):
        return None   

class variable(MonitoredDict):
    
    def __init__(self, parent, vid, vtype, init, val, ts):
        super(variable, self).__init__()
        self.noupdate = False
        self.parent = parent
        self._id = vid
        self._type = vtype

        self['init'] = init
        self.bindReporter('init', self.__report_init__)
        self['val'] = val
        self.bindReporter('val', self.__report_val__)
        self['lastEdit'] = ts

    def __report_init__(self, val):
        self.noupdate = True
        self.setInit(val)
        self.noupdate = False

    def __report_val__(self, val):
        self.noupdate = True
        self.setValue(val)
        self.noupdate = False
            
    def update(self, waitTime=0):
        if not self.noupdate:
            self.parent.update(waitTime)

    def setInit(self, val):
        response = self.parent.parent.conn.initVariable(self._type, self._id, val)

        if response is None:
            self.parent.parent.log.warning('ISY could not set variable init value: ' + str(self._type) + ', ' + str(self._id))
        else:
            self.parent.parent.log.info('ISY set variable init value: ' + str(self._type) + ', ' + str(self._id))
            self.update(_change2update_interval)

    def setValue(self, val):
        response = self.parent.parent.conn.setVariable(self._type, self._id, val)

        if response is None:
            self.parent.parent.log.warning('ISY could not set variable: ' + str(self._type) + ', ' + str(self._id))
        else:
            self.parent.parent.log.info('ISY set variable: ' + str(self._type) + ', ' + str(self._id))
            self.update(_change2update_interval)