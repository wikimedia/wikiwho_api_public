from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

from base.models import BaseModel


class FailedArticle(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia page id')
    title = models.CharField(max_length=256, blank=False)
    count = models.PositiveIntegerField(default=0)
    revisions = ArrayField(models.IntegerField(), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    language = models.CharField(max_length=8, default='', choices=(('', '-------'), ) + tuple(settings.LANGUAGES))

    class Meta:
        abstract = True

    def __str__(self):
        return '{} - {}'.format(self.id, self.title)


class LongFailedArticle(FailedArticle):
    pass


class RecursionErrorArticle(FailedArticle):
    pass
