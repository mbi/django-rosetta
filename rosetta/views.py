from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.contrib.admin.util import unquote
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.encoding import smart_unicode, iri_to_uri
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from rosetta.conf import settings as rosetta_settings
from rosetta.forms import UpdatePoForm
from rosetta.polib import pofile
from rosetta.poutil import (find_pos, pagination_range, get_app_name,
                            get_differences, priority_merge, validate_format,
                            search_msg_id_in_other_pos)
from rosetta.signals import entry_changed, post_save
from rosetta.storage import get_storage
import re
import rosetta
import subprocess
import datetime
import unicodedata
import hashlib
import os


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
        if "\n" == in_[-1] and "\n" != out_[-1]:
            out_ = out_ + "\n"
        elif "\n" != in_[-1] and "\n" == out_[-1]:
            out_ = out_.rstrip()
        return out_

    storage = get_storage(request)
    version = rosetta.get_version(True)
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
                    entry.msgid.encode("utf8") +
                    entry.msgstr.encode("utf8") +
                    (entry.msgctxt and entry.msgctxt.encode("utf8") or "") 
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
                    plural_id = unicode(rx_plural.match(key).groups()[1])

                elif rx.match(key):
                    md5hash = str(rx.match(key).groups()[0])

                if md5hash is not None:
                    entry = rosetta_i18n_pofile.find(md5hash, 'md5hash')
                    # If someone did a makemessage, some entries might
                    # have been removed, so we need to check.
                    if entry:
                        old_msgstr = entry.msgstr
                        if plural_id is not None:
                            #plural_string = fix_nls(entry.msgstr_plural[plural_id], value)
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
                    # Provide defaults in case authorization is not required.
                    request.user.first_name = getattr(request.user, 'first_name', 'Anonymous')
                    request.user.last_name = getattr(request.user, 'last_name', 'User')
                    request.user.email = getattr(request.user, 'email', 'anonymous@user.tld')

                    rosetta_i18n_pofile.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" % (request.user.first_name, request.user.last_name, request.user.email)).encode('ascii', 'ignore')
                    rosetta_i18n_pofile.metadata['X-Translated-Using'] = u"django-rosetta %s" % rosetta.get_version(False)
                    rosetta_i18n_pofile.metadata['PO-Revision-Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M%z')
                except UnicodeDecodeError:
                    pass

                try:
                    rosetta_i18n_pofile.save()
                    po_filepath, ext = os.path.splitext(rosetta_i18n_fn)
                    save_as_mo_filepath = po_filepath + '.mo'
                    rosetta_i18n_pofile.save_as_mofile(save_as_mo_filepath)

                    post_save.send(sender=None, language_code=rosetta_i18n_lang_code, request=request)
                    # Try auto-reloading via the WSGI daemon mode reload mechanism
                    if  rosetta_settings.WSGI_AUTO_RELOAD and \
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

                except:
                    storage.set('rosetta_i18n_write', False)
                storage.set('rosetta_i18n_pofile', rosetta_i18n_pofile)

                # Retain query arguments
                query_arg = '?_next=1'
                if 'query' in request.GET or 'query' in request.POST:
                    query_arg += '&query=%s' % request.REQUEST.get('query')
                if 'page' in request.GET:
                    query_arg += '&page=%d&_next=1' % int(request.GET.get('page'))
                return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))
        rosetta_i18n_lang_name = _(storage.get('rosetta_i18n_lang_name'))
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')

        if 'query' in request.REQUEST and request.REQUEST.get('query', '').strip():
            query = request.REQUEST.get('query').strip()
            rx = re.compile(re.escape(query), re.IGNORECASE)
            paginator = Paginator([e for e in rosetta_i18n_pofile if not e.obsolete and rx.search(smart_unicode(e.msgstr) + smart_unicode(e.msgid) + u''.join([o[0] for o in e.occurrences]))], rosetta_settings.MESSAGES_PER_PAGE)
        else:
            if rosetta_i18n_filter == 'untranslated':
                paginator = Paginator(rosetta_i18n_pofile.untranslated_entries(), rosetta_settings.MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'translated':
                paginator = Paginator(rosetta_i18n_pofile.translated_entries(), rosetta_settings.MESSAGES_PER_PAGE)
            elif rosetta_i18n_filter == 'fuzzy':
                paginator = Paginator([e for e in rosetta_i18n_pofile.fuzzy_entries() if not e.obsolete], rosetta_settings.MESSAGES_PER_PAGE)
            else:
                paginator = Paginator([e for e in rosetta_i18n_pofile if not e.obsolete], rosetta_settings.MESSAGES_PER_PAGE)

        if 'page' in request.GET and int(request.GET.get('page')) <= paginator.num_pages and int(request.GET.get('page')) > 0:
            page = int(request.GET.get('page'))
        else:
            page = 1

        if '_next' in request.GET or '_next' in request.POST:
            page += 1
            if page > paginator.num_pages:
                page = 1
            query_arg = '?page=%d' % page
            return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))

        rosetta_messages = paginator.page(page).object_list
        rosetta_messages = search_msg_id_in_other_pos(rosetta_messages, rosetta_i18n_lang_code, rosetta_i18n_pofile)
        if rosetta_settings.MAIN_LANGUAGE and rosetta_settings.MAIN_LANGUAGE != rosetta_i18n_lang_code:

            main_language = None
            for language in settings.LANGUAGES:
                if language[0] == rosetta_settings.MAIN_LANGUAGE:
                    main_language = _(language[1])
                    break

            fl = ("/%s/" % rosetta_settings.MAIN_LANGUAGE).join(rosetta_i18n_fn.split("/%s/" % rosetta_i18n_lang_code))
            po = pofile(fl)

            main_messages = []
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
        ENABLE_TRANSLATION_SUGGESTIONS = rosetta_settings.BING_APP_ID and rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS
        BING_APP_ID = rosetta_settings.BING_APP_ID
        MESSAGES_SOURCE_LANGUAGE_NAME = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_NAME
        MESSAGES_SOURCE_LANGUAGE_CODE = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE
        if storage.has('rosetta_last_save_error'):
            storage.delete('rosetta_last_save_error')
            rosetta_last_save_error = True
        rosetta_i18n_catalog_filter = storage.get('rosetta_i18n_catalog_filter', 'project')
        third_party_apps = rosetta_i18n_catalog_filter in ('all', 'third-party')
        django_apps = rosetta_i18n_catalog_filter in ('all', 'django')
        project_apps = rosetta_i18n_catalog_filter in ('all', 'project')
        languages_to_catalogue = []
        for language in settings.LANGUAGES:
            if rosetta_i18n_lang_code == language[0]:
                continue
            pos = find_pos(language[0], project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps)
            position = None
            for i in xrange(len(pos)):
                pos_split = pos[i].split(os.path.sep)
                try:
                    if pos_split[-5] == rosetta_i18n_app and rosetta_i18n_fn.split(os.path.sep)[-1] == pos_split[-1]:
                        position = i
                        break
                except IndexError:
                    pass
            if position is not None:
                languages_to_catalogue.append((language[0], _(language[1]), position))
        return render_to_response('rosetta/pofile.html', locals(), context_instance=RequestContext(request))
    else:
        return list_languages(request, do_session_warn=True)
