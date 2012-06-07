from django.core.cache import cache
from django.utils import importlib
import hashlib
import time


class BaseRosettaStorage(object):
    def __init__(self, request):
        self.request = request

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, val):
        raise NotImplementedError

    def has(self, key):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError


class DummyRosettaStorage(BaseRosettaStorage):
    def get(self, key, default=None):
        return default

    def set(self, key, val):
        pass

    def has(self, key):
        return False

    def delete(self, key):
        pass


class SessionRosettaStorage(BaseRosettaStorage):
    def get(self, key, default=None):
        if key in self.request.session:
            return self.request.session[key]
        return default

    def set(self, key, val):
        self.request.session[key] = val

    def has(self, key):
        return key in self.request.session

    def delete(self, key):
        del(self.request.session[key])


class CacheRosettaStorage(BaseRosettaStorage):
    # unlike the session storage backend, cache is shared among all users
    # so we need to per-user key prefix, which we store in the session
    def __init__(self, request):
        super(CacheRosettaStorage, self).__init__(request)
        if 'rosetta_cache_storage_key_prefix' in self.request.session:
            self._key_prefix = self.request.session['rosetta_cache_storage_key_prefix']
        else:
            self._key_prefix = hashlib.new('sha1', str(time.time())).hexdigest()
            self.request.session['rosetta_cache_storage_key_prefix'] = self._key_prefix

    def get(self, key, default=None):
        #print ('get', self._key_prefix + key)
        return cache.get(self._key_prefix + key, default)

    def set(self, key, val):
        #print ('set', self._key_prefix + key)
        cache.set(self._key_prefix + key, val)

    def has(self, key):
        #print ('has', self._key_prefix + key)
        return (self._key_prefix + key) in cache

    def delete(self, key):
        #print ('del', self._key_prefix + key)
        cache.delete(self._key_prefix + key)


def get_storage(request):
    from rosetta.conf import settings
    storage_module, storage_class = settings.STORAGE_CLASS.rsplit('.', 1)
    storage_module = importlib.import_module(storage_module)
    return getattr(storage_module, storage_class)(request)
