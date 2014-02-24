#! /usr/bin/python

# python builtin
import logging
import os
import signal
import sys
import time
# add standard library to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + os.sep + 'lib')
# custom imports
from daemon import runner
from WorkspaceManager import WorkspaceManager
import Log
import configuration
#import events
import Actions
import modules
import servers
# add workspace and custom library to path
sys.path.append(configuration.conf_directory + os.sep + 'lib')
sys.path.append(configuration.var_directory)
# debugging modules
try:
    import pdb
    import rlcompleter
    DEBUG = True
except ImportError:
    DEBUG = False


class app(object):

    banner = """
                   __  __                __    __
                  / / / /_  _ ____ ___  / /_  / /__
                 / /_/ / / / / __ `__ \/ __ \/ / _ \\
                / __  / /_/ / / / / / / /_/ / /  __/
               /_/ /_/\__,_/_/ /_/ /_/_.___/_/\___/
    ___         __                        __
   /   | __  __/ /_____  ____ ___  ____  / /_____  ____
  / /| |/ / / / __/ __ \/ __ `__ \/ __ `/ __/ __ \/ __ \\
 / ___ / /_/ / /_/ /_/ / / / / / / /_/ / /_/ /_/ / / / /
/_/  |_\__,_/\__/\____/_/ /_/ /_/\__,_/\__/\____/_/ /_/
    """

    def __init__(self):
        # initialize daemon settings
        self.running = True
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/tmp/HumbleAutomaton.pid'
        self.pidfile_timeout = 5
        self.servers = {'ftp': None, 'www': None}
        self.booting = True

    def run(self):
        # create standard paths
        log_path = configuration.var_directory + os.sep + 'automaton.log'
        config_path = configuration.conf_directory + 'automaton.conf'
        work_path = configuration.var_directory + os.sep + 'workspace'

        # create log file
        banner = self.banner.split('\n')
        self.log = Log.logger(log_path, 1, 1)
        self.log.info('Program Started')
        for line in banner:
            self.log.continuation(line)

        # read config files
        self.config = configuration.ConfigFile(fname=config_path, log=self.log)
        self.log.setLevels(self.config['LogLevel'], self.config['StdoutLevel'])

        # create ftp server
        self.servers['ftp'] = servers.ftp.HumbleFTPServer(
            self,
            self.config['FTPHost'],
            self.config['AdminUser'],
            self.config['AdminPass'],
            work_path, self.log)
        self.servers['ftp'].serve_on_thread()

        # create modules
        self.modules = {}
        for fullname, settings in self.config['Modules'].iteritems():
            try:
                names = fullname.split(':')
                mod = getattr(modules, names[0])
                self.modules[names[1]] = mod.install(log=self.log, **settings)
            except AttributeError:
                self.log.error('Could not install module (' +
                               names[0] + ') does not exist.')
            except TypeError:
                self.log.error('Could not install module (' +
                               names[0] + ') missing parameters.')
            except:
                self.log.error('Could not install module (' +
                               names[0] + ') unkown error.')
            else:
                self.log.info('Installed module ' +
                              names[0] + ' as ' + names[1])

        # import workspace and setup event handler
        self._ws = WorkspaceManager(self.log, work_path)
        self.action_handler = \
            Actions.actionHandler(self.log, self.config['LocString'])
        workspace = self._ws.load()
        self.action_handler.scanModule(workspace)

        # wait until exit request
        self.booting = False
        self.log.info('Ready to Run')
        while self.running:
            try:
                time.sleep(100)
            except KeyboardInterrupt:
                cmd = raw_input('Action (reboot/stop/debug/[none])? ')
                if cmd == 'reboot':
                    self.reset()
                elif cmd == 'stop':
                    self.stop()
                elif cmd == 'debug':
                    self.debug()
                else:
                    pass
        self.stop()

    def reset(self):
        self.log.info('Rebooting Application')
        self.booting = True
        self.action_handler.clear()
        workspace = self._ws.load()
        self.action_handler.scanModule(workspace)
        self.booting = False

    def debug(self):
        if DEBUG:
            pdb.Pdb.complete = rlcompleter.Completer(locals()).complete
            self.log.info('Pausing...')
            pdb.set_trace()
            self.log.info('Resuming...')
        else:
            self.log.error('Debug feature requires that the pdb module ' +
                           'and rlcompleter module to be installed.')

    def stop(self, *args, **kwargs):
        self.log.info('Quitting Application')
        # stop timer
        self.action_handler.stop()
        # quit modules
        for device in self.modules:
            self.modules[device].stop()
        # close ftp server
        self.servers['ftp'].stop()

        # wait for threads to quit
        for i in xrange(40):
            threads_running = []
            for mod in self.modules.itervalues():
                threads_running.append(mod.isAlive())
            threads_running.append(self.servers['ftp'].thread.isAlive())
            threads_running.append(self.action_handler.isAlive())
            if sum(threads_running) == 0:
                break
            time.sleep(0.25)
        # verify all threads quit
        for name, mod in self.modules.iteritems():
            if mod.isAlive():
                self.log.warning('Could not stop module, ' +
                                 name + '. Forcing Stop.')
        if self.servers['ftp'].thread.isAlive():
            self.log.warning('FTP thread would not quit. Forcing stop.')
        if self.action_handler.isAlive():
            self.log.warning('Action Handler could not be quit. Forcing stop.')

        # exit
        sys.exit(0)

    def kill(self, *args, **kwargs):
        self.running = False

if __name__ == "__main__":
    # set help documentation
    help_string = """
    Usage: HumbleAutomaton run|start|stop|restart|help

        run:     Start server in the foreground
        start:   Launch the server as a daemon
        stop:    Stop a running server daemon
        restart: Restart a running server daemon
        help:    Display this message
    """
    # create the application
    global automaton
    automaton = app()
    signal.signal(signal.SIGTERM, app.kill)
    logging.basicConfig(level=logging.CRITICAL)

    # store application as module for easy importing
    sys.modules['automaton'] = automaton

    if len(sys.argv) == 1:
        # no arguments supplied
        print help_string
    elif sys.argv[1] == 'help':
        # help docs are requested
        print help_string
    elif sys.argv[1] == 'run':
        # run the app in the foreground
        try:
            automaton.run()
        except KeyboardInterrupt:
            pass
    else:
        # run the app as a daemon
        daemon_runner = runner.DaemonRunner(automaton)
        daemon_runner.do_action()
