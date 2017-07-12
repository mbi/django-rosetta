from django.db import models
from django.utils.translation import ugettext_lazy as _


# Create your models here.

class RosettaSettings(models.Model):
    readonly = models.BooleanField(_('readonly'), default=False)

    def set_readonly(self, value):
        self.readonly = value
        self.save()

    @staticmethod
    def instance():
        if RosettaSettings.objects.count() == 0:
            RosettaSettings.objects.create().save()
        return RosettaSettings.objects.first()
