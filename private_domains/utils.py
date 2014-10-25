import time
import urllib2

from os import getenv, access, X_OK
from os.path import abspath, dirname, join, split, pathsep, exists

def package_dir():
    return dirname(abspath(__file__))

def data_dir():
    return join(package_dir(), 'data')

def timeit(logger):
    def wrap(method):
        def timed(*args, **kw):
            ts = time.time()
            result = method(*args, **kw)
            te = time.time()

            logger.debug('%r (%r, %r) %2.2f sec' % \
                  (method.__name__, args, kw, te-ts))
            return result
        return timed
    return wrap

def exponential_backoff(until_condition, body, intital_backoff=1, max_backoff=1000):
    backoff = intital_backoff
    while not until_condition():
        body()
        time.sleep(backoff)
        backoff = min(backoff*2, max_backoff)

def which(pgm):
    path = getenv('PATH')
    for p in path.split(pathsep):
        p = join(p, pgm)
        if exists(p) and access(p, X_OK):
            return p
