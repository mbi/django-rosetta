from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('rosetta.views',
    url(r'^$', 'home', name='rosetta-home'),
    url(r'^pick/$', 'list_languages', name='rosetta-pick-file'),
    url(r'^download/$', 'download_file', name='rosetta-download-file'),
    url(r'^restart/$', 'restart_server', name='rosetta-restart-server'),
    url(r'^update/catalogue/$', 'update_catalogue', name='rosetta-update-catalogue'),
    url(r'^update/current/catalogue/$', 'update_current_catalogue', name='rosetta-current-update-catalogue'),
    url(r'^update/confirmation/$', 'update_confirmation', name='rosetta-confirmation-file'),
    url(r'^change/catalogue/$', 'change_catalogue', name='rosetta-change-catalogue'),
    url(r'^select/(?P<langid>[\w\-]+)/(?P<idx>\d+)/$', 'lang_sel', name='rosetta-language-selection'),
    url(r'^ajax/update/translation/$', 'ajax_update_translation', name='rosetta-ajax-update-translation'),
)
