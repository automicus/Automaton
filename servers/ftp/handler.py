from pyftpdlib.handlers import FTPHandler
import os
import traceback


class HumbleFTPHandler(FTPHandler):
    """ This handler is the same as the FTPHandler
        class except it uses the Humble Log class.
        """

    def log(self, msg, logfun=None):
        """Log a message, including additional identifying session data."""
        if logfun is None:
            logfun = self.logger.info
            prefix = self.log_prefix % self.__dict__
            logfun("FTP %s %s" % (prefix, msg))

    def logline(self, msg, logfun=None):
        """Log a line including additional indentifying session data.
            By default this is disabled unless logging level == DEBUG.
            """
        self.logger.debug("FTP: " + msg)

    def logerror(self, msg):
        """Log an error including additional indentifying session data."""
        prefix = self.log_prefix % self.__dict__
        self.logger.warning("FTP %s %s" % (prefix, msg))

    def log_exception(self, instance):
        """Log an unhandled exception. 'instance' is the instance
            where the exception was generated.
            """
        self.logger.error("FTP unhandled exception in instance %r" % instance)
        tb_lines = traceback.format_exc().splitlines()
        for tb_line in tb_lines:
            self.logger.continuation(tb_line)

    def on_file_received(self, fname):
        if os.path.abspath(os.path.join(self.parent.home_dir, 'reboot')) \
                == fname:
            self.parent.parent.reset()
