import signal
from django.core.management.base import BaseCommand
from initd import Initd


class DaemonCommand(BaseCommand):
    """
    Run a management command as a daemon.

    Subclass this and override the `loop_callback` method with the code the
    daemon process should run. Optionally, override `exit_callback` with
    code to run when the process is stopped.

    Alternatively, if your code has more complex setup/shutdown requirements,
    override `handle_noargs` along the lines of the basic version here.

    Pass one of --start, --stop, --restart or --status to work as a daemon.
    Otherwise, the command will run as a standard application.
    """
    requires_model_validation = True
    WORKDIR = '.'
    UMASK = 0
    PID_FILE = 'daemon_command.pid'
    LOGFILE = 'daemon_command.log'
    STDOUT = '/dev/null'
    STDERR = STDOUT

    def add_arguments(self, parser):
        parser.add_argument('--start', action='store_const', const='start',
                            dest='action', help='Start the daemon')
        parser.add_argument('--stop', action='store_const', const='stop',
                            dest='action', help='Stop the daemon')
        parser.add_argument('--restart', action='store_const', const='restart',
                            dest='action', help='Stop and restart the daemon')
        parser.add_argument('--status', action='store_const', const='status',
                            dest='action', help='Report whether the daemon is'
                            ' currently running or stopped')
        parser.add_argument('--workdir', action='store', dest='workdir',
                            default=self.WORKDIR, help='Full path of the working'
                            ' directory to which the process should change on'
                            ' daemon start.')
        parser.add_argument('--umask', action='store', dest='umask',
                            default=self.UMASK, type=int,
                            help='File access creation mask ("umask") to set'
                            ' for the process on daemon start.')
        parser.add_argument('--pidfile', action='store', dest='pid_file',
                            default=self.PID_FILE, help='PID filename.')
        parser.add_argument('--logfile', action='store', dest='log_file',
                            default=self.LOGFILE, help='Path to log file')
        parser.add_argument('--stdout', action='store', dest='stdout',
                            default=self.STDOUT, help='Destination to redirect'
                            ' standard out')
        parser.add_argument('--stderr', action='store', dest='stderr',
                            default=self.STDERR, help='Destination to redirect'
                            ' standard error')
        parser.add_argument('--force', action='store_true', dest='force',
                            default=False, help='SIGKILL process if it won\'t'
                            ' terminate on SIGTERM')

    def loop_callback(self):
        raise NotImplementedError

    def exit_callback(self):
        pass

    def handle_noargs(self, **options):
        self.options = options
        action = options.pop('action', None)

        if action:
            # daemonizing so set up functions to call while running and at close
            daemon = Initd(**options)
            daemon.execute(action, run=self.loop_callback, exit=self.exit_callback)
        else:
            # running in console, so set up signal to call on ctrl-c
            signal.signal(signal.SIGINT, lambda sig, frame: self.exit_callback())
            self.loop_callback()
