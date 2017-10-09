from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings

from base.models import BaseModel


class FailedArticle(BaseModel):
    page_id = models.IntegerField(blank=False, null=False, db_index=True)
    title = models.CharField(max_length=256, blank=False)
    count = models.PositiveIntegerField(default=0)
    revisions = ArrayField(models.IntegerField(), blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    language = models.CharField(max_length=8, default='', choices=(('', '-------'), ) + tuple(settings.LANGUAGES))

    class Meta:
        abstract = True

    def __str__(self):
        return '{} - {}'.format(self.page_id, self.title)


class LongFailedArticle(FailedArticle):
    pass


class RecursionErrorArticle(FailedArticle):
    pass
