from django.conf.urls import include, re_path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


admin.autodiscover()

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^rosetta/', include('rosetta.urls')),
]

urlpatterns += staticfiles_urlpatterns()
