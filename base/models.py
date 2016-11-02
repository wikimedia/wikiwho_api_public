from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse


class TimestampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    null=True, blank=True)

    class Meta:
        abstract = True


class BaseModel(models.Model):

    class Meta:
        abstract = True

    def get_admin_url(self):
        return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name), args=(self.pk,))

    @classmethod
    def get_admin_list_url(cls):
        return reverse("admin:%s_%s_changelist" % (cls._meta.app_label, cls._meta.model_name))


class BaseTimestampedModel(TimestampedModel, BaseModel):

    class Meta:
        abstract = True
