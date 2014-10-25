import time
import json
import sys

from os.path import isfile, expanduser, join
from os import remove, getlogin

from network import get_ip, connected_to_internet
from utils import data_dir, exponential_backoff



class InteractiveConfigValidation(object):
    def ask_action(self, message, function, *args, **kwargs):
        reply = None
        while reply not in ['Y', 'n']:
            print '%s [Y/n]: ' % (message,),
            reply = raw_input()
        if reply == 'Y':
            return (function(*args, **kwargs), True)
        else:
            return (None, False)

    def get_config_path(self):
        config_paths = [
            join(data_dir(), ".pdrc_developer"), # dev config
            expanduser("~/.pdrc"), # effective user homedir
            join('/home', getlogin(), '.pdrc'), # logged in user (important for sudo)
        ]
        for path in config_paths:
            if isfile(path):
                return path
        return None

    def test_server(self, server, port):
        response = get_ip(server, port, 'wrong_secret', 'test_domain')
        res = response != 'connection_error'
        if not res:
            print "Could not reach server."
        return res

    def test_secret(self, server, port, secret):
        response = get_ip(server, port, secret, 'test_domain')
        res = response != 'connection_error' and response != 'wrong_secret'
        if not res:
            print "Could not verify secret."
        return res

    def update_server(self, config):
        server_updated = False

        while not server_updated:
            print 'Please type the private domains server IP or DOMAIN (without port): ',
            server = raw_input()
            port = None
            while port is None:
                print 'Please type the private domains server port: ',
                port = raw_input()
                try:
                    port = int(port)
                except:
                    print 'Port has to be an integer'
                    port = None

            if self.test_server(server, port):
                print 'Successfully connected to server :-)'
                server_updated = True
                config['server'] = server
                config['port'] = port
                self.write_back(config)

    def write_back(self, config):
        with open(CONFIG_PATH, "w+") as f:
            f.write(json.dumps(config))

    def update_secret(self, config):
        secret_updated = False
        while not secret_updated:
            print 'Please type secret (copy it over from your server): ',
            secret = raw_input()
            if self.test_secret(config['server'], config['port'], secret):
                print 'Secret verified :-)'
                secret_updated = True
                config['secret'] = secret
                self.write_back(config)

    def run(self, require_domain=False):
        def body():
             print "No Internet connection. Backing off."
        exponential_backoff(lambda: connected_to_internet(), body)

        config = None
        config_path = self.get_config_path()
        if config_path is not None:
            with open(config_path) as config:
                try:
                    config = json.loads(config.read())
                except Exception:
                    msg = "Your .pdrc is damaged. Do you want to remove it?"
                    _, was_removed = self.ask_action(msg, lambda: remove(CONFIG_PATH))
                    if not was_removed:
                        print "Fix your .pdrc and restart."
                        sys.exit(3)
                    else:
                        config = {}

        else:
            config = {}

        if 'server' not in config or 'port' not in config or not self.test_server(config['server'], config['port']):
            self.update_server(config)

        if 'secret' not in config or not self.test_secret(config['server'], config['port'], config['secret']):
            self.update_secret(config)

        if 'domain' not in config and require_domain:
            domain = None
            while domain is None:
                print 'What private domain name would you like to assign to this computer? :',
                domain = raw_input()

                if any([ not word.isalpha() for word in domain.split('_')]) or len(domain) not in range(5,31):
                    print 'Domain name can only use underscores and English letters between 5 and 30 characters.'
                    domain = None
            config['domain'] = domain
            self.write_back(config)

        self._config = config

    def get(self):
        return self._config
