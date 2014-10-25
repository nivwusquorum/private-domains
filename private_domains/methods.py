import subprocess
import sys
import time
import traceback

from os import getlogin
from os.path import join, expanduser, isfile
from requests.packages import urllib3

from config import InteractiveConfigValidation
from daemon import Daemon
from network import Network
from server import app
from utils import data_dir, which, ensure_sudo

# disable annoying unverified https warning
urllib3.disable_warnings()


class PingingDaemon(Daemon):
    def __init__(self, network, my_domain):
        self.network = network
        self.my_domain = my_domain
        super(PingingDaemon, self).__init__(expanduser("~/.pd_daemon_pid"))

    def run(self):
        while True:
            next_update = self.network.send_ip(self.my_domain)
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
        print '%s %s <port> [debug]\n\nStarts the server' % (script_name, method_name)

    def run(self, port, debug=False):
        if debug:
            app.run(port=port, debug=True)
        else:
            app.run(host='0.0.0.0', port=port, debug=False)

class Get(object):
    def parse_argv(self, argv):
        if len(argv) not in [1,2]:
            return None
        else:
            return (argv[0],)

    def usage(self, script_name, method_name):
        print "%s %s <private_domain>\n\nReturns ip for private domain" % (script_name, method_name)

    def run(self, domain):
        icv = InteractiveConfigValidation()
        icv.run()
        config = icv.get()

        network = Network(config['server'], config['port'], config['secret'], config['verify_ssl'])
        resp = network.get_ip(domain)

        if resp == 'not_found':
            print 'not found'
            sys.exit(1)
        elif resp == 'connection_error':
            print 'connection error'
            sys.exit(2)
        else:
            print resp

class GetAll(object):
    def parse_argv(self, argv):
        if len(argv) != 0:
            return None
        else:
            return ()

    def usage(self, script_name, method_name):
        print "%s %s\n\nReturns all known (private domain, ip) pairs." % (script_name, method_name)

    def run(self):
        icv = InteractiveConfigValidation()
        icv.run()
        config = icv.get()

        network = Network(config['server'], config['port'], config['secret'], config['verify_ssl'])
        resp = network.get_ips()

        if resp == 'connection_error':
            print 'connection error'
            sys.exit(2)
        else:
            print resp

class EtcHosts(object):
    def parse_argv(self, argv):
        if len(argv) not in [0,1]:
            return None
        if len(argv) == 1 and argv[0] != 'dryrun':
            return None
        dryrun = len(argv) == 1
        return (dryrun,)

    def usage(self, script_name, method_name):
        print "%s %s [dryrun]\n\nUpdates /etc/hosts to include all private domains from server. Dry run outputs updates to stdin without making any changes." % (script_name, method_name)

    def run(self, dryrun):
        ensure_sudo()

        icv = InteractiveConfigValidation()
        icv.run()
        config = icv.get()

        network = Network(config['server'], config['port'], config['secret'], config['verify_ssl'])
        resp = network.get_ips()

        if resp == 'connection_error':
            print 'connection error'
            sys.exit(2)

        domains = [ d.split(' ') for d in resp.split('\n')]

        updated_hosts = []
        PD_BEGIN = '### PRIVATE DOMAINS BEGIN ###'
        PD_END =   '### PRIVATE DOMAINS END ###'

        if isfile('/etc/hosts'):
            PD_NOTSTARTED = 1
            PD_STARTED = 2
            PD_ENDED = 3
            state = PD_NOTSTARTED
            with open('/etc/hosts') as f:
                for line in f:
                    line = line[:-1] # remove \n
                    if state == PD_NOTSTARTED:
                        assert line not in [PD_END]
                        if line == PD_BEGIN:
                            state = PD_STARTED
                        else:
                            updated_hosts.append(line)
                    elif state == PD_STARTED:
                        assert line not in [PD_BEGIN]
                        if line == PD_END:
                            state = PD_ENDED
                    elif state == PD_ENDED:
                        assert line not in [PD_BEGIN, PD_END]
                        updated_hosts.append(line)
        else:
            # hosts did not exists create new one
            pass
        updated_hosts.append(PD_BEGIN)
        for domain, ip in domains:
            updated_hosts.append('%s\t%s' % (ip, domain))
        updated_hosts.append(PD_END)
        # adding a newline at the end of file
        updated_hosts.append('')

        updated_hosts_string = '\n'.join(updated_hosts)
        if dryrun:
            print updated_hosts_string
        else:
            with open('/etc/hosts', "w+") as f:
                f.write(updated_hosts_string)


class Pinging(object):
    def parse_argv(self, argv):
        if len(argv) != 1 or argv[0] not in ['start', 'stop']:
            return None
        else:
            return (argv[0],)

    def usage(self, script_name, method_name):
        print "%s %s [start/stop]\n\nStarts or stops pinging server with current IP.\nIf daemon is already running it gets restarted." % (script_name, method_name)

    def run(self, action):
        icv = InteractiveConfigValidation()
        icv.run(require_domain=True)
        config = icv.get()

        network = Network(config['server'], config['port'], config['secret'], config['verify_ssl'])
        pd = PingingDaemon(network, config['domain'])

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
        print "%s %s [pinging/autohosts]\n\nPinging option helps you setup your computer to automatically start pinging when system boots. Autohosts option will help you setup automatically update your private domains in /etc/hosts file." % (script_name, method_name)

    def run(self, action):
        icv = InteractiveConfigValidation()
        if action == 'pinging':
            icv.run(require_domain=True)
        else:
            icv.run()

        config = icv.get()

        if action == "pinging":
            print "In a second you will be presented with your default text editor. Copy text below and paste it at the bottom of that file, save and exit:"
            print ""
            print "@reboot %s pinging start" % (which('pd'),)
            print ""
            print "Copy the line and press enter to continue."
            raw_input()
            subprocess.call("crontab -e", shell=True)
            print "Good job! If all went well pinging will now start automatically."
        elif action == 'autohosts':
            ensure_sudo()
            cron_file = "/etc/cron.d/pd_etchosts"
            cron_contents = "HOME=/home/%s\n*/1 * * * * root %s etchosts" % (getlogin(), which('pd'),)

            def writeback():
                with open(cron_file, "w+") as f:
                    f.write(cron_contents)
                    f.write('\n')
            print "The following lines are going to be added to %s:\n\n%s\n" % (cron_file, cron_contents)
            _, agreed = icv.ask_action("Do you wish to continue?", writeback)
            if not agreed:
                print 'Aborting.'
            else:
                print 'Done.'


METHODS = {
    "server": Server(),
    "get": Get(),
    "pinging": Pinging(),
    "install": Install(),
    "getall": GetAll(),
    "etchosts": EtcHosts(),
}

def usage(script_name, method=None):
    print "Usage:"
    for name in METHODS:
        if method is None or name == method:
            print ""
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
