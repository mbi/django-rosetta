import re, rosetta, datetime, unicodedata, hashlib, os

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

@never_cache
@user_passes_test(lambda user:can_translate(user),settings.LOGIN_URL)
def list_languages(request):
    """
    Lists the languages for the current project, the gettext catalog files
    that can be translated and their translation progress
    """
    languages = []

    filter = request.GET.get('filter', 'project') # possible values are: all, project (default), third-party, django

    third_party_apps= filter in ('all', 'third-party')
    django_apps     = filter in ('all', 'django')
    project_apps    = filter in ('all', 'project')

    has_pos = False
    for language in available_languages(request.user):
        pos = poutil.find_pos(language[0], project_apps, django_apps, third_party_apps)
        has_pos = has_pos or bool(pos)
        languages.append(
            (
                language[0],
                language[1],
                [(get_app_name(l), os.path.realpath(l), polib.pofile(l)) for l in  pos],
            )
        )

    return shortcuts.render_to_response('rosetta/languages.html', {
            'version' : rosetta.get_version(True),
            'has_pos' : has_pos,
            'filter'  : filter,
            'languages': languages,
            'ADMIN_MEDIA_PREFIX' : settings.ADMIN_MEDIA_PREFIX,
        }, context_instance=template.RequestContext(request))

def pofile_by_appname(appname, lang):
    for po in poutil.find_pos(lang, True, True, True):
        if appname == get_app_name(po):
            return po
    raise http.Http404


@never_cache
@user_passes_test(lambda user:can_translate(user), settings.LOGIN_URL)
def translate(request, appname, lang, filter='all', page=1):
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

    if lang not in [l[0] for l in available_languages(request.user)]:
        raise http.Http404

    rosetta_i18n_fn = pofile_by_appname(appname, lang)

    is_bidi = lang.split('-')[0] in settings.LANGUAGES_BIDI
    try:
        os.utime(rosetta_i18n_fn,None)
        rosetta_i18n_write = True
    except OSError:
        rosetta_i18n_write = False

    if rosetta_i18n_write:
        rosetta_i18n_pofile = polib.pofile(rosetta_i18n_fn)
    else:
        if 'rosetta_i18n_pofile' not in request.session:
            request.session['rosetta_i18n_pofile'] = polib.pofile(rosetta_i18n_fn)
        rosetta_i18n_pofile = request.session['rosetta_i18n_pofile']

    if '_next' in request.POST:
        rx = re.compile(r'^m_([0-9a-f]+)')
        rx_plural = re.compile(r'^m_([0-9a-f]+)_([0-9]+)')
        file_change = False

        entries = {}
        for entry in rosetta_i18n_pofile:
            entries[hashlib.md5(entry.msgid.encode('utf8')).hexdigest()] = entry.msgid

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
                entry_text = entries.get(md5hash)
                entry = entry_text and rosetta_i18n_pofile.find(entry_text)
                # If someone did a makemessage, some entries might
                # have been removed, so we need to check.
                if entry:
                    old_msgstr = entry.msgstr

                    if plural_id is not None:
                        plural_string = fix_nls(entry.msgstr_plural[plural_id], value)
                        entry.msgstr_plural[plural_id] = plural_string
                    else:
                        entry.msgstr = fix_nls(entry.msgid, value)

                    is_fuzzy = bool(request.POST.get('f_%s' % md5hash, False))
                    old_fuzzy = 'fuzzy' in entry.flags

                    if old_fuzzy and not is_fuzzy:
                        entry.flags.remove('fuzzy')
                    elif not old_fuzzy and is_fuzzy:
                        entry.flags.append('fuzzy')

                    file_change = True

                    if old_msgstr != value or old_fuzzy != is_fuzzy:
                        entry_changed.send(sender=entry,
                                           user=request.user,
                                           old_msgstr = old_msgstr,
                                           old_fuzzy = old_fuzzy,
                                           pofile = rosetta_i18n_fn,
                                           language_code = lang,
                                        )

                else:
                    request.session['rosetta_last_save_error'] = True


        if file_change and rosetta_i18n_write:

            try:
                rosetta_i18n_pofile.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" %(request.user.first_name,request.user.last_name,request.user.email)).encode('ascii', 'ignore')
                rosetta_i18n_pofile.metadata['X-Translated-Using'] = u"django-rosetta %s" % rosetta.get_version(False)
                rosetta_i18n_pofile.metadata['PO-Revision-Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M%z')
            except UnicodeDecodeError:
                pass

            try:
                rosetta_i18n_pofile.save()
                rosetta_i18n_pofile.save_as_mofile(rosetta_i18n_fn.replace('.po','.mo'))

                post_save.send(sender=None,language_code=lang,request=request)

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
                        import uwsgi
                        # pretty easy right?
                        uwsgi.reload()
                    except:
                        # we may not be running under uwsgi :P
                        pass
            except IOError:
                request.session['rosetta_i18n_write'] = False

            request.session['rosetta_i18n_pofile']=rosetta_i18n_pofile

            return shortcuts.redirect(request.path + '?' + request.META['QUERY_STRING'])

    lang_name = dict(settings.LANGUAGES)[lang]

    if filter == 'untranslated':
        entries_source = rosetta_i18n_pofile.untranslated_entries()
    elif filter == 'translated':
        entries_source = rosetta_i18n_pofile.translated_entries()
    elif filter == 'fuzzy':
        entries_source = rosetta_i18n_pofile.fuzzy_entries()
    else:
        entries_source = (e for e in rosetta_i18n_pofile if not e.obsolete)

    query = request.GET.get('q', '').strip()
    if query:
        rx = re.compile(re.escape(query), re.IGNORECASE)
        entries_source = (e for e in entries_source if rx.search("\n".join((smart_unicode(e.msgstr), smart_unicode(e.msgid), u''.join([o[0] for o in e.occurrences])))))

    paginator = Paginator(list(entries_source), rosetta_settings.MESSAGES_PER_PAGE)

    if int(page) <= paginator.num_pages and int(page) > 0:
        page = int(page)
    else:
        page = 1

    messages = paginator.page(page).object_list
    for message in messages:
        message.md5hash = hashlib.md5(message.msgid.encode('utf8')).hexdigest()

    if rosetta_settings.MAIN_LANGUAGE and rosetta_settings.MAIN_LANGUAGE != lang:

        main_language = None
        for language in settings.LANGUAGES:
            if language[0] == rosetta_settings.MAIN_LANGUAGE:
                main_language = _(language[1])
                break

        fl = ("/%s/" % rosetta_settings.MAIN_LANGUAGE).join(rosetta_i18n_fn.split("/%s/" % lang))
        po = polib.pofile(fl)

        main_messages = []
        for message in messages:
            message.main_lang = po.find(message.msgid).msgstr

    needs_pagination = paginator.num_pages > 1
    if needs_pagination:
        if paginator.num_pages >= 10:
            page_range = poutil.pagination_range(1, paginator.num_pages, page)
        else:
            page_range = range(1,1+paginator.num_pages)
    ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    ENABLE_TRANSLATION_SUGGESTIONS = rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS

    MESSAGES_SOURCE_LANGUAGE_NAME = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_NAME
    MESSAGES_SOURCE_LANGUAGE_CODE = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE

    if 'rosetta_last_save_error' in request.session:
        del(request.session['rosetta_last_save_error'])
        rosetta_last_save_error = True

    version = rosetta.get_version(True)

    return shortcuts.render_to_response('rosetta/pofile.html', locals(), context_instance=template.RequestContext(request))

