import urllib
import requests

class ISYhttp(object):

    def __init__(self, parent, address, port, username, password, use_https):
        self.parent     = parent
        self._address   = address
        self._port      = port
        self._username  = username
        self._password  = password
        self._use_https = use_https

    # COMMON UTILITIES
    def compileURL(self, path, query=None):
        if self._use_https:
            url = 'http://'
        else:
            url = 'http://'
        
        url += self._address
        url += '/rest/' + '/'.join([urllib.quote(item) for item in path])
         
        if query is not None:
            url += '?' + urllib.urlencode(query)
             
        return url
         
    def request(self, url, ok404=False):
        if self.parent.log is not None:
            self.parent.log.debug('ISY Request: ' + url)
        
        try:    
            r = requests.get(url, auth=(self._username, self._password))
        except requests.ConnectionError:
            self.parent.log.error('ISY Could not recieve response from device.')
            return None
        else: 
            if r.status_code == 200:
                self.parent.log.debug('ISY Response Recieved')
                return r.text
            elif r.status_code == 404 and ok404:
                self.parent.log.debug('ISY Response Recieved')
                return ''
            else:
                self.parent.log.warning('Bad ISY Request: ' + url)
                return None
            
    # CONFIGURATION
    def getConfiguration(self):
        req_url = self.compileURL(['config'])
        result = self.request(req_url)
        return result
        
    # PROGRAMS
    def getPrograms(self):
        req_url = self.compileURL(['programs'], {'subfolders': 'true'})
        result = self.request(req_url)
        return result

    def programRun(self, pid):
        return self.programRunCmd(pid, 'run')

    def programRunThen(self, pid):
        return self.programRunCmd(pid, 'runThen')

    def programRunElse(self, pid):
        return self.programRunCmd(pid, 'runElse')

    def programStop(self, pid):
        return self.programRunCmd(pid, 'stop')

    def programEnable(self, pid):
        return self.programRunCmd(pid, 'enable')

    def programDisable(self, pid):
        return self.programRunCmd(pid, 'disable')

    def programEnableRunAtStartup(self, pid):
        return self.programRunCmd(pid, 'enableRunAtStartup')

    def programDisableRunAtStartup(self, pid):
        return self.programRunCmd(pid, 'disableRunAtStartup')

    def programRunCmd(self, pid, cmd):
        req_url = self.compileURL(['programs', str(pid), cmd])
        result = self.request(req_url)
        return result

    # NODES
    def getNodes(self):
        req_url = self.compileURL(['nodes'], {'members': 'false'})
        result = self.request(req_url)
        return result

    def updateNodes(self):
        req_url = self.compileURL(['status'])
        result = self.request(req_url)
        return result
        
    def updateNode(self, nid):
        req_url = self.compileURL(['nodes', nid, 'get', 'ST'])
        response = self.request(req_url)
        return response
        
    def nodeOff(self, nid):
        req_url = self.compileURL(['nodes', nid, 'cmd', 'DOF'])
        response = self.request(req_url)
        return response
        
    def nodeOn(self, nid, val):
        if val is None:
            req_url = self.compileURL(['nodes', nid, 'cmd', 'DON'])
        elif val > 0:
            val = str(min(255, val))
            req_url = self.compileURL(['nodes', nid, 'cmd', 'DON', val])
        elif val <= 0:
            return self.nodeOff(nid)
        response = self.request(req_url)
        return response
        
    def nodeFastOff(self, nid):
        req_url = self.compileURL(['nodes', nid, 'cmd', 'DFOF'])
        response = self.request(req_url)
        return response
        
    def nodeFastOf(self, nid):
        req_url = self.compileURL(['nodes', nid, 'cmd', 'DFON'])
        response = self.request(req_url)
        return response
        
    def nodeBright(self, nid):
        req_url = self.compileURL(['nodes', nid, 'cmd', 'brt'])
        response = self.request(req_url)
        return response
        
    def nodeDim(self, nid):
        req_url = self.compileURL(['nodes', nid, 'cmd', 'dim'])
        response = self.request(req_url)
        return response
        
    # VARIABLES
    def getVariables(self):
        requests = [['vars', 'definitions', '1'], \
            ['vars', 'definitions', '2'], \
            ['vars', 'get', '1'], \
            ['vars', 'get', '2']]
        req_urls = [self.compileURL(req) for req in requests]
        results = [self.request(req_url) for req_url in req_urls]
        return results

    def updateVariables(self):
        requests = [['vars', 'get', '1'], \
            ['vars', 'get', '2']]
        req_urls = [self.compileURL(req) for req in requests]
        results = [self.request(req_url) for req_url in req_urls]
        result = ''.join(results)
        result = result.replace('</vars><?xml version="1.0" encoding="UTF-8"?><vars>', '')
        return result

    def updateVariable(self, vtype, vid):
        req_url = self.compileURL(['vars', 'get', str(vtype), str(vid)])
        result = self.request(req_url)
        return result

    def setVariable(self, vtype, vid, val):
        req_url = self.compileURL(['vars', 'set', str(vtype), str(vid), str(val)])
        result = self.request(req_url)
        return result

    def initVariable(self, vtype, vid, val):
        req_url = self.compileURL(['vars', 'init', str(vtype), str(vid), str(val)])
        result = self.request(req_url)
        return result
    
    # CLIMATE    
    def getClimate(self):
        req_url = self.compileURL(['climate'])
        result = self.request(req_url)
        return result
        
    # NETWORK
    def getNetwork(self):
        req_url = self.compileURL(['networking', 'resources'])
        result = self.request(req_url)
        return result

    def runNetwork(self, cid):
        req_url = self.compileURL(['networking', 'resources', str(cid)])
        result = self.request(req_url, ok404=True)
        return result

    # X10
    def sendX10(self, address, code):
        req_url = self.compileURL(['X10', address, str(code)])
        result = self.request(req_url)
        return result