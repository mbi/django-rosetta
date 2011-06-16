from django.conf.urls.defaults import *
urlpatterns = patterns('',
    url(r'^rosetta/',include('rosetta.urls')),
    url(r'^admin/$','rosetta.tests.views.dummy', name='dummy-login')
)
