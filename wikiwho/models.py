from functools import lru_cache

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import F
# from django.utils.functional import cached_property
from django.db.models.signals import post_delete
from django.dispatch import receiver

from base.models import BaseModel


class Article(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia page id')
    title = models.CharField(max_length=256, blank=False)
    # title = models.CharField(max_length=256, blank=False, db_index=True)
    rvcontinue = models.CharField(max_length=32, blank=True, null=False, default='0')
    spam = ArrayField(models.IntegerField(), blank=True, null=True)  # array of spam revision ids
    # langauge = models.CharField(choices=(('en', 'English'), ('de', 'German')), max_length=2, default='en')

    def __str__(self):
        return self.title

    @property
    def pickle_article_name(self):
        return self.title.replace("/", "0x2f")

    @property
    def wikipedia_url(self):
        return 'https://en.wikipedia.org/wiki/{}'.format(self.title)

    def deleted_tokens(self, threshold, last_rev_id=None):
        last_rev_id = self.revisions.order_by('timestamp').last().id
        deleted_tokens = Token.objects.\
            filter(label_revision__article__id=self.id,
                   outbound__len__gt=threshold).\
            exclude(last_used=last_rev_id).\
            select_related('label_revision').\
            order_by('label_revision__timestamp',
                     'token_id').\
            distinct()
        return last_rev_id, deleted_tokens

    def to_json(self, parameters, content=False, deleted=False, threshold=5, last_rev_id=None):
        annotate_dict = {'str': F('value')}
        values_list = ['str']
        if 'rev_id' in parameters:
            annotate_dict['rev_id'] = F('label_revision__id')
            values_list.append('rev_id')
        if 'author' in parameters:
            annotate_dict['author'] = F('label_revision__editor')
            values_list.append('author')
        if 'token_id' in parameters:
            values_list.append('token_id')
        if 'inbound' in parameters:
            values_list.append('inbound')
        if 'outbound' in parameters:
            values_list.append('outbound')
        if content:
            return NotImplemented
        elif deleted:
            revision_id, deleted_tokens = self.deleted_tokens(threshold, last_rev_id=last_rev_id)
            json_data = dict()
            json_data["deleted_tokens"] = list(deleted_tokens.annotate(**annotate_dict).values(*values_list))
            # SQL query:
            # SELECT DISTINCT "wikiwho_token"."token_id",
            #                 "wikiwho_token"."inbound",
            #                 "wikiwho_token"."outbound",
            #                 "wikiwho_token"."label_revision_id" AS "rev_id",
            #                 "wikiwho_token"."value" AS "str",
            #                 "wikiwho_revision"."editor" AS "author",
            #                 "wikiwho_revision"."timestamp"
            # FROM "wikiwho_token"
            # INNER JOIN "wikiwho_revision" ON ("wikiwho_token"."label_revision_id" = "wikiwho_revision"."id")
            # WHERE (CASE
            #            WHEN "wikiwho_token"."outbound" IS NULL THEN NULL
            #            ELSE coalesce(array_length("wikiwho_token"."outbound", 1), 0)
            #        END > 5
            #        AND "wikiwho_revision"."article_id" = 2197
            #        AND NOT ("wikiwho_token"."last_used" = 747409474))
            # ORDER BY "wikiwho_revision"."timestamp" ASC,
            #          "wikiwho_token"."token_id" ASC
            json_data["revision_id"] = revision_id
            return json_data
        return False


@receiver(post_delete, sender=Article)
def article_post_delete(sender, instance, *args, **kwargs):
    print(Paragraph.objects.filter(revisions=None).delete())
    print(Sentence.objects.filter(tokens=None).delete())


class Revision(BaseModel):
    id = models.IntegerField(primary_key=True, blank=False, null=False, editable=False, help_text='Wikipedia revision id')
    article = models.ForeignKey(Article, blank=False, null=False, related_name='revisions')
    # article_id = models.IntegerField(blank=False, null=False)
    editor = models.CharField(max_length=87, blank=False, null=False)  # max_length='0|' + 85
    timestamp = models.DateTimeField(blank=True, null=True)
    length = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    # relations = JSON

    # class Meta:
    #     ordering = ['timestamp', 'id']

    def __str__(self):
        # return 'Revision #{}: {}'.format(self.id, self.article.title)
        return str(self.id)

    # @cached_property
    @property
    def tokens(self):
        # TODO compare timing with this
        # tokens = self.article.tokens.\
        #     filter(sentences__sentence__paragraphs__paragraph__revisions__revision__id=self.id)
        tokens = Token.objects.\
            filter(sentences__sentence__paragraphs__paragraph__revisions__revision__id=self.id).\
            select_related('label_revision').\
            order_by('sentences__sentence__paragraphs__paragraph__revisions__position',
                     'sentences__sentence__paragraphs__position',
                     'sentences__position')
            # order_by('label_revision__timestamp', 'token_id')
        # tokens = SentenceToken.objects\
        #     .filter(sentence__paragraphs__paragraph__revisions__revision__id=self.id).\
        #     select_related('label_revision', 'label_revision__editor').\
        #     order_by('sentence__paragraphs__paragraph__revisions__position',
        #              'sentence__paragraphs__position',
        #              'position')
        return tokens

    def deleted_tokens(self, threshold):
        deleted_tokens = Token.objects.\
            filter(label_revision__article__id=self.article.id,
                   outbound__len__gt=threshold).\
            exclude(last_used=self.id).\
            select_related('label_revision', 'label_revision__editor').\
            order_by('label_revision__timestamp',
                     'token_id').\
            distinct()
        return deleted_tokens

    # @lru_cache(maxsize=None, typed=False)
    # TODO use this cache only for last rev ids. but how?
    def to_json(self, parameters, content=False, deleted=False, threshold=5):
        annotate_dict = {'str': F('value')}
        values_list = ['str']
        if 'rev_id' in parameters:
            annotate_dict['rev_id'] = F('label_revision__id')
            values_list.append('rev_id')
        if 'author' in parameters:
            annotate_dict['author'] = F('label_revision__editor')
            values_list.append('author')
        if 'token_id' in parameters:
            values_list.append('token_id')
        if 'inbound' in parameters:
            values_list.append('inbound')
        if 'outbound' in parameters:
            values_list.append('outbound')

        if content:
            tokens = self.tokens.annotate(**annotate_dict).values(*values_list)
            #          "wikiwho_sentencetoken"."position" ASC
            # print(len(tokens))
            json_data = {"author": self.editor,
                         # "time": str(self.timestamp),
                         "time": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         "tokens": list(tokens)}
            # SQL query:
            # SELECT "wikiwho_token"."token_id",
            #        "wikiwho_token"."inbound",
            #        "wikiwho_token"."outbound",
            #        "wikiwho_token"."label_revision_id" AS "rev_id",
            #        "wikiwho_token"."value" AS "str",
            #        T8."editor" AS "author"
            # FROM "wikiwho_token"
            # INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
            # INNER JOIN "wikiwho_sentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_sentence"."id")
            # INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentence"."id" = "wikiwho_paragraphsentence"."sentence_id")
            # INNER JOIN "wikiwho_paragraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_paragraph"."id")
            # INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraph"."id" = "wikiwho_revisionparagraph"."paragraph_id")
            # INNER JOIN "wikiwho_revision" T8 ON ("wikiwho_token"."label_revision_id" = T8."id")
            # WHERE "wikiwho_revisionparagraph"."revision_id" = 9100
            # ORDER BY "wikiwho_revisionparagraph"."position" ASC,
            #          "wikiwho_paragraphsentence"."position" ASC,
            #          "wikiwho_sentencetoken"."position" ASC
            return json_data
        elif deleted:
            deleted_tokens = self.deleted_tokens(threshold).annotate(**annotate_dict).values(*values_list)
            return list(deleted_tokens)
        return False


class RevisionParagraph(BaseModel):
    # id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    id = models.BigAutoField(primary_key=True)
    revision = models.ForeignKey(Revision, blank=False, related_name='paragraphs')
    # revision_id = models.IntegerField(blank=False, null=False)
    paragraph = models.ForeignKey('Paragraph', blank=False, related_name='revisions')
    # paragraph_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.IntegerField(blank=False)

    # class Meta:
    #     ordering = ['revision__timestamp',
    #                 'position']

    def __str__(self):
        return 'RP #{}'.format(self.id)
        # return 'RP #{}: {}'.format(self.id, self.paragraph.hash_value)


class Paragraph(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    hash_value = models.CharField(max_length=32, blank=False, default='')

    def __str__(self):
        return 'Paragraph #{}'.format(self.id)

    # class Meta:
    #     ordering = ['id']

    @property
    def text(self):
        text = []
        for s in self.sentences.all():
            text.append(s.sentence.text)
        return ' '.join(text)


class ParagraphSentence(BaseModel):
    # id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    id = models.BigAutoField(primary_key=True)
    paragraph = models.ForeignKey(Paragraph, blank=False, related_name='sentences')
    # paragraph_id = models.UUIDField(blank=False, null=False, editable=False)
    sentence = models.ForeignKey('Sentence', blank=False, related_name='paragraphs')
    # sentence_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.IntegerField(blank=False)

    # class Meta:
    #     ordering = ['paragraph__revisions__revision__timestamp',
    #                 'paragraph__revisions__position',
    #                 'position']

    def __str__(self):
        return 'PS #{}'.format(self.id)
        # return 'PS #{}: {}'.format(self.id, self.sentence.hash_value)


class Sentence(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    hash_value = models.CharField(max_length=32, blank=False, default='')

    def __str__(self):
        return 'Sentence #{}'.format(self.id)

    @property
    def splitted(self):
        return self.tokens.select_related('token').values_list('token__value', flat=True)

    @property
    def text(self):
        return ' '.join(self.splitted)


class SentenceToken(BaseModel):
    # id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    id = models.BigAutoField(primary_key=True)
    sentence = models.ForeignKey(Sentence, blank=False, related_name='tokens')
    # sentence_id = models.UUIDField(blank=False, null=False, editable=False)
    token = models.ForeignKey('Token', blank=False, related_name='sentences')
    # token_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.IntegerField(blank=False)

    # class Meta:
    #     unique_together = (('token_id', 'label_revision_id'),)  # TODO this must be satisfied!

    #     ordering = ['sentence__paragraphs__paragraph__revisions__revision__timestamp',
    #                 'sentence__paragraphs__paragraph__revisions__position',
    #                 'sentence__paragraphs__position',
    #                 'position']

    def __str__(self):
        return 'ST #{}'.format(self.id)
        # return 'ST #{}: {}'.format(self.id, self.token)


class Token(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)  # unique per article
    value = models.TextField(blank=False, null=False)
    last_used = models.IntegerField(blank=False, null=False, default=0)  # last used revision ids
    inbound = ArrayField(models.IntegerField(), blank=True, null=True)  # inbound/reintroduced in revision ids
    outbound = ArrayField(models.IntegerField(), blank=True, null=True)  # outbound/deleted in revision ids
    label_revision = models.ForeignKey(Revision, blank=False, related_name='introduced_tokens')
    # label_revision_id = models.IntegerField(blank=False, null=False)
    token_id = models.IntegerField(blank=False)  # sequential id in article, unique per article

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

    @property
    def article(self):
        return self.label_revision.article

    @property
    def article_id(self):
        return self.label_revision.article.id

"""
class Editor(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    # wikipedia_id = models.IntegerField(default=0, db_index=True)  # they are not unique in wp
    wikipedia_id = models.IntegerField(default=0)
    name = models.CharField(max_length=87, blank=True, null=False, default='')

    # class Meta:
    #     unique_together = (('wikipedia_id', 'name'),)

    def __str__(self):
        editor = 'Editor {}'.format(self.wikipedia_id)
        if self.name:
            editor = '{} - {}'.format(editor, self.name)
        return editor

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid3(uuid.NAMESPACE_X500, '{}{}'.format(self.wikipedia_id, self.name))
        super(Editor, self).save(*args, **kwargs)

    @property
    def wikipedia_url(self):
        return 'https://en.wikipedia.org/wiki/User:{}'.format(self.name)
"""


def get_paragraphs_data(revision_id):
    return RevisionParagraph.objects.filter(revision_id=revision_id).\
                    select_related('paragraph').\
                    order_by('position').\
                    values('paragraph_id', 'paragraph__hash_value')


def get_sentences_data(paragraph_id):
    return ParagraphSentence.objects.filter(paragraph_id=paragraph_id).\
                            select_related('sentence').\
                            order_by('position').\
                            values('sentence_id', 'sentence__hash_value')


def get_tokens_data(sentence_id):
    return SentenceToken.objects.filter(sentence_id=sentence_id).\
                                    select_related('token').\
                                    order_by('position').\
                                    values('token_id', 'token__value', 'token__token_id',
                                           'token__last_used', 'token__inbound', 'token__outbound')


# TODO check https://github.com/tvavrys/django-memoize + https://github.com/3Top/lru2cache
# TODO or write your own decorator to do this by using memcached!
# each server restart clears the local cache
@lru_cache(maxsize=None, typed=False)  # The LRU feature performs best when maxsize is a power-of-two.
def get_cached_paragraphs_data(revision_id):
    return get_paragraphs_data(revision_id)


@lru_cache(maxsize=None, typed=False)
def get_cached_sentences_data(paragraph_id):
    return get_sentences_data(paragraph_id)


@lru_cache(maxsize=None, typed=False)
def get_cached_tokens_data(sentence_id):
    return get_tokens_data(sentence_id)
