
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
# from django.utils.functional import cached_property

from base.models import BaseModel

from api.utils_pickles import get_pickle_folder


class Article(BaseModel):
    page_id = models.IntegerField(blank=False, null=False, db_index=True)
    title = models.CharField(max_length=256, blank=False)
    rvcontinue = models.CharField(max_length=32, blank=True, null=False, default='0')
    spam_ids = ArrayField(models.IntegerField(), blank=True, null=True)  # array of spam revision ids
    language = models.CharField(max_length=2, default='', db_index=True,
                                choices=(('', '-------'), ) + tuple(settings.LANGUAGES))

    # class Meta:
    #     unique_together = (('page_id', 'language'), )

    def __str__(self):
        return '{} - {}'.format(self.title, self.page_id)

    @property
    def pickle_file(self):
        return '{}/{}.p'.format(get_pickle_folder(self.language), self.page_id)

    @property
    def wikipedia_url(self):
        return 'https://{}.wikipedia.org/wiki/{}'.format(self.language, self.title)


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
    # total_actions = models.IntegerField(blank=False, default=0)
    # total_actions_surv_48h = models.IntegerField(blank=False, default=0)
    # total_actions_stopword_count = models.IntegerField(blank=False, default=0)
    # adds_surv_ratio = models.IntegerField(blank=False, default=0)
    # reins_surv_ratio = models.IntegerField(blank=False, default=0)
    # dels_surv_ratio = models.IntegerField(blank=False, default=0)

    # data = JSONField(null=True, blank=True)  # TODO or TextField?

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


class Revision(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia revision id')
    article = models.ForeignKey(Article, blank=False, null=False, related_name='revisions')
    editor = models.CharField(max_length=87, blank=False, null=False)  # max_length='0|' + 85
    timestamp = models.DateTimeField(blank=True, null=True)
    length = models.IntegerField(default=0)
    original_adds = models.IntegerField(blank=False)
    token_ids = ArrayField(models.IntegerField(), blank=True, null=True)  # ordered list of token ids
    # TODO: remove article and editor fields and add these:
    # article_id = models.IntegerField(blank=False, null=False)
    # # Use editor id and name separately because indexing on int is faster
    # editor_id = models.IntegerField(blank=False, null=False)
    # editor_name = models.CharField(max_length=85, default='')  # max_length='0|' + 85
    # language = models.CharField(max_length=2, default='',
    #                             choices=(('', '-------'), ('en', 'English'), ('de', 'German'), ('eu', 'Basque')))

    # class Meta:
    #     ordering = ['timestamp', 'id']

    def __str__(self):
        # return 'Revision #{}: {}'.format(self.id, self.article.title)
        return str(self.id)

    @staticmethod
    def get_annotate_and_values(parameters, ids=False, deleted=False):
        annotate_dict = {}
        values_list = []
        if 'str' in parameters:
            annotate_dict['str'] = F('value')
            values_list.append('str')
        if 'rev_id' in parameters:
            annotate_dict['rev_id'] = F('id' if ids else 'origin_rev_id')
            values_list.append('rev_id')
        if 'editor' in parameters:
            values_list.append('editor')
        if not ids and not deleted:
            values_list.append('token_id')
        if 'inbound' in parameters:
            values_list.append('inbound')
        if 'outbound' in parameters:
            values_list.append('outbound')
        if 'timestamp' in parameters:
            values_list.append('timestamp')
        return annotate_dict, values_list

    # @cached_property
    @property
    def tokens(self):
        return Token.objects.filter(article_id=self.article_id, token_id__in=self.token_ids)

    def tokens_list(self, annotate_dict, values_list, ordered=True, with_token_ids=True):
        tokens = list(self.tokens.annotate(**annotate_dict).values(*values_list))
        if ordered:
            mapping = {t['token_id']: t for t in tokens}
            if with_token_ids:
                tokens[:] = [mapping[t_id] for t_id in self.token_ids]
            else:
                tokens[:] = []
                for t_id in self.token_ids:
                    del mapping[t_id]['token_id']
                    tokens.append(mapping[t_id])
        return tokens


class Token(BaseModel):
    # TODO use uuid v1? must be better for indexing but we dont want to index?!
    # Definetely use uuid, gives uniqueness everywhere!
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)  # unique per article
    value = models.TextField(blank=False, null=False)
    article = models.ForeignKey(Article, blank=False, null=False, related_name='tokens')
    # article_id = models.IntegerField(blank=False, null=False)
    token_id = models.IntegerField(blank=False)  # sequential id in article, unique per article
    origin_rev = models.ForeignKey(Revision, blank=False, related_name='introduced_tokens')
    # origin_rev_id = models.IntegerField(blank=False, null=False)
    editor = models.CharField(max_length=87, default='', help_text='Editor of label revision')  # max_length='0|' + 85
    timestamp = models.DateTimeField(blank=True, null=True)
    last_rev_id = models.IntegerField(blank=False, null=False, default=0)
    inbound = ArrayField(models.IntegerField(), blank=True, null=True)  # inbound/reintroduced in revision ids
    outbound = ArrayField(models.IntegerField(), blank=True, null=True)  # outbound/deleted in revision ids

    # class Meta:
    #     ordering = []

    def __str__(self):
        return 'Token #{}: {}'.format(self.id, self.value)

    @property
    def text(self):
        return self.value


class RevisionContent(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia revision id')
    # TODO TextField or ArrayField
    values = models.TextField()  # token strings
    token_ids = models.TextField()
    rev_ids = models.TextField()  # origin rev ids of each token
    editors = models.TextField()
    inbound = models.TextField()
    outbound = models.TextField()
    # values = ArrayField(models.TextField(), blank=True, null=True)
    # token_ids = ArrayField(models.IntegerField(), blank=True, null=True)
    # rev_ids = ArrayField(models.IntegerField(), blank=True, null=True)
    # editors = ArrayField(models.CharField(max_length=87), blank=True, null=True)
    # inbound = ArrayField(models.IntegerField(), blank=True, null=True)
    # outbound = ArrayField(models.IntegerField(), blank=True, null=True)
"""
