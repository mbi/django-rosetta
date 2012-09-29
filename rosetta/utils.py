from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import smart_unicode, iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from rosetta.conf import settings as rosetta_settings
from rosetta.polib import pofile
from rosetta.poutil import find_pos, pagination_range
from rosetta.signals import entry_changed, post_save
from rosetta.storage import get_storage
import re
import rosetta
import datetime
import unicodedata
import hashlib
import os
from microsofttranslator import Translator, TranslateApiException

def translate_text(language_from, language_to, text):
    if language_from == language_to:
        data = { 'success' : True, 'translation' : text }
    else:
        # run the translation:
        AZURE_CLIENT_ID = getattr(settings, 'AZURE_CLIENT_ID', None)
        AZURE_CLIENT_SECRET = getattr(settings, 'AZURE_CLIENT_SECRET', None)

        translator = Translator(AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)

        try:
            translated_text = translator.translate(text, language_to)
            data = { 'success' : True, 'translation' : translated_text }
        except TranslateApiException as e:
            data = { 'success' : False, 'error' : "Translation API Exception: {0}".format(e.message) }

    return HttpResponse(simplejson.dumps(data), mimetype='application/json')
    