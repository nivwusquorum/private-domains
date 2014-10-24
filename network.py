import requests


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
