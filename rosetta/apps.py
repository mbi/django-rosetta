from django.apps import AppConfig
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from rosetta.conf import settings as rosetta_settings


class RosettaAppConfig(AppConfig):
    name = 'rosetta'

    def ready(self):
        from django.contrib import admin
        from django.contrib.admin import sites

        class RosettaAdminSite(admin.AdminSite):
            @never_cache
            def index(self, request, extra_context=None):
                resp = super(RosettaAdminSite, self).index(request,
                                                           extra_context)
                app_dict = {
                    'app_url': reverse('rosetta-home'),
                    'models': [
                        {
                            'admin_url': reverse('rosetta-home'),
                            'name': _('Browse'),
                            'add_url': None
                        },
                    ],
                    'has_module_perms': True,
                    'name': _('Transplations'),
                    'app_label': 'rosetta'
                }
                resp.context_data['app_list'].append(app_dict)
                return resp

        if rosetta_settings.SHOW_AT_ADMIN_PANEL:
            rosetta = RosettaAdminSite()
            admin.site = rosetta
            sites.site = rosetta
