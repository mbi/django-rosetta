from django.conf.urls import url
from django.views.generic.base import RedirectView
try:
    from django.urls import reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse_lazy

from . import views


urlpatterns = [

    url(r'^$',
        RedirectView.as_view(
            url=reverse_lazy('rosetta-file-list', kwargs={'po_filter': 'project'}),
            permanent=False
        ),
        name='rosetta-old-home-redirect',
        ),

    url(r'^files/$',
        RedirectView.as_view(
            url=reverse_lazy('rosetta-file-list', kwargs={'po_filter': 'project'}),
            permanent=False
        ),
        name='rosetta-file-list-redirect',
        ),

    url(r'^files/(?P<po_filter>[\w-]+)/$',
        views.TranslationFileListView.as_view(),
        name='rosetta-file-list',
        ),

    url(r'^files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.]+)/(?P<idx>\d+)/$',
        views.TranslationFormView.as_view(),
        name='rosetta-form',
        ),

    url(r'^files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.]+)/(?P<idx>\d+)/download/$',
        views.TranslationFileDownload.as_view(),
        name='rosetta-download-file',
        ),

    url(r'^translate/$',
        views.translate_text,
        name='rosetta.translate_text',
        ),
]
