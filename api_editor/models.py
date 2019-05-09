from django.db import models

from base.models import BaseModel

import architect


class EditorData(BaseModel):
    # Use editor id and name separately because indexing on int is faster
    editor_name = models.CharField(
        max_length=85, default='')  # max_length='0|' + 85
    adds = models.IntegerField(blank=False)
    adds_surv_48h = models.IntegerField(blank=False)
    adds_persistent = models.IntegerField(blank=False)
    adds_stopword_count = models.IntegerField(blank=False, default=0)

    dels = models.IntegerField(blank=False)
    dels_surv_48h = models.IntegerField(blank=False)
    dels_persistent = models.IntegerField(blank=False)
    dels_stopword_count = models.IntegerField(blank=False, default=0)

    reins = models.IntegerField(blank=False)
    reins_surv_48h = models.IntegerField(blank=False)
    reins_persistent = models.IntegerField(blank=False)
    reins_stopword_count = models.IntegerField(blank=False, default=0)

    elegibles = models.IntegerField(blank=False, default=0)
    undos = models.IntegerField(blank=False, default=0)
    conflict = models.FloatField(blank=False, default=0)

    @property
    def language(self):
        return self.__class__.__name__.lower().split('editordata')[-1]

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class EditorDataNotIndexed(EditorData):
    page_id = models.IntegerField(blank=False, null=False)
    editor_id = models.IntegerField(blank=False, null=False)
    year_month = models.DateField(blank=False, null=False)

    class Meta:
        abstract = True


class EditorDataEnNotIndexed(EditorDataNotIndexed):
    pass


@architect.install('partition', type='range', subtype='date', constraint='year', column='year_month')
class EditorDataEn(EditorDataNotIndexed):
    pass


class EditorDataEuNotIndexed(EditorDataNotIndexed):
    pass


@architect.install('partition', type='range', subtype='date', constraint='year', column='year_month')
class EditorDataEu(EditorDataNotIndexed):
    pass


class EditorDataDeNotIndexed(EditorDataNotIndexed):
    pass


@architect.install('partition', type='range', subtype='date', constraint='year', column='year_month')
class EditorDataDe(EditorDataNotIndexed):
    pass


class EditorDataEsNotIndexed(EditorDataNotIndexed):
    pass


@architect.install('partition', type='range', subtype='date', constraint='year', column='year_month')
class EditorDataEs(EditorDataNotIndexed):
    pass


class EditorDataTrNotIndexed(EditorDataNotIndexed):
    pass


@architect.install('partition', type='range', subtype='date', constraint='year', column='year_month')
class EditorDataTr(EditorDataNotIndexed):
    pass
