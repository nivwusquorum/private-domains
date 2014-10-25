import subprocess
import sys
import time
import traceback

from os import getlogin
from os.path import join

from config import InteractiveConfigValidation
from daemon import Daemon
from network import get_ip, send_ip, SEND_MIN_WAIT
from server import app
from utils import data_dir

class PingingDaemon(Daemon):
    def __init__(self, config):
        self.config = config
        super(PingingDaemon, self).__init__(join('/tmp', ".daemon_pid"))

    def run(self):
        while True:
            next_update = send_ip(self.config['server'],
                                  self.config['port'],
                                  self.config['secret'],
                                  self.config['domain'])
            if next_update is None:
                next_update = SEND_MIN_WAIT
            time.sleep(next_update)


class Server(object):
    def parse_argv(self, argv):
        if len(argv) not in [1,2]:
            return None

        port=None
        try:
            port = int(argv[0])
        except Exception:
            return None

        debug = False
        if len(argv) == 2:
            if argv[1] not in ['debug']:
                return None
            else:
                debug = True
        return (port, debug)

    def usage(self, script_name, method_name):
        print '%s %s <port> [debug]\nStarts the server' % (script_name, method_name)

    def run(self, port, debug=False):
        if debug:
            app.run(port=port, debug=True)
        else:
            app.run(host='0.0.0.0', port=port, debug=False)

class Get(object):
    def parse_argv(self, argv):
        if len(argv) != 1:
            return None
        else:
            return (argv[0],)

    def usage(self, script_name, method_name):
        print "%s %s <private_domain>\nReturns ip for private domain" % (script_name, method_name)

    def run(self, domain):
        icv = InteractiveConfigValidation()
        icv.run()
        config = icv.get()

        resp = get_ip(config['server'], config['port'], config['secret'], domain)

        if resp == 'not_found':
            print 'not found'
        elif resp == 'connection_error':
            print 'connection error'
        else:
            print resp



class Pinging(object):
    def parse_argv(self, argv):
        if len(argv) != 1 or argv[0] not in ['start', 'stop']:
            return None
        else:
            return (argv[0],)

    def usage(self, script_name, method_name):
        print "%s %s [start/stop]\nStarts or stops pinging server with current IP.\nIf daemon is already running it gets restarted." % (script_name, method_name)

    def run(self, action):
        icv = InteractiveConfigValidation()
        icv.run(require_domain=True)
        config = icv.get()

        pd = PingingDaemon(config)

        if action == 'start':
            if pd.is_running():
                pd.stop()
            pd.start()
        elif action == 'stop':
            if pd.is_running():
                pd.stop()

class Install(object):
    def parse_argv(self, argv):
        if len(argv) != 1 or argv[0] not in ['pinging', 'autohosts']:
            return None
        else:
            return (argv[0],)

    def usage(self, script_name, method_name):
        print "%s %s [pinging/autohosts]\nPinging option helps you setup your computer to automatically start pinging when system boots. Autohosts option will help you setup automatically update your private domains in /etc/hosts file." % (script_name, method_name)

    def run(self, action):
        icv = InteractiveConfigValidation()
        if action == 'pinging':
            icv.run(require_domain=True)
        else:
            icv.run()
            print 'not implemented'
            sys.exit(1)

        config = icv.get()

        if action == "pinging":
            print "In a second you will be presented with your default text editor. Copy text below and paste it at the bottom of that file, save and exit:"
            print ""
            print "@reboot %s pd pinging start" % getlogin()
            print ""
            print "Copy the line and press enter to continue."
            raw_input()
        subprocess.call("crontab -e", shell=True)
        print "Good job! If all went well pinging will now start automatically."
METHODS = {
    "server": Server(),
    "get": Get(),
    "pinging": Pinging(),
    "install": Install(),
}

def usage(script_name, method=None):
    print "Usage:"
    for name in METHODS:
        if method is None or name == method:
            print ""
            METHODS[name].usage(script_name, name)
    sys.exit(0)

def execute(argv):
    if len(argv) < 2 or argv[1] not in METHODS:
        usage(argv[0])

    method = METHODS[argv[1]]

    args = method.parse_argv(argv[2:])
    if args is None:
        usage(argv[0], argv[1])
    else:
        method.run(*args)
