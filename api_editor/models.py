from django.db import models

from base.models import BaseModel


class EditorData(BaseModel):
    # Use editor id and name separately because indexing on int is faster
    editor_name = models.CharField(max_length=85, default='')  # max_length='0|' + 85
    o_adds = models.IntegerField(blank=False)
    o_adds_surv_48h = models.IntegerField(blank=False)
    dels = models.IntegerField(blank=False)
    dels_surv_48h = models.IntegerField(blank=False)
    reins = models.IntegerField(blank=False)
    reins_surv_48h = models.IntegerField(blank=False)
    persistent_o_adds = models.IntegerField(blank=False)
    persistent_actions = models.IntegerField(blank=False)
    adds_stopword_count = models.IntegerField(blank=False, default=0)
    dels_stopword_count = models.IntegerField(blank=False, default=0)
    reins_stopword_count = models.IntegerField(blank=False, default=0)


    @property
    def language(self):
        return self.__class__.__name__.lower().split('editordata')[-1]

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)


class EditorDataNotIndexed(EditorData):
    article_id = models.IntegerField(blank=False, null=False)
    editor_id = models.IntegerField(blank=False, null=False)
    year_month = models.DateField(blank=False, null=False)

    class Meta:
        abstract = True


class EditorDataEnNotIndexed(EditorDataNotIndexed):
    pass


class EditorDataEn(EditorDataNotIndexed):
    pass

    # class Meta:
    #     ordering = ['year_month', 'editor_id']


class EditorDataEuNotIndexed(EditorDataNotIndexed):
    pass


class EditorDataEu(EditorDataNotIndexed):
    pass


class EditorDataDeNotIndexed(EditorDataNotIndexed):
    pass


class EditorDataDe(EditorDataNotIndexed):
    pass


class EditorDataEsNotIndexed(EditorDataNotIndexed):
    pass


class EditorDataEs(EditorDataNotIndexed):
    pass


class EditorDataTrNotIndexed(EditorDataNotIndexed):
    pass


class EditorDataTr(EditorDataNotIndexed):
    pass
