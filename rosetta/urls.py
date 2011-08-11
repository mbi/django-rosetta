from django.conf.urls.defaults import *

urlpatterns = patterns('rosetta.views',
    url(r'^$',                                       'list_languages', name='rosetta-home'),
    url(r'^translate/(?P<appname>[\w_]+)/(?P<lang>[\w\-]+)/(?P<filter>(untranslated|translated|fuzzy|all))/(?P<page>\d+)$',
                                                     'translate',      name='rosetta-translate'),
    url(r'^download/(?P<appname>[\w_]+)/(?P<lang>[\w\-]+)$',
                                                     'download_file',  name='rosetta-download-file'),
)
