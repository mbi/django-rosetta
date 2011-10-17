import re, rosetta, datetime, unicodedata, hashlib, os, zipfile
import time
from StringIO import StringIO

from django.conf import settings

from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django import http, template, shortcuts

from django.utils.encoding import smart_unicode, iri_to_uri
from django.utils.translation import ugettext_lazy as _
from rosetta.conf import settings as rosetta_settings
from rosetta import poutil, polib
from rosetta.signals import entry_changed, post_save

_pofiles = {} # see init_pofiles for struct
_filters = {
    'project' : (True, False, False),
    'django'  : (False, True, False),
    'third-party': (False, False, True),
}

def upd_pofile(po):
    last_modified = os.path.getmtime(po['path'])
    if last_modified > po['last_modified']: #ie version in cache outdated
        po['pofile'] = polib.pofile(po['path'])
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

def init_pofiles():
    pofiles = {}
    for l in rosetta_settings.LANGUAGES:
        lang_pos = {}
        for filter, values in _filters.items():
            for p in poutil.find_pos(l[0], *values):
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
        pofiles[l[0]] = lang_pos
    return pofiles

_pofiles = init_pofiles()

@never_cache
@user_passes_test(lambda user:can_translate(user),settings.LOGIN_URL)
def list_languages(request):
    """
    Lists the languages for the current project, the gettext catalog files
    that can be translated and their translation progress
    """
    filter = request.GET.get('filter', 'project')

    if filter != 'all' and filter not in _filters:
        raise http.Http404

    languages = []
    for l in available_languages(request.user):
        pos = [upd_pofile(po) for po in _pofiles[l[0]].values() if filter=='all' or filter==po['filter']]
        if pos:
            languages.append((l[0], l[1], pos))

    return shortcuts.render_to_response('rosetta/languages.html', {
            'filter'  : filter,
            'languages': languages,
            'ADMIN_MEDIA_PREFIX' : settings.ADMIN_MEDIA_PREFIX,
        }, context_instance=template.RequestContext(request))

def pofile_by_appname(appname, lang, user):
    if lang not in [l[0] for l in available_languages(user)]:
        raise http.Http404

    if lang not in _pofiles:
        raise http.Http404

    if appname not in _pofiles[lang]:
        raise http.Http404

    return upd_pofile(_pofiles[lang][appname])