@never_cache
@user_passes_test(lambda user:can_translate(user),settings.LOGIN_URL)
def download_file(request, appname, lang):
    import zipfile, os
    from StringIO import StringIO
    # original filename
    rosetta_i18n_fn = pofile_by_appname(appname, lang)
    # in-session modified catalog
    if request.session.get('rosetta_i18n_write'):
        rosetta_i18n_pofile = polib.pofile(rosetta_i18n_fn)
    else:
        rosetta_i18n_pofile = request.session.get('rosetta_i18n_pofile')

    if not rosetta_i18n_fn or not rosetta_i18n_pofile:
        raise http.Http404

    if len(rosetta_i18n_fn.split('/')) >= 5:
        offered_fn = '_'.join(rosetta_i18n_fn.split('/')[-5:])
    else:
        offered_fn = rosetta_i18n_fn.split('/')[-1]
    po_fn = str(rosetta_i18n_fn.split('/')[-1])
    mo_fn = str(po_fn.replace('.po','.mo')) # not so smart, huh
    zipdata = StringIO()
    zipf = zipfile.ZipFile(zipdata, mode="w")
    zipf.writestr(po_fn, unicode(rosetta_i18n_pofile).encode("utf8"))
    zipf.writestr(mo_fn, rosetta_i18n_pofile.to_binary())
    zipf.close()
    zipdata.seek(0)

    response = http.HttpResponse(zipdata.read())
    response['Content-Disposition'] = 'attachment; filename=%s.%s.zip' %(offered_fn, lang)
    response['Content-Type'] = 'application/x-zip'
    return response

def get_app_name(path):
    app = path.split("/locale")[0].split("/")[-1]
    return app

def available_languages(user):
    if not user.is_authenticated():
        return []

    languages = settings.LANGUAGES
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
