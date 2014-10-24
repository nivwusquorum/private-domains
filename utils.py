import time

from os.path import abspath, dirname

def get_distribution_directory():
    return dirname(abspath(__file__))

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
