import socket
import requests
import time

SERVER = "http://localhost"
PORT = 5555
MY_DOMAIN = 'lenovo_laptop'
SECRET = 'gzkfqqurkvnjtagjfmxi'
MIN_WAIT = 10
def get_network_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('facebook.com', 0))
    return s.getsockname()[0]

payload = {
    'domain': MY_DOMAIN,
    'ip': get_network_ip(),
    'password': SECRET,
}

while True:
    r = requests.post('%s:%d/save_ip' % (SERVER,PORT), data=payload)
    next_update = int(r.text.split(' ')[-1])
    time.sleep(max(MIN_WAIT, next_update))
