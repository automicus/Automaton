import os
import sys
import traceback
from configuration import var_directory
import types


class WorkspaceManager(object):

    def __init__(self, log, path):
        self._log = log
        self._path = path

    def clean(self):
        for (path, dirs, files) in os.walk(self._path):
            for file in files:
                # remove compiled python files
                if file.endswith('.pyc'):
                    os.remove(path + os.sep + file)

    def unload(self):
        ws_modules = [key for key in sys.modules.keys()
                      if key.startswith('workspace')]
        for mod in ws_modules:
            del sys.modules[mod]

    def load(self):
        self.unload()
        self.clean()
        try:
            import workspace
            return workspace
        except Exception as e:
            # print exception and traceback
            directory = os.path.join(var_directory, 'workspace')
            tb = traceback.format_exc()
            tb = tb.replace(directory, 'WORKSPACE').split('\n')
            tb = tb[0:1] + tb[-4:-1]
            esig = str(type(e)) + ': ' + str(e)
            self._log.error('Workspace import error.')
            self._log.continuation(esig)
            for line in tb:
                self._log.continuation(line)
            return types.ModuleType('workspace')
