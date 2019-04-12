import os
import tempfile
from datetime import datetime

import django
from django.apps import apps
from django.conf import ENVIRONMENT_VARIABLE, settings
from django.core.cache import caches
from django.utils import timezone

from rosetta.conf import settings as rosetta_settings


cache = caches[rosetta_settings.ROSETTA_CACHE_NAME]


def timestamp_with_timezone(dt=None):
    """
    Return a timestamp with a timezone for the configured locale.  If all else
    fails, consider localtime to be UTC.
    """
    dt = dt or datetime.now()
    if timezone is None:
        return dt.strftime('%Y-%m-%d %H:%M%z')
    if not dt.tzinfo:
        tz = timezone.get_current_timezone()
        if not tz:
            tz = timezone.utc
        dt = dt.replace(tzinfo=timezone.get_current_timezone())
    return dt.strftime("%Y-%m-%d %H:%M%z")


def find_pos(lang, project_apps=True, django_apps=False, third_party_apps=False):
    """
    scans a couple possible repositories of gettext catalogs for the given
    language code

    """

    paths = []

    # project/locale
    if settings.SETTINGS_MODULE:
        parts = settings.SETTINGS_MODULE.split('.')
    else:
        # if settings.SETTINGS_MODULE is None, we are probably in "test" mode
        # and override_settings() was used
        # see: https://code.djangoproject.com/ticket/25911
        parts = os.environ.get(ENVIRONMENT_VARIABLE).split('.')
    project = __import__(parts[0], {}, {}, [])
    abs_project_path = os.path.normpath(os.path.abspath(os.path.dirname(project.__file__)))
    if project_apps:
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale'))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale')))
        if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(project.__file__), '..', 'locale'))):
            paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), '..', 'locale')))

    case_sensitive_file_system = True
    tmphandle, tmppath = tempfile.mkstemp()
    if os.path.exists(tmppath.upper()):
        # Case insensitive file system.
        case_sensitive_file_system = False

    # django/locale
    if django_apps:
        django_paths = cache.get('rosetta_django_paths')
        if django_paths is None:
            django_paths = []
            for root, dirnames, filename in os.walk(os.path.abspath(os.path.dirname(django.__file__))):
                if 'locale' in dirnames:
                    django_paths.append(os.path.join(root, 'locale'))
                    continue
            cache.set('rosetta_django_paths', django_paths, 60 * 60)
        paths = paths + django_paths
    # settings
    for localepath in settings.LOCALE_PATHS:
        if os.path.isdir(localepath):
            paths.append(localepath)

    # project/app/locale
    for app_ in apps.get_app_configs():
        if rosetta_settings.EXCLUDED_APPLICATIONS and app_.name in rosetta_settings.EXCLUDED_APPLICATIONS:
            continue

        app_path = app_.path
        # django apps
        if 'contrib' in app_path and 'django' in app_path and not django_apps:
            continue

        # third party external
        if not third_party_apps and abs_project_path not in app_path:
            continue

        # local apps
        if not project_apps and abs_project_path in app_path:
            continue

        if os.path.exists(os.path.abspath(os.path.join(app_path, 'locale'))):
            paths.append(os.path.abspath(os.path.join(app_path, 'locale')))
        if os.path.exists(os.path.abspath(os.path.join(app_path, '..', 'locale'))):
            paths.append(os.path.abspath(os.path.join(app_path, '..', 'locale')))

    ret = set()
    langs = [lang]
    if u'-' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'-', 1))
        langs += [u'%s_%s' % (_l, _c), u'%s_%s' % (_l, _c.upper()), u'%s_%s' % (_l, _c.capitalize())]
    elif u'_' in lang:
        _l, _c = map(lambda x: x.lower(), lang.split(u'_', 1))
        langs += [u'%s-%s' % (_l, _c), u'%s-%s' % (_l, _c.upper()), u'%s_%s' % (_l, _c.capitalize())]

    paths = map(os.path.normpath, paths)
    paths = list(set(paths))
    for path in paths:
        # Exclude paths
        if path not in rosetta_settings.ROSETTA_EXCLUDED_PATHS:
            for lang_ in langs:
                dirname = os.path.join(path, lang_, 'LC_MESSAGES')
                for fn in rosetta_settings.POFILENAMES:
                    filename = os.path.join(dirname, fn)
                    abs_path = os.path.abspath(filename)
                    # On case insensitive filesystems (looking at you, MacOS)
                    # compare the lowercase absolute path of the po file
                    # to all lowercased paths already collected.
                    # This is not an issue on sane filesystems
                    if not case_sensitive_file_system:
                        if filename.lower() in [p.lower() for p in ret]:
                            continue
                    if os.path.isfile(abs_path):
                        ret.add(abs_path)
    return list(sorted(ret))


def pagination_range(first, last, current):
    r = []

    r.append(first)
    if first + 1 < last:
        r.append(first + 1)

    if current - 2 > first and current - 2 < last:
        r.append(current - 2)
    if current - 1 > first and current - 1 < last:
        r.append(current - 1)
    if current > first and current < last:
        r.append(current)
    if current + 1 < last and current + 1 > first:
        r.append(current + 1)
    if current + 2 < last and current + 2 > first:
        r.append(current + 2)

    if last - 1 > first:
        r.append(last - 1)
    r.append(last)

    r = list(set(r))
    r.sort()
    prev = 10000
    for e in r[:]:
        if prev + 1 < e:
            try:
                r.insert(r.index(e), '...')
            except ValueError:
                pass
        prev = e
    return r
