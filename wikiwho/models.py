from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import F
# from django.utils.functional import cached_property
from django.db.models.signals import post_delete
from django.dispatch import receiver

from base.models import BaseModel
from wikiwho.utils_db import tokens_custom


class ArticleManager(models.Manager):
    def get_queryset(self):
        return super(ArticleManager, self).get_queryset().filter(is_article=True)


class NonArticleManager(models.Manager):
    def get_queryset(self):
        return super(NonArticleManager, self).get_queryset().filter(is_article=False)


class Article(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia page id')
    title = models.CharField(max_length=256, blank=False)
    rvcontinue = models.CharField(max_length=32, blank=True, null=False, default='0')
    spam_ids = ArrayField(models.IntegerField(), blank=True, null=True)  # array of spam revision ids
    # langauge = models.CharField(choices=(('en', 'English'), ('de', 'German')), max_length=2, default='en')
    # is_article = models.NullBooleanField(default=True)

    # objects = ArticleManager()
    # non_articles = NonArticleManager()
    # all_articles = models.Manager()

    def __str__(self):
        return self.title

    @property
    def pickle_article_name(self):
        return self.title.replace("/", "0x2f")

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
            exclude(last_used=last_rev_id).\
            select_related('label_revision').\
            order_by(*order_fields)
        return deleted_tokens

    def to_json(self, parameters, content=False, deleted=False, threshold=5, last_rev_id=None, ids=False, ordered=True, explain=False, minimal=False):
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
            return {last_rev_id: last_rev.to_json(parameters, content=True, custom=True, ordered=ordered, explain=explain, minimal=minimal)}
        elif deleted:
            annotate_dict, values_list = Revision.get_annotate_and_values(parameters, minimal=minimal)
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
        elif ids:
            json_data = dict()
            annotate_dict, values_list = Revision.get_annotate_and_values(parameters, ids=True)
            order_fields = ['timestamp'] if ordered else []
            json_data["revisions"] = list(self.revisions.order_by(*order_fields).annotate(**annotate_dict).values(*values_list))
            # """
            # EXPLAIN SELECT "wikiwho_revision"."editor",
            #                "wikiwho_revision"."timestamp",
            #                "wikiwho_revision"."id" AS "rev_id"
            #         FROM "wikiwho_revision"
            #         WHERE "wikiwho_revision"."article_id" = 662
            #         ORDER BY "wikiwho_revision"."timestamp" ASC
            # """
            # json_data["revisions"] = list(self.revisions.order_by(*order_fields).annotate(**annotate_dict).values_list(*values_list, flat=True))
            return json_data

        return False


@receiver(post_delete, sender=Article)
def article_post_delete(sender, instance, *args, **kwargs):
    # Delete all related elements
    # r_ids = list(Revision.objects.filter(article_id=instance.id).values_list('id', flat=True))
    # rp_ids = RevisionParagraph.objects.filter(revision_id__in=r_ids).values_list('id', flat=True)
    # p_ids = list(RevisionParagraph.objects.filter(revision_id__in=r_ids).values_list('paragraph_id', flat=True))
    # ps_ids = ParagraphSentence.objects.filter(paragraph_id__in=p_ids).values_list('id', flat=True)
    # s_ids = list(ParagraphSentence.objects.filter(paragraph_id__in=p_ids).values_list('sentence_id', flat=True))
    # st_ids = SentenceToken.objects.filter(sentence_id__in=s_ids).values_list('id', flat=True)
    # t_ids = SentenceToken.objects.filter(sentence_id__in=s_ids).values_list('token_id', flat=True)
    # Token.objects.filter(id__in=t_ids).delete()
    # Sentence.objects.filter(id__in=s_ids).delete()
    # SentenceToken.objects.filter(id__in=st_ids).delete()
    # Paragraph.objects.filter(id__in=p_ids).delete()
    # ParagraphSentence.objects.filter(id__in=ps_ids).delete()
    # Revision.objects.filter(id__in=r_ids).delete()
    # RevisionParagraph.objects.filter(id__in=rp_ids).delete()
    # Delete paragraphs, paragraph sentences and sentences
    # Paragraph.objects.filter(revisions=None).delete()
    # Sentence.objects.filter(tokens=None).delete()
    pass  # TODO ?


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
    def get_annotate_and_values(parameters, ids=False, minimal=False):
        annotate_dict = {}
        values_list = []
        if 'str' in parameters:
            annotate_dict['str'] = F('value')
            values_list.append('str')
        if 'rev_id' in parameters:
            annotate_dict['rev_id'] = F('id' if ids else 'label_revision_id')
            values_list.append('rev_id')
        if 'editor' in parameters:
            values_list.append('editor')
        if 'token_id' in parameters:
            if minimal:
                annotate_dict['t_id'] = F('token_id')
                values_list.append('t_id')
            else:
                values_list.append('token_id')
        if 'inbound' in parameters:
            if minimal:
                annotate_dict['in'] = F('inbound')
                values_list.append('in')
            else:
                values_list.append('inbound')
        if 'outbound' in parameters:
            if minimal:
                annotate_dict['out'] = F('outbound')
                values_list.append('out')
            else:
                values_list.append('outbound')
        if 'timestamp' in parameters:
            values_list.append('timestamp')
        return annotate_dict, values_list

    # @cached_property
    @property
    def tokens(self):
        tokens = Token.objects.\
            filter(sentences__sentence__paragraphs__paragraph__revisions__revision__id=self.id).\
            select_related('label_revision').\
            order_by('sentences__sentence__paragraphs__paragraph__revisions__position',
                     'sentences__sentence__paragraphs__position',
                     'sentences__position')
        return tokens

    def tokens_custom(self, values_list, ordered=True, explain=False, return_dict=True):
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
            select_related('label_revision').\
            order_by(*order_fields)
        return deleted_tokens

    # @lru_cache(maxsize=None, typed=False)
    # TODO use this cache only for last rev ids. but how?
    def to_json(self, parameters, content=False, deleted=False, threshold=5, custom=True, ordered=True, explain=False, minimal=False):
        annotate_dict, values_list = self.get_annotate_and_values(parameters, minimal=minimal)
        if content:
            if custom:
                tokens = self.tokens_custom(values_list, ordered, explain)
                # SQL query:
                # """
                # EXPLAIN SELECT "wikiwho_token"."token_id",
                #                "wikiwho_token"."inbound",
                #                "wikiwho_token"."outbound",
                #                "wikiwho_token"."label_revision_id",
                #                "wikiwho_token"."value",
                #                "wikiwho_token"."editor"
                #         FROM "wikiwho_token"
                #         INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
                #         INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_paragraphsentence"."sentence_id")
                #         INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_revisionparagraph"."paragraph_id")
                #         WHERE "wikiwho_revisionparagraph"."revision_id" = 19137
                #         ORDER BY "wikiwho_revisionparagraph"."position" ASC,
                #                  "wikiwho_paragraphsentence"."position" ASC,
                #                  "wikiwho_sentencetoken"."position" ASC
                # """
            else:
                tokens = self.tokens.annotate(**annotate_dict).values(*values_list)
                tokens = list(tokens)
                # SQL query:
                # SELECT "wikiwho_token"."token_id",
                #        "wikiwho_token"."inbound",
                #        "wikiwho_token"."outbound",
                #        "wikiwho_token"."label_revision_id" AS "rev_id",
                #        "wikiwho_token"."value" AS "str",
                #        "wikiwho_revision"."editor"
                # FROM "wikiwho_token"
                # INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
                # INNER JOIN "wikiwho_sentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_sentence"."id")
                # INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentence"."id" = "wikiwho_paragraphsentence"."sentence_id")
                # INNER JOIN "wikiwho_paragraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_paragraph"."id")
                # INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraph"."id" = "wikiwho_revisionparagraph"."paragraph_id")
                # INNER JOIN "wikiwho_revision" ON ("wikiwho_token"."label_revision_id" = "wikiwho_revision"."id")
                # WHERE "wikiwho_revisionparagraph"."revision_id" = 9100
                # ORDER BY "wikiwho_revisionparagraph"."position" ASC,
                #          "wikiwho_paragraphsentence"."position" ASC,
                #          "wikiwho_sentencetoken"."position" ASC
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
    article_id = models.IntegerField(blank=False, null=False)
    token_id = models.IntegerField(blank=False)  # sequential id in article, unique per article
    label_revision = models.ForeignKey(Revision, blank=False, related_name='introduced_tokens')
    # label_revision_id = models.IntegerField(blank=False, null=False)
    editor = models.CharField(max_length=87, default='', help_text='Editor of label revision')  # max_length='0|' + 85
    timestamp = models.DateTimeField(blank=True, null=True, help_text='Timestamp of label revision')
    last_used = models.IntegerField(blank=False, null=False, default=0)  # last used revision ids
    inbound = ArrayField(models.IntegerField(), blank=True, null=True)  # inbound/reintroduced in revision ids
    outbound = ArrayField(models.IntegerField(), blank=True, null=True)  # outbound/deleted in revision ids
    # conflict_score = models.IntegerField(null=True)

    # class Meta:
    #     ordering = ['sentences__sentence__paragraphs__paragraph__revisions__revision__timestamp',
    #                 'sentences__sentence__paragraphs__paragraph__revisions__position',
    #                 'sentences__sentence__paragraphs__position',
    #                 'sentences__position']

    def __str__(self):
        return 'Token #{}: {}'.format(self.id, self.value)

    @property
    def text(self):
        return self.value
