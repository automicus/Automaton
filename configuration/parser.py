import os

def _cleanLine(line):
    try:
        ind = line.index('#')
        return line[:ind].replace('\n','')
    except ValueError:
        return line.replace('\n','')

def _cleanPath(directory, path):
    if 'win' in os.name:
        if ':' in path:
            return os.path.abspath(path)
        else:
            return os.path.abspath(directory + os.sep + path)
    else:
        if path[0] == '/':
            return os.path.abspath(path)
        else:
            return os.path.abspath(directory + '/' + path)

class ConfigFile(object):

    data = {'LogLevel': 'info', 'StdoutLevel': 'info',
        'AdminUser': 'admin', 'AdminPass': 'admin',
        'WWWHost': '0.0.0.0:10080', 'FTPHost': '0.0.0.0:10080',
        'LocString': 'Greenwich, England'}

    def __init__(self, log, data=None, fname=None):
        self.logger = log
        if data is not None:
            self.data = data
        else:
            self.data = {'Modules': {}}
            if fname is not None:
                self.read(fname)

    def __getitem__(self, key):
        return self.data.__getitem__(key)
    def __setitem__(self, key, val):
        return self.data.__setitem__(key, val)
    def __repr__(self): return self.data.__repr__()
    def __str__(self): return self.data.__str__()
    def iteritems(self): return self.data.iteritems()

    def read(self, fname):
        # clean fname, get directory
        fname = os.path.abspath(fname)
        directory = os.path.dirname(fname)

        # read file, remove comments
        data = open(fname, 'r').readlines()
        data = [_cleanLine(line) for line in data]

        # parse file data
        try:
            in_mod = None

            # loop through lines in file
            while True:
                line = data.pop(0)
                if len(line) > 0:
                    line = line.split()

                    if line[0] == 'Include':
                        # include additional file
                        new_data = open(_cleanPath(directory, line[1]), 'r').readlines()
                        new_data = [_cleanLine(line) for line in new_data]
                        data += new_data

                    elif line[0] == 'Module':
                        # parse module data
                        in_mod = line[1]
                        self.data['Modules'][in_mod] = {}

                    elif line[0] == 'EndModule':
                        # end module data
                        in_mod = None

                    else:
                        # regular parameter line
                        if in_mod is None:
                            self.data[line[0]] = line[1]
                        else:
                            self.data['Modules'][in_mod][line[0]] = line[1]

        except IndexError:
            # done scanning data
            pass

        self.logger.info('Imported Configuration')

    def write(self, fname, writeConfig=True, writeModules=True):
        f = open(fname, 'w')

        # write configuration
        if writeConfig:
            for key, val in self.data.iteritems():
                if key is not 'Modules':
                    f.write(key + ' ' + val + '\n')

        # write modules
        if writeModules:
            for mod_name, mod_dict in self.data['Modules'].iteritems():
                f.write('Module ' + mod_name + '\n')
                for key, val in mod_dict:
                    f.write('    ' + key + ' ' + val + '\n')

        f.close()
        self.logger.info('Exported Configuration')


