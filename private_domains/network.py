import socket
import requests
import urllib2


class Network(object):
    SEND_MIN_WAIT = 30

    def __init__(self, server, port, secret, verify_ssl=True, timeout=2):
        self.server = server
        self.port = port
        self.secret = secret
        self.verify_ssl = verify_ssl
        self.timeout = timeout

    def interpret_reponse(self, response):
        if response.status_code == 404:
            return 'not_found'
        elif response.status_code == 403 and response.text == 'WRONG SECRET':
            return 'wrong_secret'
        elif response.status_code == 400 and response.text == 'WRONG DATA':
            return 'wrong_data'
        elif response.status_code == 200:
            return response.text
        else:
            return 'connection_error'

    def make_request(self, path, payload=None):
        return requests.post('%s:%d%s' % (self.server, self.port, path), data=payload,  timeout=self.timeout, verify=self.verify_ssl)

    def get_ip(self, domain):
        payload = {
            'domain': domain,
            'password': self.secret,
        }
        try:
            r = self.make_request('/get_ip', payload)
            return self.interpret_reponse(r)
        except Exception as e:
            print e
            return 'connection_error'

    def get_ips(self):
        payload = {
            'password': self.secret,
        }
        try:
            r = self.make_request('/get_ips', payload)
            return self.interpret_reponse(r)
        except Exception as e:
            print e
            return 'connection_error'

    def get_network_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('facebook.com', 0))
        return s.getsockname()[0]

    def send_ip(self, my_domain):
        payload = {
            'domain': my_domain,
            'ip': self.get_network_ip(),
            'password': self.secret,
        }

        try:
            r = self.make_request('/save_ip', payload)
            return int(r.text.split(' ')[-1])
        except Exception as e:
            return None

    @staticmethod
    def connected_to_internet():
        try:
            _ = urllib2.urlopen("http://74.125.228.100", timeout=3) # one of google's IPs.
            return True
        except urllib2.URLError:
            return False
