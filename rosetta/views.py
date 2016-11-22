from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.utils.encoding import force_text
from django.contrib import messages

from microsofttranslator import Translator, TranslateApiException

from rosetta.conf import settings as rosetta_settings
from polib import pofile
from rosetta.poutil import find_pos, pagination_range, timestamp_with_timezone
from rosetta.signals import entry_changed, post_save
from rosetta.storage import get_storage
from rosetta.access import can_translate, can_translate_language

import json
import re
import rosetta
import unicodedata
import hashlib
import os
import six


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def home(request):
    """
    Displays a list of messages to be translated
    """

    def fix_nls(in_, out_):
        """Fixes submitted translations by filtering carriage returns and pairing
        newlines at the begging and end of the translated string with the original
        """
        if 0 == len(in_) or 0 == len(out_):
            return out_

        if "\r" in out_ and "\r" not in in_:
            out_ = out_.replace("\r", '')

        if "\n" == in_[0] and "\n" != out_[0]:
            out_ = "\n" + out_
        elif "\n" != in_[0] and "\n" == out_[0]:
            out_ = out_.lstrip()
        if 0 == len(out_):
            pass
        elif "\n" == in_[-1] and "\n" != out_[-1]:
            out_ = out_ + "\n"
        elif "\n" != in_[-1] and "\n" == out_[-1]:
            out_ = out_.rstrip()
        return out_

    def _request_request(key, default=None):
        if key in request.GET:
            return request.GET.get(key)
        elif key in request.POST:
            return request.POST.get(key)
        return default

    storage = get_storage(request)
    query = ''
    if storage.has('rosetta_i18n_fn'):
        rosetta_i18n_fn = storage.get('rosetta_i18n_fn')

        rosetta_i18n_app = get_app_name(rosetta_i18n_fn)
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')
        rosetta_i18n_lang_bidi = rosetta_i18n_lang_code.split('-')[0] in settings.LANGUAGES_BIDI
        rosetta_i18n_write = storage.get('rosetta_i18n_write', True)
        if rosetta_i18n_write:
            rosetta_i18n_pofile = pofile(rosetta_i18n_fn, wrapwidth=rosetta_settings.POFILE_WRAP_WIDTH)
            for entry in rosetta_i18n_pofile:
                entry.md5hash = hashlib.md5(
                    (six.text_type(entry.msgid) +
                        six.text_type(entry.msgstr) +
                        six.text_type(entry.msgctxt or "")).encode('utf8')
                ).hexdigest()

        else:
            rosetta_i18n_pofile = storage.get('rosetta_i18n_pofile')

        if 'filter' in request.GET:
            if request.GET.get('filter') in ('untranslated', 'translated', 'fuzzy', 'all'):
                filter_ = request.GET.get('filter')
                storage.set('rosetta_i18n_filter', filter_)
                return HttpResponseRedirect(reverse('rosetta-home'))

        rosetta_i18n_filter = storage.get('rosetta_i18n_filter', 'all')

        if '_next' in request.POST:
            rx = re.compile(r'^m_([0-9a-f]+)')
            rx_plural = re.compile(r'^m_([0-9a-f]+)_([0-9]+)')
            file_change = False
            for key, value in request.POST.items():
                md5hash = None
                plural_id = None

                if rx_plural.match(key):
                    md5hash = str(rx_plural.match(key).groups()[0])
                    # polib parses .po files into unicode strings, but
                    # doesn't bother to convert plural indexes to int,
                    # so we need unicode here.
                    plural_id = six.text_type(rx_plural.match(key).groups()[1])

                    # Above no longer true as of Polib 1.0.4
                    if plural_id and plural_id.isdigit():
                        plural_id = int(plural_id)

                elif rx.match(key):
                    md5hash = str(rx.match(key).groups()[0])

                if md5hash is not None:
                    entry = rosetta_i18n_pofile.find(md5hash, 'md5hash')
                    # If someone did a makemessage, some entries might
                    # have been removed, so we need to check.
                    if entry:
                        old_msgstr = entry.msgstr
                        if plural_id is not None:
                            plural_string = fix_nls(entry.msgid_plural, value)
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
                                               old_msgstr=old_msgstr,
                                               old_fuzzy=old_fuzzy,
                                               pofile=rosetta_i18n_fn,
                                               language_code=rosetta_i18n_lang_code,
                                               )

                    else:
                        storage.set('rosetta_last_save_error', True)

            if file_change and rosetta_i18n_write:
                try:
                    rosetta_i18n_pofile.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" % (
                        getattr(request.user, 'first_name', 'Anonymous'),
                        getattr(request.user, 'last_name', 'User'),
                        getattr(request.user, 'email', 'anonymous@user.tld')
                    )).encode('ascii', 'ignore')
                    rosetta_i18n_pofile.metadata['X-Translated-Using'] = u"django-rosetta %s" % rosetta.get_version(False)
                    rosetta_i18n_pofile.metadata['PO-Revision-Date'] = timestamp_with_timezone()
                except UnicodeDecodeError:
                    pass

                try:
                    rosetta_i18n_pofile.save()
                    po_filepath, ext = os.path.splitext(rosetta_i18n_fn)

                    if rosetta_settings.AUTO_COMPILE:
                        save_as_mo_filepath = po_filepath + '.mo'
                        rosetta_i18n_pofile.save_as_mofile(save_as_mo_filepath)

                    post_save.send(sender=None, language_code=rosetta_i18n_lang_code, request=request)
                    # Try auto-reloading via the WSGI daemon mode reload mechanism
                    if rosetta_settings.WSGI_AUTO_RELOAD and \
                        'mod_wsgi.process_group' in request.environ and \
                        request.environ.get('mod_wsgi.process_group', None) and \
                        'SCRIPT_FILENAME' in request.environ and \
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

                except Exception as e:
                    messages.error(request, e)
                    storage.set('rosetta_i18n_write', False)
                storage.set('rosetta_i18n_pofile', rosetta_i18n_pofile)

                # Retain query arguments
                query_arg = '?_next=1'
                if _request_request('query', False):
                    query_arg += '&query=%s' % _request_request('query')
                if 'page' in request.GET:
                    query_arg += '&page=%d&_next=1' % int(request.GET.get('page'))
                return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')

        if _request_request('query', False) and _request_request('query', '').strip():
            query = _request_request('query', '').strip()
            rx = re.compile(re.escape(query), re.IGNORECASE)
            paginator = Paginator([e_ for e_ in rosetta_i18n_pofile if not e_.obsolete and rx.search(six.text_type(e_.msgstr) + six.text_type(e_.msgid) + six.text_type(e_.comment) + u''.join([o[0] for o in e_.occurrences]))], rosetta_settings.MESSAGES_PER_PAGE)
        else:
            if rosetta_i18n_filter == 'untranslated':
                paginator = Paginator(rosetta_i18n_pofile.untranslated_entries(), rosetta_settings.MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'translated':
                paginator = Paginator(rosetta_i18n_pofile.translated_entries(), rosetta_settings.MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'fuzzy':
                paginator = Paginator([e_ for e_ in rosetta_i18n_pofile.fuzzy_entries() if not e_.obsolete], rosetta_settings.MESSAGES_PER_PAGE)
            else:
                paginator = Paginator([e_ for e_ in rosetta_i18n_pofile if not e_.obsolete], rosetta_settings.MESSAGES_PER_PAGE)

        if rosetta_settings.ENABLE_REFLANG:
            ref_lang = storage.get('rosetta_i18n_ref_lang_code', 'msgid')
            ref_pofile = None
            if ref_lang != 'msgid':
                ref_fn = re.sub('/locale/[a-z]{2}/', '/locale/%s/' % ref_lang, rosetta_i18n_fn)
                try:
                    ref_pofile = pofile(ref_fn)
                except IOError:
                    # there's a syntax error in the PO file and polib can't open it. Let's just
                    # do nothing and thus display msgids.
                    pass

            for o in paginator.object_list:
                # default
                o.ref_txt = o.msgid
                if ref_pofile is not None:
                    ref_entry = ref_pofile.find(o.msgid)
                    if ref_entry is not None and ref_entry.msgstr:
                        o.ref_txt = ref_entry.msgstr
            LANGUAGES = list(settings.LANGUAGES) + [('msgid', 'MSGID')]
        else:
            ref_lang = None
            LANGUAGES = settings.LANGUAGES

        page = 1
        if 'page' in request.GET:
            try:
                get_page = int(request.GET.get('page'))
            except ValueError:
                page = 1  # fall back to page 1
            else:
                if 0 < get_page <= paginator.num_pages:
                    page = get_page

        if '_next' in request.GET or '_next' in request.POST:
            page += 1
            if page > paginator.num_pages:
                page = 1
            query_arg = '?page=%d' % page
            return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))

        rosetta_messages = paginator.page(page).object_list
        main_language = None
        if rosetta_settings.MAIN_LANGUAGE and rosetta_settings.MAIN_LANGUAGE != rosetta_i18n_lang_code:
            for language in settings.LANGUAGES:
                if language[0] == rosetta_settings.MAIN_LANGUAGE:
                    main_language = _(language[1])
                    break

            fl = ("/%s/" % rosetta_settings.MAIN_LANGUAGE).join(rosetta_i18n_fn.split("/%s/" % rosetta_i18n_lang_code))
            po = pofile(fl)

            for message in rosetta_messages:
                message.main_lang = po.find(message.msgid).msgstr

        needs_pagination = paginator.num_pages > 1
        if needs_pagination:
            if paginator.num_pages >= 10:
                page_range = pagination_range(1, paginator.num_pages, page)
            else:
                page_range = range(1, 1 + paginator.num_pages)
        try:
            ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
            ADMIN_IMAGE_DIR = ADMIN_MEDIA_PREFIX + 'img/admin/'
        except AttributeError:
            ADMIN_MEDIA_PREFIX = settings.STATIC_URL + 'admin/'
            ADMIN_IMAGE_DIR = ADMIN_MEDIA_PREFIX + 'img/'

        if storage.has('rosetta_last_save_error'):
            storage.delete('rosetta_last_save_error')
            rosetta_last_save_error = True
        else:
            rosetta_last_save_error = False

        try:
            rosetta_i18n_lang_name = force_text(_(storage.get('rosetta_i18n_lang_name')))
        except:
            rosetta_i18n_lang_name = force_text(storage.get('rosetta_i18n_lang_name'))

        return render(request, 'rosetta/pofile.html', dict(
            version=rosetta.get_version(True),
            ADMIN_MEDIA_PREFIX=ADMIN_MEDIA_PREFIX,
            ADMIN_IMAGE_DIR=ADMIN_IMAGE_DIR,
            ENABLE_REFLANG=rosetta_settings.ENABLE_REFLANG,
            LANGUAGES=LANGUAGES,
            rosetta_settings=rosetta_settings,
            rosetta_i18n_lang_name=rosetta_i18n_lang_name,
            rosetta_i18n_lang_code=rosetta_i18n_lang_code,
            rosetta_i18n_lang_bidi=rosetta_i18n_lang_bidi,
            rosetta_last_save_error=rosetta_last_save_error,
            rosetta_i18n_filter=rosetta_i18n_filter,
            rosetta_i18n_write=rosetta_i18n_write,
            rosetta_messages=rosetta_messages,
            page_range=needs_pagination and page_range,
            needs_pagination=needs_pagination,
            main_language=main_language,
            rosetta_i18n_app=rosetta_i18n_app,
            page=page,
            query=query,
            paginator=paginator,
            rosetta_i18n_pofile=rosetta_i18n_pofile,
            ref_lang=ref_lang,
        ))
    else:
        return list_languages(request, do_session_warn=True)


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def download_file(request):
    import zipfile
    storage = get_storage(request)
    # original filename
    rosetta_i18n_fn = storage.get('rosetta_i18n_fn', None)
    # in-session modified catalog
    rosetta_i18n_pofile = storage.get('rosetta_i18n_pofile', None)
    # language code
    rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code', None)

    if not rosetta_i18n_lang_code or not rosetta_i18n_pofile or not rosetta_i18n_fn:
        return HttpResponseRedirect(reverse('rosetta-home'))
    try:
        if len(rosetta_i18n_fn.split('/')) >= 5:
            offered_fn = '_'.join(rosetta_i18n_fn.split('/')[-5:])
        else:
            offered_fn = rosetta_i18n_fn.split('/')[-1]
        po_fn = str(rosetta_i18n_fn.split('/')[-1])
        mo_fn = str(po_fn.replace('.po', '.mo'))  # not so smart, huh
        zipdata = six.BytesIO()
        zipf = zipfile.ZipFile(zipdata, mode="w")
        zipf.writestr(po_fn, six.text_type(rosetta_i18n_pofile).encode("utf8"))
        zipf.writestr(mo_fn, rosetta_i18n_pofile.to_binary())
        zipf.close()
        zipdata.seek(0)

        response = HttpResponse(zipdata.read())
        response['Content-Disposition'] = 'attachment; filename=%s.%s.zip' % (offered_fn, rosetta_i18n_lang_code)
        response['Content-Type'] = 'application/x-zip'
        return response

    except Exception:
        return HttpResponseRedirect(reverse('rosetta-home'))


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def list_languages(request, do_session_warn=False):
    """
    Lists the languages for the current project, the gettext catalog files
    that can be translated and their translation progress
    """
    storage = get_storage(request)
    languages = []

    if 'filter' in request.GET:
        if request.GET.get('filter') in ('project', 'third-party', 'django', 'all'):
            filter_ = request.GET.get('filter')
            storage.set('rosetta_i18n_catalog_filter', filter_)
            return HttpResponseRedirect(reverse('rosetta-pick-file'))

    rosetta_i18n_catalog_filter = storage.get('rosetta_i18n_catalog_filter', 'project')

    third_party_apps = rosetta_i18n_catalog_filter in ('all', 'third-party')
    django_apps = rosetta_i18n_catalog_filter in ('all', 'django')
    project_apps = rosetta_i18n_catalog_filter in ('all', 'project')

    has_pos = False
    for language in settings.LANGUAGES:
        if not can_translate_language(request.user, language[0]):
            continue

        pos = find_pos(language[0], project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps)
        has_pos = has_pos or len(pos)
        languages.append(
            (
                language[0],
                _(language[1]),
                sorted([(get_app_name(l), os.path.realpath(l), pofile(l)) for l in pos], key=lambda app: app[0]),
            )
        )
    try:
        ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    except AttributeError:
        ADMIN_MEDIA_PREFIX = settings.STATIC_URL + 'admin/'
    do_session_warn = do_session_warn and 'SessionRosettaStorage' in rosetta_settings.STORAGE_CLASS and 'signed_cookies' in settings.SESSION_ENGINE

    return render(request, 'rosetta/languages.html', dict(
        version=rosetta.get_version(True),
        ADMIN_MEDIA_PREFIX=ADMIN_MEDIA_PREFIX,
        do_session_warn=do_session_warn,
        languages=languages,
        has_pos=has_pos,
        rosetta_i18n_catalog_filter=rosetta_i18n_catalog_filter
    ))


