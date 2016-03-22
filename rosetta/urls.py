from django.conf.urls import url
from .views import (home, list_languages, download_file, lang_sel, translate_text, ref_sel)

urlpatterns = [
    url(r'^$', home, name='rosetta-home'),
    url(r'^pick/$', list_languages, name='rosetta-pick-file'),
    url(r'^download/$', download_file, name='rosetta-download-file'),
    url(r'^select/(?P<langid>[\w\-_\.]+)/(?P<idx>\d+)/$', lang_sel, name='rosetta-language-selection'),
    url(r'^select-ref/(?P<langid>[\w\-_\.]+)/$', ref_sel, name='rosetta-reference-selection'),
    url(r'^translate/$', translate_text, name='translate_text'),
]
