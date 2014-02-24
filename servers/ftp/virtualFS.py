from pyftpdlib.filesystems import AbstractedFS, FilesystemError
from abstractedFS import HumbleAbstractedFS
from types import FunctionType
import grp
import time
import os


class VirtualFS(AbstractedFS):

    structure = {}

    def __init__(self, root, cmd_channel):
        """
            - (instance) cmd_channel: the FTPHandler class instance
            """
        self._cwd = '/'
        self._root = '/'
        self.cmd_channel = cmd_channel
        #self.structure = {}

    def __setitem__(self, key, val):
        assert isinstance(key, str), key
        assert isinstance(val, dict) or isinstance(val, VirtualFile), val
        self.structure[key] = val

    def __getitem__(self, key):
        assert isinstance(key, str), key
        return self.structure[key]

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, val):
        pass

    @property
    def cwd(self):
        return unicode(self._cwd)

    @cwd.setter
    def cwd(self, val):
        pass

    # --- Wrapper methods around open()

    def open(self, filename, mode):
        """Open a file returning its handler."""
        assert isinstance(filename, unicode), filename
        # navigate to file in dictionary
        path_parts = filename.split('/')[1:]
        target = self.structure
        for ind in xrange(len(path_parts)):
            target = target[path_parts[ind]]
            # check for embeded file system
            if isinstance(target, AbstractedFS):
                return target.open(unicode('/'.join(path_parts[ind + 1:])))
        return target.open(mode)

    # --- Wrapper methods around os.* calls

    def chdir(self, path):
        """Change the current directory."""
        # note: process cwd will be reset by the caller
        self._cwd = self.fs2ftp(path)

    def mkdir(self, path):
        """Create the specified directory."""
        assert isinstance(path, unicode), path
        raise FilesystemError('Cannot create directories in a virtual path')

    def listdir(self, path):
        """List the content of a directory."""
        assert isinstance(path, unicode), path
        # navigate to path
        path_parts = path.split('/')[1:]
        if len(path_parts[-1]) == 0:
            path_parts = path_parts[0:-1]
        target = self.structure
        for ind in xrange(len(path_parts)):
            target = target[path_parts[ind]]
            if isinstance(target, AbstractedFS):
                return target.listdir(unicode('/'.join(path_parts)))
        output = [unicode(key) for key in target.keys()]
        return output

    def rmdir(self, path):
        """Remove the specified directory."""
        assert isinstance(path, unicode), path
        raise FilesystemError('Cannot remove directories in a virtual path')

    def remove(self, path):
        """Remove the specified file."""
        assert isinstance(path, unicode), path
        # navigate to file in dictionary
        path_parts = path.split('/')[1:]
        parent = None
        target = self.structure
        for ind in xrange(len(path_parts)):
            parent = target
            target = target[path_parts[ind]]
            # check for embeded file system
            if isinstance(target, AbstractedFS):
                return target.remove(unicode('/'.join(path_parts[ind + 1:])))
        if isinstance(target, VirtualFile) and target.canDelete():
            del parent[path_parts[-1]]
        else:
            raise FilesystemError('Cannot delete ' + path)

    def rename(self, src, dst):
        """Rename the specified src file to the dst filename."""
        assert isinstance(src, unicode), src
        assert isinstance(dst, unicode), dst
        raise FilesystemError('Cannot rename files in a virtual path')

    def chmod(self, path, mode):
        """Change file/directory mode."""
        assert isinstance(path, unicode), path
        raise FilesystemError('Cannot chmod files in a virtual path')

    def stat(self, path):
        """Perform a stat() system call on the given path."""
        # on python 2 we might also get bytes from os.lisdir()
        #assert isinstance(path, unicode), path
        return {}

    def lstat(self, path):
        """Like stat but does not follow symbolic links."""
        # on python 2 we might also get bytes from os.lisdir()
        assert isinstance(path, unicode), path
        return VirtualStatResult(self.isdir(path),
                                 self.getsize(path),
                                 self.getmtime(path))

    # --- Wrapper methods around os.path.* calls

    def isfile(self, path):
        """Return True if path is a file."""
        assert isinstance(path, unicode), path
        target = self.structure
        path_parts = path.split('/')[1:]
        try:
            for ind in xrange(len(path_parts)):
                target = target[path_parts[ind]]
                # check for embeded file system
                if isinstance(target, AbstractedFS):
                    return target.isfile(unicode('/'.join(path_parts[ind + 1:])))
            return isinstance(target, VirtualFile)
        except KeyError:
            return False

    def islink(self, path):
        """Return True if path is a symbolic link."""
        assert isinstance(path, unicode), path
        return False

    def isdir(self, path):
        """Return True if path is a directory."""
        assert isinstance(path, unicode), path
        target = self.structure
        path_parts = path.split('/')[1:]
        if len(path_parts[-1]) == 0:
            path_parts = path_parts[0:-1]
        for ind in xrange(len(path_parts)):
            target = target[path_parts[ind]]
            # check for embeded file system
            if isinstance(target, AbstractedFS):
                new_path = self.ftp2fs(unicode('/'.join(path_parts[ind + 1:])))
                print new_path
                return target.isdir(new_path)
        return isinstance(target, dict)

    def getsize(self, path):
        """Return the size of the specified file in bytes."""
        assert isinstance(path, unicode), path
        target = self.structure
        path_parts = path.split('/')[1:]
        for ind in xrange(len(path_parts)):
            target = target[path_parts[ind]]
            # check for embeded file system
            if isinstance(target, AbstractedFS):
                return target.getsize(unicode('/'.join(path_parts[ind + 1:])))
        if isinstance(target, VirtualFile):
            return target.size()
        else:
            return 0

    def getmtime(self, path):
        """Return the last modified time as a number of seconds since
            the epoch."""
        assert isinstance(path, unicode), path
        target = self.structure
        path_parts = path.split('/')[1:]
        for ind in xrange(len(path_parts)):
            target = target[path_parts[ind]]
            # check for embeded file system
            if isinstance(target, AbstractedFS):
                return target.getmtime(unicode('/'.join(path_parts[ind + 1:])))
        if isinstance(target, VirtualFile):
            return target.mtime
        else:
            return int(time.mktime(time.localtime()))

    def realpath(self, path):
        """Return the canonical version of path eliminating any
            symbolic links encountered in the path (if they are
            supported by the operating system).
            """
        assert isinstance(path, unicode) or \
            isinstance(path, str), path
        return path

    def lexists(self, path):
        """Return True if path refers to an existing path, including
            a broken or circular symbolic link.
            """
        assert isinstance(path, unicode), path
        try:
            target = self.structure
            path_parts = path.split('/')[1:]
            for ind in xrange(len(path_parts)):
                target = target[path_parts[ind]]
                # check for embeded file system
                if isinstance(target, AbstractedFS):
                    return target.lexists(unicode('/'.join(path_parts[ind + 1:])))
            return True
        except:
            return False

    def get_user_by_uid(self, uid):
        """Return the username associated with user id.
            If this can't be determined return raw uid instead.
            On Windows just return "owner".
            """
        return uid

    def get_group_by_gid(self, gid):
        """Return the groupname associated with group id.
            If this can't be determined return raw gid instead.
            On Windows just return "group".
            """
        try:
            return grp.getgrgid(gid).gr_name
        except KeyError:
            return gid

    # --- Listing utilities

    def get_list_dir(self, path):
        """"Return an iterator object that yields a directory listing
        in a form suitable for LIST command.
        """
        assert isinstance(path, unicode), path
        print self.isdir(path)
        if self.isdir(path):
            listing = self.listdir(path)
            print 'LISTING:'
            print listing
            try:
                listing.sort()
            except UnicodeDecodeError:
                # (Python 2 only) might happen on filesystem not
                # supporting UTF8 meaning os.listdir() returned a list
                # of mixed bytes and unicode strings:
                # http://goo.gl/6DLHD
                # http://bugs.python.org/issue683592
                pass
            return self.format_list(path, listing)
        # if path is a file or a symlink we return information about it
        else:
            basedir, filename = os.path.split(path)
            self.lstat(path)  # raise exc in case of problems
            return self.format_list(basedir, [filename])