home = never_cache(home)
home = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(home)


def download_file(request):
    import zipfile
    from StringIO import StringIO
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
        zipdata = StringIO()
        zipf = zipfile.ZipFile(zipdata, mode="w")
        zipf.writestr(po_fn, unicode(rosetta_i18n_pofile).encode("utf8"))
        zipf.writestr(mo_fn, rosetta_i18n_pofile.to_binary())
        zipf.close()
        zipdata.seek(0)

        response = HttpResponse(zipdata.read())
        response['Content-Disposition'] = 'attachment; filename=%s.%s.zip' % (offered_fn, rosetta_i18n_lang_code)
        response['Content-Type'] = 'application/x-zip'
        return response

    except Exception:
        return HttpResponseRedirect(reverse('rosetta-home'))
download_file = never_cache(download_file)
download_file = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(download_file)


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
        pos = find_pos(language[0], project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps)
        has_pos = has_pos or len(pos)
        languages.append(
            (language[0],
            _(language[1]),
            [(get_app_name(l), os.path.realpath(l), pofile(l)) for l in  pos],
            )
        )
    try:
        ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    except AttributeError:
        ADMIN_MEDIA_PREFIX = settings.STATIC_URL + 'admin/'

    version = rosetta.get_version(True)
    do_session_warn = do_session_warn and 'SessionRosettaStorage' in rosetta_settings.STORAGE_CLASS and 'signed_cookies' in settings.SESSION_ENGINE
    return render_to_response('rosetta/languages.html', locals(), context_instance=RequestContext(request))
list_languages = never_cache(list_languages)
list_languages = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(list_languages)


def restart_server(request):
    """
    Restart web server
    """
    if request.method == 'POST':
        do_restart(request)
        return HttpResponseRedirect(reverse('rosetta-home'))
    ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    return render_to_response('rosetta/confirm_restart.html', locals(), context_instance=RequestContext(request))

restart_server = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(restart_server)
restart_server = never_cache(restart_server)


