from django.conf.urls import include, url
from .views import dummy

urlpatterns = [
    url(r'^rosetta/', include('rosetta.urls')),
    url(r'^admin/$', dummy, name='dummy-login')
]
