import os
import django
from django.conf import settings
from rosetta.conf import settings as rosetta_settings
from django.core.cache import cache

from rosetta import polib

try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

FUZZY = 'fuzzy'


def find_pos(lang, project_apps=True, django_apps=False, third_party_apps=False):
    """
    scans a couple possible repositories of gettext catalogs for the given
    language code

    """

    paths = []

    # project/locale
    parts = settings.SETTINGS_MODULE.split('.')
    project = __import__(parts[0], {}, {}, [])
    abs_project_path = os.path.normpath(os.path.abspath(os.path.dirname(project.__file__)))
    if project_apps:
        paths.append(os.path.abspath(os.path.join(os.path.dirname(project.__file__), 'locale')))

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
    for appname in settings.INSTALLED_APPS:
        if rosetta_settings.EXCLUDED_APPLICATIONS and appname in rosetta_settings.EXCLUDED_APPLICATIONS:
            continue
        p = appname.rfind('.')
        if p >= 0:
            app = getattr(__import__(appname[:p], {}, {}, [appname[p + 1:]]), appname[p + 1:])
        else:
            app = __import__(appname, {}, {}, [])

        apppath = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(app.__file__), 'locale')))
        

        # django apps
        if 'contrib' in apppath and 'django' in apppath and not django_apps:
            continue

        # third party external
        if not third_party_apps and abs_project_path not in apppath:
            continue
            
        # local apps
        if not project_apps and abs_project_path in apppath:
            continue
            
        
        if os.path.isdir(apppath):
            paths.append(apppath)
            
            
        
            
    ret = set()
    langs = (lang,)
    if u'-' in lang:
        _l,_c =  map(lambda x:x.lower(),lang.split(u'-'))
        langs += (u'%s_%s' %(_l, _c), u'%s_%s' %(_l, _c.upper()), )
    elif u'_' in lang:
        _l,_c = map(lambda x:x.lower(),lang.split(u'_'))
        langs += (u'%s-%s' %(_l, _c), u'%s-%s' %(_l, _c.upper()), )
        
    paths = map(os.path.normpath, paths)
    for path in paths:
        for lang_ in langs:
            dirname = os.path.join(path, lang_, 'LC_MESSAGES')
            for fn in ('django.po','djangojs.po',):
                filename = os.path.join(dirname, fn)
                if os.path.isfile(filename):
                    ret.add(os.path.abspath(filename))
    return list(ret)

def pagination_range(first,last,current):
    r = []
    
    r.append(first)
    if first + 1 < last: r.append(first+1)
    
    if current -2 > first and current -2 < last: r.append(current-2)
    if current -1 > first and current -1 < last: r.append(current-1)
    if current > first and current < last: r.append(current)
    if current + 1 < last and current+1 > first: r.append(current+1)
    if current + 2 < last and current+2 > first: r.append(current+2)
    
    if last-1 > first: r.append(last-1)
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


def priority_merge(po_destination, po_source, priority=False):
    for entry in po_source:
        e = po_destination.find(entry.msgid)
        if e:
            if (not e.translated() or priority) and entry.translated():
                # entry found, we update if it isn't translated
                e.occurrences = entry.occurrences
                e.comment = entry.comment
                e.msgstr = entry.msgstr
                e.msgstr_plural = entry.msgstr_plural
                if FUZZY in e.flags:
                    e.flags.remove(FUZZY)
        else:
            # entry is not in the po file, we must add it
            # entry is created with msgid, occurrences and comment
            new_entry = polib.POEntry(msgid=entry.msgid,
                                      occurrences=entry.occurrences,
                                      comment=entry.comment,
                                      msgstr=entry.msgstr,
                                      msgstr_plural=entry.msgstr_plural)
            po_destination.append(new_entry)
    po_destination.save()


def get_differences(po_destination, po_source, priority=False):
    l_changes = []
    l_news = []
    for entry_source in po_source:
        entry_destination = po_destination.find(entry_source.msgid)
        item = {}
        if entry_destination:
            if entry_source.translated() and not entry_destination.translated():
                item['entry_source'] = entry_source
                item['entry_destination'] = ""
            elif priority:
                if entry_destination.msgstr != entry_source.msgstr or \
                   entry_destination.msgstr_plural != entry_source.msgstr_plural:
                    item['entry_source'] = entry_source
                    item['entry_destination'] = entry_destination
                    l_changes.append(item)
        else:
            item['entry_source'] = entry_source
            l_news.append(item)
    return l_news, l_changes


def get_app_name(path):
    app = path.split("/locale")[0].split("/")[-1]
    return app
