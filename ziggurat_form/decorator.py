import functools

class cached(object):
    def __init__(self, obj):
        self.cache = {}
        self.obj = obj

    def __get__(self, obj, objtype=None):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)

    def __call__(self, *args, **kwargs):
        cache_key = '{}.{}'.format(args, kwargs)
        if cache_key not in self.cache:
            res = self.obj(*args, **kwargs)
            self.cache[cache_key] = res
            return res
        return self.cache[cache_key]
