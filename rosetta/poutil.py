import os, hashlib
from django.conf import settings
from rosetta.conf import settings as rosetta_settings
import polib

from django.utils import translation

filters = ('project', 'django', 'third-party')

def init_pofiles():
    all_pofiles = {}
    for l in rosetta_settings.LANGUAGES:
        lang_pos = {}
        for filter in filters:
            for p in find_pos(l[0], filter):
                path = os.path.realpath(p)
                writable = os.access(path, os.W_OK)
                if rosetta_settings.EXCLUDE_READONLY and not writable:
                    continue
                appname = path.rsplit("/locale", 1)[0].rsplit("/", 1)[-1]
                lang_pos[appname] = {
                    'appname' : appname,
                    'path'    : path,
                    'filter'  : filter,
                    'writable': writable,
                    'pofile'  : None,
                    'last_modified': 0,
                }
        all_pofiles[l[0]] = lang_pos
    return all_pofiles

def find_pos(lang, scope):
    """ possible scope values are ('project', 'django', 'third-party') """

    paths = set()
    def _path(appname):
        p = appname.rfind('.')
        if p >= 0: # from somewhere import appname
            app = getattr(__import__(appname[:p], {}, {}, [appname[p+1:]]), appname[p+1:])
        else: # import appname
            app = __import__(appname, {}, {}, [])

        return os.path.normpath(os.path.dirname(os.path.abspath(app.__file__)))

    def walk_down(path):
        return set(os.path.join(dir , 'locale') for dir, ds, fs in os.walk(path) if 'locale' in ds)

    project_path = _path('settings')
    django_path  = _path('django')

    if scope == 'django':
        paths = walk_down(django_path)

    elif scope == 'project':
        if settings.LOCALE_PATHS:
            paths = set(os.path.abspath(p) for p in settings.LOCALE_PATHS)
        else:
            paths = walk_down(project_path)

    elif scope == 'third-party':
        for appname in settings.INSTALLED_APPS:
            if appname in rosetta_settings.EXCLUDED_APPLICATIONS:
                continue

            apppath = _path(appname)

            if django_path in apppath or project_path in apppath:
                continue

            if os.path.exists(os.path.join(apppath, 'locale')):
                paths.add(apppath)

    ret = set()
    locale = translation.to_locale(lang)
    for path in paths:
        dirname = os.path.join(path, locale, 'LC_MESSAGES')
        for fn in ('django.po','djangojs.po',):
            filename = os.path.join(dirname, fn)
            if os.path.isfile(filename):
                ret.add(os.path.abspath(filename))
    return list(ret)

pofiles = init_pofiles()

def upd_pofile(po):
    last_modified = os.path.getmtime(po['path'])
    if last_modified > po['last_modified']: #ie version in cache outdated
        po['pofile'] = polib.pofile(po['path'],
                    klass=SmartPOFile,
                    wrapwidth=rosetta_settings.POFILE_WRAP_WIDTH
                )
        po['last_modified'] = last_modified
        entries = {}
        for entry in po['pofile']:
            entries[hashlib.md5(entry.msgid.encode('utf8')).hexdigest()] = entry
        po['entries'] = entries
    elif last_modified < po['last_modified'] and po['writable']:
        try:
            po['pofile'].save()
            po['pofile'].save_as_mofile(po['path'].replace('.po','.mo'))
        except IOError:
            po['writable'] = False
        else: #saving itself takes some time
            po['last_modified'] = os.path.getmtime(po['path'])

    return po

def upd_stats(po):

    def get_stats_from_parsed_po(pofile):
        return {
                'translated_entries'  : len(pofile.translated_entries()),
                'untranslated_entries': len(pofile.untranslated_entries()),
                'fuzzy_entries'       : len(pofile.fuzzy_entries()),
                'obsolete_entries'    : len(pofile.obsolete_entries()),
            }

    if po['pofile']:
        if os.path.getmtime(po['path']) <= po['last_modified']:
            return get_stats_from_parsed_po(po['pofile'])

    fhandle = open(po['path'])
    search_strings = {
        'Translated-entries'  : 'translated_entries',
        'Untranslated-entries': 'untranslated_entries',
        'Fuzzy-entries'       : 'fuzzy_entries',
        'Obsolete-entries'    : 'obsolete_entries',
    }
    data = {}
    for i in range(30):
        line = fhandle.readline().strip(' "\'\n\\n')
        for source, target in search_strings.items():
            if line.startswith(source):
                try:
                    data[target] = int(line.rsplit(':')[-1])
                except ValueError:
                    pass

    if not data:
        pofile = upd_pofile(po)['pofile']
        pofile.save()
        return get_stats_from_parsed_po(pofile)

    return data

class SmartPOFile(polib.POFile):
    """ polib.POFile with additional hook to save translation progress in metadata """
    def save(self, *args, **kwargs):
        self.metadata['Translated-entries']  = len(self.translated_entries())
        self.metadata['Untranslated-entries']= len(self.untranslated_entries())
        self.metadata['Fuzzy-entries']       = len(self.fuzzy_entries())
        self.metadata['Obsolete-entries']    = len(self.obsolete_entries())
        return super(SmartPOFile, self).save(*args, **kwargs)

def pagination_range(first,last,current):
    if last<10:
        return range(1,1+last)

    assert first <= current <= last
    r = [first, first+1, current-2, current-1, current, current+1, current+2, last-1, last]
    r = list(set(r))
    r.sort()
    r = filter(lambda x: first <= x <= last, r)

    if current-2 > first + 1: r.insert(first + 1, '...')
    if current+2 < last - 2:  r.insert(-2, '...')

    return r
