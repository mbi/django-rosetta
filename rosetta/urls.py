from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('rosetta.views',
    url(r'^$', 'home', name='rosetta-home'),
    url(r'^pick/$', 'list_languages', name='rosetta-pick-file'),
    url(r'^download/$', 'download_file', name='rosetta-download-file'),
    url(r'^select/(?P<langid>[\w\-]+)/(?P<idx>\d+)/$', 'lang_sel', name='rosetta-language-selection'),
)