@never_cache
@user_passes_test(lambda user:can_translate(user), settings.LOGIN_URL)
def translate(request, appname, rosetta_i18n_lang_code, filter='all', page=1):
    """
    Displays a list of messages to be translated
    """

    def fix_nls(in_,out_):
        """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
        """
        if 0 == len(in_) or 0 == len(out_):
            return out_

        if "\r" in out_ and "\r" not in in_:
            out_=out_.replace("\r",'')

        if "\n" == in_[0] and "\n" != out_[0]:
            out_ = "\n" + out_
        elif "\n" != in_[0] and "\n" == out_[0]:
            out_ = out_.lstrip()

        if "\n" == in_[-1] and "\n" != out_[-1]:
            out_ += "\n"
        elif "\n" != in_[-1] and "\n" == out_[-1]:
            out_ = out_.rstrip()

        return out_

    po = pofile_by_appname(appname, rosetta_i18n_lang_code, request.user)
    rosetta_i18n_fn    = po['path']
    rosetta_i18n_write = po['writable']
    rosetta_last_save_error = False

    if '_next' in request.POST:
        rx = re.compile(r'm_([0-9a-f]+)')
        rx_plural = re.compile(r'm_([0-9a-f]+)_([0-9]+)')
        file_change = False

        for key, value in request.POST.items():
            md5hash = None
            plural_id = None

            if rx_plural.match(key):
                md5hash = str(rx_plural.match(key).groups()[0])
                # polib parses .po files into unicode strings, but
                # doesn't bother to convert plural indexes to int,
                # so we need unicode here.
                plural_id = unicode(rx_plural.match(key).groups()[1])

            elif rx.match(key):
                md5hash = str(rx.match(key).groups()[0])

            if md5hash is not None:
                entry = po['entries'].get(md5hash)
                # If someone did a makemessage, some entries might
                # have been removed, so we need to check.
                if entry:
                    entry_change = False
                    old_msgstr = entry.msgstr

                    if plural_id is not None:
                        plural_string = fix_nls(entry.msgstr_plural[plural_id], value)
                        entry_change = entry_changed or entry.msgstr_plural[plural_id] != plural_string
                        entry.msgstr_plural[plural_id] = plural_string
                    else:
                        msgstr = fix_nls(entry.msgid, value)
                        entry_change = entry_changed or entry.msgstr != msgstr
                        entry.msgstr = msgstr

                    old_fuzzy = 'fuzzy' in entry.flags
                    new_fuzzy = bool(request.POST.get('f_%s' % md5hash, False))
                    if new_fuzzy != old_fuzzy:
                        entry_change = True
                        if new_fuzzy:
                            entry.flags.append('fuzzy')
                        else:
                            entry.flags.remove('fuzzy')

                    if entry_change:
                        file_change = True
                        entry_changed.send(sender=entry,
                                           user=request.user,
                                           old_msgstr = old_msgstr,
                                           old_fuzzy = old_fuzzy,
                                           pofile = po['pofile'],
                                           language_code = rosetta_i18n_lang_code,
                                        )
                else:
                    rosetta_last_save_error = True

        if file_change:
            try:
                po['pofile'].metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" %(request.user.first_name,request.user.last_name,request.user.email)).encode('ascii', 'ignore')
                po['pofile'].metadata['X-Translated-Using'] = u"django-rosetta %s" % rosetta.get_version(False)
                po['pofile'].metadata['PO-Revision-Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M%z')
            except UnicodeDecodeError:
                pass

            po['last_modified'] = time.time()
            po = upd_pofile(po)

            post_save.send(sender=None,language_code=rosetta_i18n_lang_code,request=request)

            # Try auto-reloading via the WSGI daemon mode reload mechanism
            if  rosetta_settings.WSGI_AUTO_RELOAD and \
                request.environ.has_key('mod_wsgi.process_group') and \
                request.environ.get('mod_wsgi.process_group',None) and \
                request.environ.has_key('SCRIPT_FILENAME') and \
                int(request.environ.get('mod_wsgi.script_reloading', '0')):
                    try:
                        os.utime(request.environ.get('SCRIPT_FILENAME'), None)
                    except OSError:
                        pass
            # Try auto-reloading via uwsgi daemon reload mechanism
            if rosetta_settings.UWSGI_AUTO_RELOAD:
                try:
                    import uwsgi # pretty easy right?
                    uwsgi.reload()
                except: # we may not be running under uwsgi :P
                    pass

            return shortcuts.redirect(request.path + '?' + request.META['QUERY_STRING'])

    if filter == 'untranslated':
        entries_source = po['pofile'].untranslated_entries()
    elif filter == 'translated':
        entries_source = po['pofile'].translated_entries()
    elif filter == 'fuzzy':
        entries_source = po['pofile'].fuzzy_entries()
    else:
        entries_source = (e for e in po['pofile'] if not e.obsolete)

    query = request.GET.get('q', '').strip()
    if query:
        rx = re.compile(re.escape(query), re.IGNORECASE)
        entries_source = (e for e in entries_source if rx.search("\n".join((smart_unicode(e.msgstr), smart_unicode(e.msgid), u''.join([o[0] for o in e.occurrences])))))

    paginator = Paginator(list(entries_source), rosetta_settings.MESSAGES_PER_PAGE)

    if int(page) <= paginator.num_pages and int(page) > 0:
        page = int(page)
    else:
        page = 1

    rosetta_messages = paginator.page(page).object_list
    for message in rosetta_messages:
        message.md5hash = hashlib.md5(message.msgid.encode('utf8')).hexdigest()

    if rosetta_settings.MAIN_LANGUAGE and rosetta_settings.MAIN_LANGUAGE != rosetta_i18n_lang_code:
        main_language = dict(rosetta_settings.LANGUAGES).get(rosetta_settings.MAIN_LANGUAGE)

        fl = ("/%s/" % rosetta_settings.MAIN_LANGUAGE).join(rosetta_i18n_fn.split("/%s/" % rosetta_i18n_lang_code))
        po = polib.pofile(fl)

        main_messages = []
        for message in messages:
            message.main_lang = po.find(message.msgid).msgstr

    return shortcuts.render_to_response('rosetta/pofile.html', {
            'rosetta_i18n_fn'       : rosetta_i18n_fn,
            'rosetta_i18n_write'    : rosetta_i18n_write,
            'rosetta_i18n_pofile'   : po['pofile'],
            'rosetta_i18n_lang_bidi': rosetta_i18n_lang_code.split('-', 1)[0] in settings.LANGUAGES_BIDI,
            'rosetta_messages'      : rosetta_messages,
            'rosetta_i18n_lang_name': dict(rosetta_settings.LANGUAGES)[rosetta_i18n_lang_code],
            'rosetta_i18n_lang_code': rosetta_i18n_lang_code,
            'rosetta_i18n_app'      : appname,
            'rosetta_i18n_filter'   : filter,
            'rosetta_last_save_error' : rosetta_last_save_error,

            'ADMIN_MEDIA_PREFIX'             : settings.ADMIN_MEDIA_PREFIX,
            'ENABLE_TRANSLATION_SUGGESTIONS' : rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS,
            'MESSAGES_SOURCE_LANGUAGE_NAME'  : rosetta_settings.MESSAGES_SOURCE_LANGUAGE_NAME,
            'MESSAGES_SOURCE_LANGUAGE_CODE'  : rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE,

            'query'                   : query,
            'paginator'               : paginator,
            'needs_pagination'        : paginator.num_pages > 1,
            'page_range'              : poutil.pagination_range(1, paginator.num_pages, page),
            'page'                    : page,
        }, context_instance=template.RequestContext(request))

