import time
import json
import sys

from os.path import isfile, expanduser
from os import remove

from network import get_ip

CONFIG_PATH = expanduser("~/.pdrc")

class InteractiveConfigValidation(object):
    def ask_action(self, message, function, *args, **kwargs):
        reply = None
        while reply not in ['Y', 'n']:
            print '%s [Y/n]: ' % (message,),
            reply = raw_input()[:-1]
        if reply:
            return (function(*args, **kwargs), True)
        else:
            return (None, False)

    def test_server(self, server, port):
        response = get_ip(server, port, 'wrong_secret', 'test_domain')
        return response != 'connection_error'

    def test_secret(self, server, port, secret):
        response = get_ip(server, port, secret, 'test_domain')
        return response != 'connection_error' and response != 'wrong_secret'

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
            else:
                print 'Connection unsuccessful.'

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
            else:
                print 'Secret could not be verified.'

    def run(self):
        config = None
        if isfile(CONFIG_PATH):
            with open(CONFIG_PATH) as config:
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

        self._config = config

    def get(self):
        return self._config
