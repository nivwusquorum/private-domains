import time
import json
import sys

from os.path import isfile, expanduser, join
from os import remove, getlogin

from network import Network
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
        ]
        try:
            # logged in user (important for sudo), but not all distros support it
            config_paths.append(join('/home', getlogin(), '.pdrc'))
        except OSError:
            pass

        for path in config_paths:
            if isfile(path):
                return path
        return None

    def test_server(self, config):
        network = Network(config['server'], config['port'], 'wrong_secret', config['verify_ssl'])

        response = network.get_ip('test_domain')
        res = response != 'connection_error'
        if not res:
            print "Could not reach server."
        return res

    def test_secret(self, config):
        network = Network(config['server'], config['port'], config['secret'], config['verify_ssl'])

        response = network.get_ip('test_domain')
        res = response != 'connection_error' and response != 'wrong_secret'
        if not res:
            print "Could not verify secret."
        return res

    def update_server(self, config):
        server_updated = False

        while not server_updated:
            print 'Please type the private domains server IP or DOMAIN (without port but including protocol): ',
            server = raw_input()

            if 'https' in server:
                default_port = 443
            else:
                default_port = 80
            port = None
            while port is None:
                print 'Please type the private domains server port[%d]: ' % (default_port,),
                port = raw_input()
                if port == '':
                    port = default_port
                try:
                    port = int(port)
                except:
                    print 'Port has to be an integer'
                    port = None
            updated_config = dict(config.items() + {'server':server, 'port': port}.items())
            if self.test_server(updated_config):
                print 'Successfully connected to server :-)'
                server_updated = True
                config.update(updated_config)
                self.write_back(config)

    def write_back(self, config):
        path = self.get_config_path()
        if path is None:  # file does not exist yet
            path = expanduser("~/.pdrc")
        with open(path, "w+") as f:
            f.write(json.dumps(config))

    def update_secret(self, config):
        secret_updated = False
        while not secret_updated:
            print 'Please type secret (copy it over from your server): ',
            secret = raw_input()
            updated_config = dict(config.items() + {'secret': secret}.items())

            if self.test_secret(updated_config):
                print 'Secret verified :-)'
                secret_updated = True
                config.update(updated_config)
                self.write_back(config)

    def run(self, require_domain=False):
        def body():
             print "No Internet connection. Backing off."
        exponential_backoff(lambda: Network.connected_to_internet(), body)

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

        if not 'verify_ssl' in config:
            _, verify_ssl = self.ask_action("Do you wish to perform ssl verification?", lambda: ())
            config['verify_ssl'] = verify_ssl
            self.write_back(config)

        if 'server' not in config or 'port' not in config or not self.test_server(config):
            self.update_server(config)

        if 'secret' not in config or not self.test_secret(config):
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
