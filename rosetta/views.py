from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_unicode, iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from rosetta.conf import settings as rosetta_settings
from rosetta.polib import pofile
from rosetta.poutil import find_pos, pagination_range
from rosetta.signals import entry_changed, post_save
import re
import rosetta
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

    version = rosetta.get_version(True)
    if 'rosetta_i18n_fn' in request.session:
        rosetta_i18n_fn = request.session.get('rosetta_i18n_fn')
        rosetta_i18n_app = get_app_name(rosetta_i18n_fn)
        rosetta_i18n_lang_code = request.session['rosetta_i18n_lang_code']
        rosetta_i18n_lang_bidi = rosetta_i18n_lang_code.split('-')[0] in settings.LANGUAGES_BIDI
        rosetta_i18n_write = request.session.get('rosetta_i18n_write', True)
        if rosetta_i18n_write:
            rosetta_i18n_pofile = pofile(rosetta_i18n_fn, wrapwidth=rosetta_settings.POFILE_WRAP_WIDTH)
            for entry in rosetta_i18n_pofile:
                entry.md5hash = hashlib.md5(entry.msgid.encode("utf8") + entry.msgstr.encode("utf8")).hexdigest()

        else:
            rosetta_i18n_pofile = request.session.get('rosetta_i18n_pofile')

        if 'filter' in request.GET:
            if request.GET.get('filter') in ('untranslated', 'translated', 'fuzzy', 'all'):
                filter_ = request.GET.get('filter')
                request.session['rosetta_i18n_filter'] = filter_
                return HttpResponseRedirect(reverse('rosetta-home'))

        rosetta_i18n_filter = request.session.get('rosetta_i18n_filter', 'all')

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
                                               old_msgstr=old_msgstr,
                                               old_fuzzy=old_fuzzy,
                                               pofile=rosetta_i18n_fn,
                                               language_code=rosetta_i18n_lang_code,
                                               )

                    else:
                        request.session['rosetta_last_save_error'] = True

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
                    rosetta_i18n_pofile.save_as_mofile(rosetta_i18n_fn.replace('.po', '.mo'))

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
                    request.session['rosetta_i18n_write'] = False

                request.session['rosetta_i18n_pofile'] = rosetta_i18n_pofile

                # Retain query arguments
                query_arg = ''
                if 'query' in request.REQUEST:
                    query_arg = '?query=%s' % request.REQUEST.get('query')
                if 'page' in request.GET:
                    if query_arg:
                        query_arg = query_arg + '&'
                    else:
                        query_arg = '?'
                    query_arg = query_arg + 'page=%d' % int(request.GET.get('page'))
                return HttpResponseRedirect(reverse('rosetta-home') + iri_to_uri(query_arg))
        rosetta_i18n_lang_name = _(request.session.get('rosetta_i18n_lang_name'))
        rosetta_i18n_lang_code = request.session.get('rosetta_i18n_lang_code')

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
        rosetta_messages = paginator.page(page).object_list
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
        ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
        ENABLE_TRANSLATION_SUGGESTIONS = rosetta_settings.BING_APP_ID and rosetta_settings.ENABLE_TRANSLATION_SUGGESTIONS
        BING_APP_ID = rosetta_settings.BING_APP_ID
        MESSAGES_SOURCE_LANGUAGE_NAME = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_NAME
        MESSAGES_SOURCE_LANGUAGE_CODE = rosetta_settings.MESSAGES_SOURCE_LANGUAGE_CODE
        if 'rosetta_last_save_error' in request.session:
            del(request.session['rosetta_last_save_error'])
            rosetta_last_save_error = True

        return render_to_response('rosetta/pofile.html', locals(), context_instance=RequestContext(request))
    else:
        return list_languages(request)
home = never_cache(home)
home = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(home)


def download_file(request):
    import zipfile
    from StringIO import StringIO
    # original filename
    rosetta_i18n_fn = request.session.get('rosetta_i18n_fn', None)
    # in-session modified catalog
    rosetta_i18n_pofile = request.session.get('rosetta_i18n_pofile', None)
    # language code
    rosetta_i18n_lang_code = request.session.get('rosetta_i18n_lang_code', None)

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


def list_languages(request):
    """
    Lists the languages for the current project, the gettext catalog files
    that can be translated and their translation progress
    """
    languages = []

    if 'filter' in request.GET:
        if request.GET.get('filter') in ('project', 'third-party', 'django', 'all'):
            filter_ = request.GET.get('filter')
            request.session['rosetta_i18n_catalog_filter'] = filter_
            return HttpResponseRedirect(reverse('rosetta-pick-file'))

    rosetta_i18n_catalog_filter = request.session.get('rosetta_i18n_catalog_filter', 'project')

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
    ADMIN_MEDIA_PREFIX = settings.ADMIN_MEDIA_PREFIX
    version = rosetta.get_version(True)
    return render_to_response('rosetta/languages.html', locals(), context_instance=RequestContext(request))
list_languages = never_cache(list_languages)
list_languages = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(list_languages)


def get_app_name(path):
    app = path.split("/locale")[0].split("/")[-1]
    return app


def lang_sel(request, langid, idx):
    """
    Selects a file to be translated
    """
    if langid not in [l[0] for l in settings.LANGUAGES]:
        raise Http404
    else:

        rosetta_i18n_catalog_filter = request.session.get('rosetta_i18n_catalog_filter', 'project')

        third_party_apps = rosetta_i18n_catalog_filter in ('all', 'third-party')
        django_apps = rosetta_i18n_catalog_filter in ('all', 'django')
        project_apps = rosetta_i18n_catalog_filter in ('all', 'project')
        file_ = find_pos(langid, project_apps=project_apps, django_apps=django_apps, third_party_apps=third_party_apps)[int(idx)]

        request.session['rosetta_i18n_lang_code'] = langid
        request.session['rosetta_i18n_lang_name'] = unicode([l[1] for l in settings.LANGUAGES if l[0] == langid][0])
        request.session['rosetta_i18n_fn'] = file_
        po = pofile(file_)
        for entry in po:
            entry.md5hash = hashlib.md5(entry.msgid.encode("utf8") + entry.msgstr.encode("utf8")).hexdigest()

        request.session['rosetta_i18n_pofile'] = po
        try:
            os.utime(file_, None)
            request.session['rosetta_i18n_write'] = True
        except OSError:
            request.session['rosetta_i18n_write'] = False

        return HttpResponseRedirect(reverse('rosetta-home'))
lang_sel = never_cache(lang_sel)
lang_sel = user_passes_test(lambda user: can_translate(user), settings.LOGIN_URL)(lang_sel)


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