class VirtualFile(object):

    def __init__(self, fun, perm='rwad'):
        """
            - (function) fun: Function that returns the contents of the file
            - (str) perm: Optional, permissions for the file. Default: rwd
            r - Read
            w - Write
            a - Append
            d - Delete
            """
        assert isinstance(fun, FunctionType), fun
        assert isinstance(perm, unicode), perm
        self._fun = fun
        self._perm = perm
        self._mtime = int(time.mktime(time.localtime()))

    def __repr__(self):
        return 'VirtualFile(' + str(self.fun) + ')'

    @property
    def fun(self):
        return self._fun

    @fun.setter
    def fun(self, fun):
        assert isinstance(FunctionType), fun
        self._fun = fun

    @property
    def perm(self, perm):
        return self._perm

    @perm.setter
    def perm(self, perm):
        assert isinstance(perm, unicode), perm
        self._perm = perm

    @property
    def mtime(self):
        return self._mtime

    def open(self, mode='r'):
        # ignore binary mode requests
        # check mode
        if mode[0] in self.perm:
            self._mode = mode
        else:
            raise FilesystemError('Cannot open file with mode: ' + mode)
        # initialize data
        if mode[0] == 'r':
            data = self.fun(mode)
        elif mode[0] in 'wa':
            self._data = ''
        return VirtualFileObject(self, mode, data)

    def canDelete(self):
        return 'd' in self.perm

    def size(self):
        if 'r' in self.perm:
            return len(self.fun('rb'))
        else:
            return 0


class VirtualFileObject(object):
    def __init__(self, parent, mode, data):
        self.parent = parent
        self._mode = mode
        self._data = data
        self._cursor = 0

    def seek(self, pos):
        # store new position if reading only
        # write and append don't really need the cursor
        # throw error if no file is open
        if self._mode[0] in 'rwa':
            self._cursor = pos
        else:
            raise FilesystemError('File not open for r, w, or a')

    def close(self):
        if self._mode[0] in 'wa':
            self.parent.fun(self._mode, self._data)
            self.parent._mtime = time.mktime(time.localtime())

    def read(self, buffer_size=None):
        if 'r' in self._mode:
            if buffer_size is None:
                buffer_size = len(self._data - self._cursor)
            new_cursor = self._cursor + buffer_size
            output = self._data[self._cursor:new_cursor]
            self._cursor = new_cursor
            return output
        else:
            raise FilesystemError('File not open for reading')

    def write(self, chunk):
        if self._mode[0] in 'wa':
            self._data += chunk
        else:
            raise FilesystemError('File not open for writing')


class VirtualStatResult(object):
    def __init__(self, isdir, size, mtime):
        if isdir:
            self.st_mode = 16749
        else:
            self.st_mode = 33133
        self.st_ino = 1
        self.st_dev = 1
        self.st_nlink = 0
        self.st_uid = 1000
        self.st_gid = 20
        self.st_size = size
        self.st_atime = int(time.time())
        self.st_mtime = mtime
        self.st_ctime = mtime
