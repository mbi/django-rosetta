from datetime import datetime
from pathlib import Path

from django.core.cache import caches
from django.utils.translation.reloader import translation_file_changed

from .conf import settings as rosetta_settings


cache = caches[rosetta_settings.ROSETTA_CACHE_NAME]

# This is a global, not a thread local variable, because so is Django's
# translation cache, see django.utils.translation.trans_real._translations
TIMESTAMP = None
TIMESTAMP_CACHE_KEY = "ROSETTA_TIMESTAMP"


def AutoReloadMiddleware(get_response):
    def _AutoReloadMiddleware(request):
        global TIMESTAMP

        # Get last time changes were made to rosetta.
        cached_timestamp = cache.get(TIMESTAMP_CACHE_KEY)

        # If the cache was empty or cleared then we need to set an initial value.
        if not cached_timestamp:
            cached_timestamp = datetime.now().timestamp()
            cache.set(TIMESTAMP_CACHE_KEY, cached_timestamp)

        # If TIMESTAMP is None then this is a new process that just
        # received the first request, so no need to cleare the cache.
        if TIMESTAMP is None:
            TIMESTAMP = cached_timestamp

        # If TIMESTAMP doesn't match the last time changes were made to rosetta
        # then clear the whole translation cache for this process.
        if TIMESTAMP != cached_timestamp:
            TIMESTAMP = cached_timestamp
            # Clear translation cache for all languages
            translation_file_changed(sender=None, file_path=Path("dummy.mo"))

        return get_response(request)

    return _AutoReloadMiddleware if rosetta_settings.AUTO_RELOAD else get_response
