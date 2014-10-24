import hashlib
import random
import re
import sqlite3
import time
import sys
import time

from contextlib import closing
from flask import Flask, request, g, render_template
from os.path import isfile, join

from utils import timeit, data_dir

app = Flask(__name__)

DATABASE = join(data_dir(), 'pd.db')
SQL_INIT_FILE = join(data_dir(), 'schema.sql')

CONFIG_DEFAULTS = {
    'ping_frequency' : 60,
}

DEBUG = True

class DatabaseHandler(object):
    def __init__(self):
        self.database_exists = None

    def init_state(self):
        with closing(sqlite3.connect(DATABASE)) as db:
            with app.open_resource(SQL_INIT_FILE, mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

    def connect(self):
        self.database_exists = self.database_exists or isfile(DATABASE)
        if not self.database_exists:
            self.init_state()
            self.database_exists = True
        return sqlite3.connect(DATABASE)

    def get(self):
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = self.connect()
        return db

    def query(self, query, args=(), one=False):
        cur = self.get().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

    # query each time to ensure fresh data
    # do not execute too frequently
    def get_config(self, key):
        config_dict = {}
        for conf in self.query('select * from config'):
            config_dict[conf[0]] = conf[1]

        res = config_dict.get(key)
        if res is None and key in CONFIG_DEFAULTS:
            return CONFIG_DEFAULTS[key]
        return res

    def get_ip(self, domain):
        return self.query('select ip from domains where domain=?', (domain,), True)

    def get_domains(self):
        for dom in self.query('select * from domains'):
            yield dom

    def update_config(self, key, value):
        self.get().execute('insert or replace into config (key, value) values (?,?)', (key, value))
        self.get().commit()

    def update_domain(self, domain, ip):
        self.get().execute('insert or replace into domains (domain, ip, lastping_ms) values (?,?,?)', (domain, ip, int(time.time()*1000)))
        self.get().commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

db = DatabaseHandler()

def random_secret():
    s = []
    for _ in range(20):
        s.append(chr(random.randint(97,122)))
    return ''.join(s)

from utils import timeit

@app.route("/save_ip", methods=['GET', 'POST'])
@timeit(app.logger)
def save_ip():
    if request.method == 'GET':
        return 'do this from a script...'
    secret_hash = db.get_config('secret_hash')
    if secret_hash is None:
        return "NO SECRET", 503

    domain = request.form.get('domain')
    ip = request.form.get('ip')
    password = request.form.get('password')
    print type(password)

    if type(password) != unicode or hashlib.sha224(password).hexdigest() != secret_hash:
        return "WRONG SECRET"


    if (type(domain) != unicode or type(ip) != unicode or
        not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) or
        any([ not word.isalpha() for word in domain.split('_')])
        or len(domain) not in range(5,31)):
        return "WRONG DATA", 400

    db.update_domain(domain, ip)

    return "OK NEXT UPDATE SECONDS %d" % (db.get_config('ping_frequency'))

@app.route("/get_ip", methods=['GET', 'POST'])
def get_ip():
    if request.method == 'GET':
        return 'do this from a script...'
    secret_hash = db.get_config('secret_hash')
    if secret_hash is None:
        return "NO SECRET", 503

    domain = request.form.get('domain')
    password = request.form.get('password')

    if type(password) != unicode or hashlib.sha224(password).hexdigest() != secret_hash:
        return "WRONG SECRET", 403

    if type(domain) != unicode:
        return "WRONG DATA", 400

    ip = db.get_ip(domain)
    return ip if ip else ("NOT FOUND", 404)

def create_secret():
    s = random_secret()
    db.update_config('secret_hash', hashlib.sha224(s).hexdigest())
    return """"CREATED NEW SECRET:<br>
              %s<br>
              PLEASE STORE SAFELY'
              <script>
              document.cookie="secret=%s";
              </script>
           """ % (s,s)

@app.route("/", methods=['GET'])
@app.route("/domains", methods=['GET'])
def index():
    secret_hash = db.get_config('secret_hash')
    if secret_hash is None:
        return create_secret()
    cookies_secret = request.cookies.get('secret')
    if type(cookies_secret) != unicode or hashlib.sha224(cookies_secret).hexdigest() != secret_hash:
        return "set your cookies straight"
    ping_frequency = db.get_config('ping_frequency')

    processed_domains = []
    for domain, ip, last_ping_ms in db.get_domains():
        time_since_ping = int(time.time()*1000) - last_ping_ms
        alive = time_since_ping <= 3*ping_frequency*1000

        processed_domains.append((domain, ip, alive, time_since_ping))

    return render_template("domains.html", domains=processed_domains)


@app.route("/configuration", methods=['GET', 'POST'])
def configuration():
    secret_hash = db.get_config('secret_hash')
    if secret_hash is None:
        return create_secret()
    cookies_secret = request.cookies.get('secret')
    if type(cookies_secret) != unicode or hashlib.sha224(cookies_secret).hexdigest() != secret_hash:
        return "set your cookies straight"
    ping_frequency = db.get_config('ping_frequency')


    return render_template("configuration.html", secret=cookies_secret)
    #return "SECRET OK: %s<br>%s" % (cookies_secret,'\n'.join(domain_string))