def do_restart(request):
    """
    * "test" for a django instance (this do a touch over settings.py for reload)
    * "apache"
    * "httpd"
    * "wsgi"
    * "restart_script <script_path_name>"
    """
    if request.is_ajax():
        noresponse = True
    else:
        noresponse = False
    reload_method = getattr(settings, 'AUTO_RELOAD_METHOD', getattr(rosetta_settings, 'AUTO_RELOAD_METHOD', 'test'))
    if reload_method == 'test':
        script = 'touch settings.py'
    ## No RedHAT or similars
    elif reload_method == 'apache2':
        script = 'sudo apache2ctl restart'
    ## RedHAT, CentOS
    elif reload_method == 'httpd':
        script = 'sudo service httpd restart'
    elif reload_method.startswith('restart_script'):
        script = " ".join(reload_method.split(" ")[1:])
    subprocess.call(script.split(" "))
    if noresponse:
        return
    return HttpResponseRedirect(request.environ['HTTP_REFERER'])


def update_current_catalogue(request):
    storage = get_storage(request)
    po_file_path = storage.get('rosetta_i18n_fn', None)
    po_file = storage.get('rosetta_i18n_pofile', None) or pofile(po_file_path)
    if not po_file or not po_file_path:
        request.user.message_set.create(message=ugettext("There is not a current catalogue"))
        return HttpResponseRedirect(reverse('rosetta-pick-file'))
    return _update_catalogue(request, po_file, po_file_path)
update_current_catalogue = never_cache(update_current_catalogue)
update_current_catalogue = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(update_current_catalogue)


def update_catalogue(request):
    return _update_catalogue(request)
update_catalogue = never_cache(update_catalogue)
update_catalogue = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(update_catalogue)


def _update_catalogue(request, po_file=None, po_file_path=None):
    storage = get_storage(request)
    data = None
    files = None
    if request.method == 'POST':
        data = request.POST
        files = request.FILES
    form = UpdatePoForm(po_file=po_file, po_file_path=po_file_path, data=data, files=files)
    if form.is_valid():
        po_tmp, po_destination, priority = form.save_temporal_file()
        storage.set('rosetta_update_confirmation', {
            'path_source': po_tmp.fpath,
            'path_destination': po_destination.fpath,
            'priority': priority,
        })
        return HttpResponseRedirect(reverse('rosetta.views.update_confirmation'))
    if po_file:
        rosetta_i18n_lang_name = _(storage.get('rosetta_i18n_lang_name'))
        rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')
        rosetta_i18n_fn = storage.get('rosetta_i18n_fn')
        rosetta_i18n_app = get_app_name(rosetta_i18n_fn)
    ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    return render_to_response('rosetta/update_file.html',
                              locals(),
                              context_instance=RequestContext(request))


def update_confirmation(request):
    storage = get_storage(request)
    up_conf = storage.get('rosetta_update_confirmation')
    priority = up_conf['priority']
    path_source = up_conf['path_source']
    po_source = pofile(path_source)
    path_destination = up_conf['path_destination']
    po_destination = pofile(path_destination)

    if request.method == 'POST':
        priority = up_conf['priority']
        priority_merge(po_destination, po_source, priority=priority)
        redirect_to = reverse('rosetta.views.home')
        return HttpResponseRedirect(redirect_to)
    news_entries, changes_entries = get_differences(po_destination,
                                                    po_source, priority)
    storage = get_storage(request)
    rosetta_i18n_lang_name = _(storage.get('rosetta_i18n_lang_name'))
    rosetta_i18n_lang_code = storage.get('rosetta_i18n_lang_code')
    rosetta_i18n_fn = storage.get('rosetta_i18n_fn')
    rosetta_i18n_app = get_app_name(path_destination)
    ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    return render_to_response('rosetta/update_confirmation.html',
                              locals(),
                              context_instance=RequestContext(request))
update_confirmation = never_cache(update_confirmation)
update_confirmation = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(update_confirmation)


def lang_sel(request, langid, idx):
    """
    Selects a file to be translated
    """
    storage = get_storage(request)
    if langid not in [l[0] for l in settings.LANGUAGES]:
        raise Http404
    else:

        rosetta_i18n_catalog_filter = storage.get('rosetta_i18n_catalog_filter', 'project')

        third_party_apps = rosetta_i18n_catalog_filter in ('all', 'third-party')
        django_apps = rosetta_i18n_catalog_filter in ('all', 'django')
        project_apps = rosetta_i18n_catalog_filter in ('all', 'project')
        file_ = find_pos(langid, project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps)[int(idx)]

        storage.set('rosetta_i18n_lang_code', langid)
        storage.set('rosetta_i18n_lang_name', unicode([l[1] for l in settings.LANGUAGES if l[0] == langid][0]))
        storage.set('rosetta_i18n_fn',  file_)
        po = pofile(file_)
        for entry in po:
            entry.md5hash = hashlib.md5(
                entry.msgid.encode("utf8") +
                entry.msgstr.encode("utf8") +
                (entry.msgctxt and entry.msgctxt.encode("utf8") or "")
            ).hexdigest()
        storage.set('rosetta_i18n_pofile', po)
        try:
            os.utime(file_, None)
            storage.set('rosetta_i18n_write', True)
        except OSError:
            storage.set('rosetta_i18n_write', False)

        return HttpResponseRedirect(reverse('rosetta-home'))