@never_cache
@user_passes_test(lambda user:can_translate(user),settings.LOGIN_URL)
def download_file(request, appname, rosetta_i18n_lang_code):
    po = pofile_by_appname(appname, rosetta_i18n_lang_code, request.user)

    offered_fn = '_'.join(po['path'].split('/')[-5:])
    po_fn = str(po['path'].split('/')[-1])
    mo_fn = str(po_fn.replace('.po','.mo')) # not so smart, huh
    zipdata = StringIO()
    zipf = zipfile.ZipFile(zipdata, mode="w")
    zipf.writestr(po_fn, unicode(po['pofile']).encode("utf8"))
    zipf.writestr(mo_fn, po['pofile'].to_binary())
    zipf.close()
    zipdata.seek(0)

    response = http.HttpResponse(zipdata.read())
    response['Content-Disposition'] = 'attachment; filename=%s.%s.zip' %(offered_fn, rosetta_i18n_lang_code)
    response['Content-Type'] = 'application/x-zip'
    return response

def available_languages(user):
    if not user.is_authenticated():
        return []

    languages = rosetta_settings.LANGUAGES
    if user.is_superuser and user.is_staff:
        return languages

    user_groups = set([group['name'] for group in user.groups.filter(name__startswith='translators').values('name')])
    if 'translators' in user_groups:
        return languages

    permitted_languages = []
    for lang in languages:
        if 'translators_'+lang[0] in user_groups:
            permitted_languages.append(lang)
    return permitted_languages

def can_translate(user):
    return bool(available_languages(user))

def can_reload_wsgi(user):
    return user.is_superuser and user.is_staff