def get_app_name(path):
    app = path.split("/locale")[0].split("/")[-1]
    return app


@never_cache
@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def lang_sel(request, langid, idx):
    """
    Selects a file to be translated
    """
    storage = get_storage(request)
    if langid not in [l[0] for l in settings.LANGUAGES] or not can_translate_language(request.user, langid):
        raise Http404
    else:

        rosetta_i18n_catalog_filter = storage.get('rosetta_i18n_catalog_filter', 'project')

        third_party_apps = rosetta_i18n_catalog_filter in ('all', 'third-party')
        django_apps = rosetta_i18n_catalog_filter in ('all', 'django')
        project_apps = rosetta_i18n_catalog_filter in ('all', 'project')
        file_ = sorted(find_pos(langid, project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps), key=get_app_name)[int(idx)]

        storage.set('rosetta_i18n_lang_code', langid)
        storage.set('rosetta_i18n_lang_name', six.text_type([l[1] for l in settings.LANGUAGES if l[0] == langid][0]))
        storage.set('rosetta_i18n_fn', file_)
        po = pofile(file_)
        for entry in po:
            entry.md5hash = hashlib.new(
                'md5',
                (six.text_type(entry.msgid) +
                    six.text_type(entry.msgstr) +
                    six.text_type(entry.msgctxt or "")).encode('utf8')
            ).hexdigest()

        storage.set('rosetta_i18n_pofile', po)
        try:
            os.utime(file_, None)
            storage.set('rosetta_i18n_write', True)
        except OSError:
            storage.set('rosetta_i18n_write', False)

        return HttpResponseRedirect(reverse('rosetta-home'))


def ref_sel(request, langid):
    storage = get_storage(request)
    ALLOWED_LANGUAGES = [l[0] for l in settings.LANGUAGES] + ['msgid']

    if langid not in ALLOWED_LANGUAGES:
        raise Http404

    storage.set('rosetta_i18n_ref_lang_code', langid)

    return HttpResponseRedirect(reverse('rosetta-home'))
ref_sel = never_cache(ref_sel)
ref_sel = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(ref_sel)


@user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)
def translate_text(request):
    language_from = request.GET.get('from', None)
    language_to = request.GET.get('to', None)
    text = request.GET.get('text', None)

    if language_from == language_to:
        data = {'success': True, 'translation': text}
    else:
        # run the translation:

        AZURE_CLIENT_ID = getattr(settings, 'AZURE_CLIENT_ID', None)
        AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)

        translator = Translator(AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)

        try:
            translated_text = translator.translate(text, language_to, language_from)
            data = {'success': True, 'translation': translated_text}
        except TranslateApiException as e:
            data = {'success': False, 'error': "Translation API Exception: {0}".format(e.message)}

    return HttpResponse(json.dumps(data), content_type='application/json')