lang_sel = never_cache(lang_sel)
lang_sel = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(lang_sel)


def change_catalogue(request):
    new_catalog = request.GET.get('catalog', None)
    if not new_catalog:
        return HttpResponseRedirect(reverse('rosetta-home'))
    reload_catalog_in_storage(request, file_path=unquote(new_catalog))
    entry_id = request.GET.get('entry_id', None)
    if entry_id:
        query_arg = '?query=%s' % entry_id
    else:
        query_arg = ''
    return HttpResponseRedirect(reverse('rosetta-home') + query_arg)
change_catalogue = never_cache(change_catalogue)
change_catalogue = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(change_catalogue)


def ajax_update_translation(request):

    storage = get_storage(request)
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
        if "\n" == in_[-1] and "\n" != out_[-1]:
            out_ = out_ + "\n"
        elif "\n" != in_[-1] and "\n" == out_[-1]:
            out_ = out_.rstrip()
        return out_
    catalog = request.GET.get('catalog', None)
    translation = request.GET.get('translation', None)
    if not translation:
        translation = {}
        for key, value in request.GET.items():
            if key.startswith('translation_'):
                translation[key.replace('translation_', '')] = value
    msgid = request.GET.get('msgid', None)
    try:
        po_file = pofile(catalog)
        entry = po_file.find(msgid)
    except:
        po_file = None
        entry = None
    if not catalog or not translation or not msgid\
       or not po_file or not entry:
        raise Http404

    saved = False
    if isinstance(translation, dict):
        for key, item in translation.items():
            entry.msgstr_plural[key] = fix_nls(entry.msgid_plural, item)
    else:
        entry.msgstr = fix_nls(entry.msgid, translation)
    if 'fuzzy' in entry.flags:
        entry.flags.remove('fuzzy')
    rosetta_i18n_write = storage.get('rosetta_i18n_write', True)
    format_errors = validate_format(po_file)
    if rosetta_i18n_write and not format_errors:
        try:
            po_file.metadata['Last-Translator'] = unicodedata.normalize('NFKD', u"%s %s <%s>" % (request.user.first_name,
                                                                                                 request.user.last_name,
                                                                                                 request.user.email)).encode('ascii', 'ignore')
            po_file.metadata['X-Translated-Using'] = str("django-rosetta %s" % rosetta.get_version(False))
            po_file.metadata['PO-Revision-Date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M%z')
        except UnicodeDecodeError:
            pass
        try:
            po_file.save()
            po_file.save_as_mofile(po_file.fpath.replace('.po', '.mo'))
            saved = True
        except:
            pass

    json_dict = simplejson.dumps({'saved': saved,
                                  'translation': translation})
    return HttpResponse(json_dict, mimetype='text/javascript')
ajax_update_translation = never_cache(ajax_update_translation)
ajax_update_translation = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(ajax_update_translation)


def ajax_restart(request):
    json_dict = simplejson.dumps({'restarting': True})
    do_restart(request)
    return HttpResponse(json_dict, mimetype='text/javascript')
ajax_restart = never_cache(ajax_restart)
ajax_restart = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(ajax_restart)


def ajax_is_wakeup(request):
    json_dict = simplejson.dumps({'wakeup': True})
    return HttpResponse(json_dict, mimetype='text/javascript')
ajax_is_wakeup = never_cache(ajax_is_wakeup)
ajax_is_wakeup = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(ajax_is_wakeup)


def reload_catalog_in_storage(request, file_path=None):
    """ Reload rosetta catalog in storage """
    storage = get_storage(request)
    if file_path is None:
        file_path = storage.get("rosetta_i18n_fn")
    po = pofile(file_path)
    for i in range(len(po)):
        po[i].id = i
    storage.set('rosetta_i18n_fn', file_path)
    storage.set('rosetta_i18n_pofile', po)
    storage.set('rosetta_i18n_mtime', os.stat(file_path)[-2])


def can_translate(user):
    if not getattr(settings, 'ROSETTA_REQUIRES_AUTH', True):
        return True
    if not user.is_authenticated():
        return False
    elif user.is_superuser and user.is_staff:
        return True
    else:
        try:
            from django.contrib.auth.models import Group
            translators = Group.objects.get(name='translators')
            return translators in user.groups.all()
        except Group.DoesNotExist:
            return False
