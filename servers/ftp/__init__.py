from abstractedFS import HumbleAbstractedFS
#from virtualFS import VirtualFS
from authorizer import HumbleAuthorizer
from handler import HumbleFTPHandler
from pyftpdlib.servers import ThreadedFTPServer as FTPServer
from threading import Thread


class HumbleFTPServer(FTPServer):
    """
        This FTP Server will automatically set up the
        authorizer, filesystem, and handler. A new
        funciton is also available that allows the
        server to be run in a thread.
        """
    def __init__(self, parent, host, user, passwd, home_dir, log):
        # pull settings
        self.parent = parent
        self.home_dir = unicode(home_dir)
        host = host.split(':')
        host[1] = int(host[1])
        # create authorizer
        authorizer = HumbleAuthorizer()
        authorizer.add_user(user, passwd, home_dir, perm="elradfmw")
        # create filesystem
        #virtual_fs = VirtualFS
        filesystem = HumbleAbstractedFS
        filesystem.parent = self
        # create handler
        handler = HumbleFTPHandler
        handler.parent = self
        handler.logger = log
        handler.authorizer = authorizer
        handler.passive_ports = range(60000, 65535)
        handler.abstracted_fs = filesystem  # virtual_fs  # real_fs
        # setup virtual fs
        # real_fs = HumbleAbstractedFS(self.home_dir, handler)
        # real_fs.parent = self
        # virtual_fs.structure = {'workspace': real_fs}
        # init self
        self.logger = log
        FTPServer.__init__(self, host, handler)
        self.max_cons = 256
        self.max_cons_per_ip = 5

    def serve_on_thread(self):
        """Run server in a thread."""
        self.thread = Thread(target=self.serve_forever, args=[5])
        self.thread.daemon = True
        self.thread.start()

    def _log_start(self):
        addr = self.address
        self.logger.info("FTP Server Started on %s:%s" % (addr[0], addr[1]))

    def stop(self):
        """ Stop FTP Server """
        self.close_all()

    def serve_forever(self, timeout=None, blocking=True, handle_exit=True):
        """Start serving.

            - (float) timeout: the timeout passed to the underlying IO
            loop expressed in seconds (default 1.0).

            - (bool) blocking: if False loop once and then return the
            timeout of the next scheduled call next to expire soonest
            (if any).

            - (bool) handle_exit: when True catches KeyboardInterrupt and
            SystemExit exceptions (generally caused by SIGTERM / SIGINT
            signals) and gracefully exits after cleaning up resources.
            Also, logs server start and stop.
            """
        if handle_exit:
            log = handle_exit and blocking
            if log:
                self._log_start()
            try:
                self.ioloop.loop(timeout, blocking)
            except (KeyboardInterrupt, SystemExit):
                pass
            if blocking:
                if log:
                    self.logger.info(
                        "FTP shutting down server (%s active fds)" %
                        self._map_len())
                self.close_all()
        else:
            self.ioloop.loop(timeout, blocking)
