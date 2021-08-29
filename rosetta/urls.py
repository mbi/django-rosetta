from django.urls import re_path, reverse_lazy
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    re_path(
        r'^$',
        RedirectView.as_view(
            url=reverse_lazy('rosetta-file-list', kwargs={'po_filter': 'project'}),
            permanent=False,
        ),
        name='rosetta-old-home-redirect',
    ),
    re_path(
        r'^files/$',
        RedirectView.as_view(
            url=reverse_lazy('rosetta-file-list', kwargs={'po_filter': 'project'}),
            permanent=False,
        ),
        name='rosetta-file-list-redirect',
    ),
    re_path(
        r'^files/(?P<po_filter>[\w-]+)/$',
        views.TranslationFileListView.as_view(),
        name='rosetta-file-list',
    ),
    re_path(
        r'^files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.]+)/(?P<idx>\d+)/$',
        views.TranslationFormView.as_view(),
        name='rosetta-form',
    ),
    re_path(
        r'^files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.]+)/(?P<idx>\d+)/download/$',
        views.TranslationFileDownload.as_view(),
        name='rosetta-download-file',
    ),
    re_path(r'^translate/$', views.translate_text, name='rosetta.translate_text'),
]
