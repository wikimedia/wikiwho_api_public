from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import F
from django.conf import settings
# from django.utils.functional import cached_property

from base.models import BaseModel
from wikiwho.utils_db import tokens_custom


class Article(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia page id')
    title = models.CharField(max_length=256, blank=False)
    rvcontinue = models.CharField(max_length=32, blank=True, null=False, default='0')
    spam_ids = ArrayField(models.IntegerField(), blank=True, null=True)  # array of spam revision ids
    # langauge = models.CharField(choices=(('en', 'English'), ('de', 'German')), max_length=2, default='en')

    def __str__(self):
        return self.title

    @property
    def pickle_file(self):
        return '{}/{}.p'.format(settings.PICKLE_FOLDER, self.id)

    @property
    def wikipedia_url(self):
        return 'https://en.wikipedia.org/wiki/{}'.format(self.title)

    def deleted_tokens(self, threshold, last_rev_id=None, ordered=False):
        if threshold > 0:
            filter_ = {'article_id': self.id,
                       'outbound__len__gt': threshold}
        else:
            # threshold as 0.
            filter_ = {'article_id': self.id}
        order_fields = ['timestamp', 'token_id'] if ordered else []
        deleted_tokens = Token.objects.\
            filter(**filter_).\
            exclude(last_rev_id=last_rev_id).\
            order_by(*order_fields)
        return deleted_tokens

    def to_json(self, parameters, content=False, deleted=False, threshold=5, last_rev_id=None, ids=False, ordered=True, explain=False):
        if not last_rev_id and not ids:
            last_rev = self.revisions.order_by('timestamp').last()
            # """
            # SELECT "wikiwho_revision"."id",
            #        "wikiwho_revision"."article_id",
            #        "wikiwho_revision"."editor",
            #        "wikiwho_revision"."timestamp",
            #        "wikiwho_revision"."length",
            #        "wikiwho_revision"."created"
            # FROM "wikiwho_revision"
            # WHERE "wikiwho_revision"."article_id" = 662
            # ORDER BY "wikiwho_revision"."timestamp" DESC LIMIT 1
            # """
            if not last_rev and self.rvcontinue == '1':
                # This article has no revision, because all is detected as spam by wikiwho
                return {}
                # return {'message': 'This article has no revision in Wikiwho system.'}
            last_rev_id = last_rev.id
        elif content and not ids:
            last_rev = Revision.objects.get(id=last_rev_id)

        if content:
            return {last_rev_id: last_rev.to_json(parameters, content=True, custom=True, ordered=ordered, explain=explain)}
        elif deleted:
            annotate_dict, values_list = Revision.get_annotate_and_values(parameters, deleted=True)
            deleted_tokens = self.deleted_tokens(threshold, last_rev_id, ordered)
            json_data = dict()
            json_data["deleted_tokens"] = list(deleted_tokens.annotate(**annotate_dict).values(*values_list))
            # token_ids = [t['token_id'] for t in json_data['deleted_tokens']]
            # print(len(token_ids), len(set(token_ids)))
            # assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(self.title)
            # assert len(token_ids) == len(json_data['deleted_tokens']), "{}: there are duplicated token ids".format(self.title)
            # SQL query:
            # SELECT "wikiwho_token"."editor",
            #        "wikiwho_token"."token_id",
            #        "wikiwho_token"."inbound",
            #        "wikiwho_token"."outbound",
            #        "wikiwho_token"."label_revision_id" AS "rev_id",
            #        "wikiwho_token"."value" AS "str"
            # FROM "wikiwho_token"
            # WHERE (CASE
            #            WHEN "wikiwho_token"."outbound" IS NULL THEN NULL
            #            ELSE coalesce(array_length("wikiwho_token"."outbound", 1), 0)
            #        END > 5
            #        AND "wikiwho_token"."article_id" = 662
            #        AND NOT ("wikiwho_token"."last_used" = 754673798))

            # no editor and threshold = 0
            # """
            # EXPLAIN SELECT "wikiwho_token"."token_id",
            #                "wikiwho_token"."inbound",
            #                "wikiwho_token"."outbound",
            #                "wikiwho_token"."label_revision_id" AS "rev_id",
            #                "wikiwho_token"."value" AS "str"
            #         FROM "wikiwho_token"
            #         WHERE ("wikiwho_token"."article_id" = 662
            #                AND NOT ("wikiwho_token"."last_used" = 754673798))
            # """
            json_data["revision_id"] = last_rev_id
            return json_data

        return False


class Revision(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia revision id')
    article = models.ForeignKey(Article, blank=False, null=False, related_name='revisions')
    # article_id = models.IntegerField(blank=False, null=False)
    editor = models.CharField(max_length=87, blank=False, null=False)  # max_length='0|' + 85
    timestamp = models.DateTimeField(blank=True, null=True)
    length = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    position = models.IntegerField(blank=False)
    original_adds = models.IntegerField(blank=False)
    token_ids = ArrayField(models.IntegerField(), blank=True, null=True)  # ordered list of token ids

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

    def tokens_custom(self, values_list, ordered=True, explain=False, return_dict=True):
        # TODO do we need this?
        return tokens_custom(self.id, values_list, ordered, explain, return_dict)

    def deleted_tokens(self, threshold, ordered=False):
        if threshold > 0:
            filter_ = {'article_id': self.article_id,
                       'outbound__len__gt': threshold}
        else:
            # threshold as 0.
            filter_ = {'article_id': self.article_id}
        order_fields = ['timestamp', 'token_id'] if ordered else []
        deleted_tokens = Token.objects.\
            filter(**filter_).\
            exclude(last_used=self.id).\
            order_by(*order_fields)
        return deleted_tokens

    # @lru_cache(maxsize=None, typed=False)
    # TODO use this cache only for last rev ids. but how?
    def to_json(self, parameters, content=False, deleted=False, threshold=5, custom=False, ordered=True, explain=False, with_token_ids=True):
        annotate_dict, values_list = self.get_annotate_and_values(parameters, deleted=deleted)
        if content:
            if custom:
                tokens = self.tokens_custom(values_list, ordered, explain)
                # SQL query:
                # """
                # """
            else:
                tokens = self.tokens_list(annotate_dict, values_list, with_token_ids=with_token_ids)
                # SQL query:
            json_data = {"editor": self.editor,
                         # "time": str(self.timestamp),
                         "time": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         "tokens": tokens}
            return json_data
        elif deleted:
            deleted_tokens = self.deleted_tokens(threshold, ordered).annotate(**annotate_dict).values(*values_list)
            return list(deleted_tokens)
        return False


class Token(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)  # unique per article
    value = models.TextField(blank=False, null=False)
    article = models.ForeignKey(Article, blank=False, null=False, related_name='tokens')
    # article_id = models.IntegerField(blank=False, null=False)
    token_id = models.IntegerField(blank=False)  # sequential id in article, unique per article
    origin_rev = models.ForeignKey(Revision, blank=False, related_name='introduced_tokens')
    # origin_rev_id = models.IntegerField(blank=False, null=False)
    editor = models.CharField(max_length=87, default='', help_text='Editor of label revision')  # max_length='0|' + 85
    last_rev_id = models.IntegerField(blank=False, null=False, default=0)
    inbound = ArrayField(models.IntegerField(), blank=True, null=True)  # inbound/reintroduced in revision ids
    outbound = ArrayField(models.IntegerField(), blank=True, null=True)  # outbound/deleted in revision ids
    # conflict_score = models.IntegerField(null=True)

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
    values = models.TextField()
    token_ids = models.TextField()
    rev_ids = models.TextField()
    editors = models.TextField()
    inbound = models.TextField()
    outbound = models.TextField()
    # values = ArrayField(models.TextField(), blank=True, null=True)
    # token_ids = ArrayField(models.IntegerField(), blank=True, null=True)
    # rev_ids = ArrayField(models.IntegerField(), blank=True, null=True)
    # editors = ArrayField(models.CharField(max_length=87), blank=True, null=True)
    # inbound = ArrayField(models.IntegerField(), blank=True, null=True)
    # outbound = ArrayField(models.IntegerField(), blank=True, null=True)
