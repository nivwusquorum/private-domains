import socket
import requests
import urllib2


def interpret_reponse(response):
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

def get_ip(server, port, secret, domain):
    payload = {
        'domain': domain,
        'password': secret,
    }
    try:
        r = requests.post('%s:%d/get_ip' % (server, port), data=payload,  timeout=2)
        return interpret_reponse(r)
    except Exception as e:
        print e
        return 'connection_error'

def get_network_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('facebook.com', 0))
    return s.getsockname()[0]


SEND_MIN_WAIT = 30

def send_ip(server, port, secret, my_domain):
    payload = {
        'domain': my_domain,
        'ip': get_network_ip(),
        'password': secret,
    }

    try:
        r = requests.post('%s:%d/save_ip' % (server, port), data=payload, timeout=2)
        return int(r.text.split(' ')[-1])
    except Exception as e:
        return None

def connected_to_internet():
    try:
        _ = urllib2.urlopen("http://74.125.228.100", timeout=3) # one of google's IPs.
        print 'true'
        return True
    except urllib2.URLError:
        print 'false'
        return False
