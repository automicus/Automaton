import os
import shutil
from pyftpdlib.filesystems import AbstractedFS, FilesystemError


class HumbleAbstractedFS(AbstractedFS):
    """
        This custom file system is much like the default
        AbstractedFS except that it will not return
        pyc files and init files. Default init files are
        also added to new directories automatically.
        It also will allow directories to be removed
        with pyc and __init__.py files in them.
        """
    def listdir(self, path):
        """List the content of a directory."""
        assert isinstance(path, unicode), path
        listing = os.listdir(path)
        out = []
        for item in listing:
            if (not item.endswith('.pyc')) and (item != '__init__.py'):
                out.append(item)
        return out

    def rmdir(self, path):
        """Remove the specified directory."""
        assert isinstance(path, unicode), path
        # check if dir is empty
        empty = True
        for item in os.listdir(path):
            if (not item.endswith('.pyc')) and (item != '__init__.py'):
                empty = False
                break
        # remove all
        if empty:
            shutil.rmtree(path)
        else:
            raise OSError('Directory not empty.')

    def mkdir(self, path):
        """Create the specified directory."""
        assert isinstance(path, unicode), path
        def_init = str(self.ftp2fs(unicode('/'))) + os.sep + '__init__.py'
        os.mkdir(path)
        shutil.copy(def_init, path)

    def remove(self, path):
        """Remove the specified file."""
        assert isinstance(path, unicode), path
        if os.path.abspath(os.path.join(self.parent.home_dir, 'reboot')) \
                != path:
            os.remove(path)
        else:
            raise FilesystemError('Cannot remove the reboot file')

    def rename(self, src, dst):
        """Rename the specified src file to the dst filename."""
        assert isinstance(src, unicode), src
        assert isinstance(dst, unicode), dst
        if os.path.abspath(os.path.join(self.parent.home_dir, 'reboot')) \
                != src and \
                os.path.abspath(os.path.join(self.parent.home_dir, 'reboot')) \
                != dst:
            os.rename(src, dst)
        else:
            raise FilesystemError('Cannot move/overwrite the reboot file')