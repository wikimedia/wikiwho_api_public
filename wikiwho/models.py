import uuid

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import F
from django.db.models.signals import post_delete
from django.dispatch import receiver

from base.models import BaseModel


class Editor(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    # wikipedia_id = models.PositiveIntegerField(default=0, db_index=True)  # they are not unique in wp
    wikipedia_id = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=256, blank=True, null=False, default='')

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


class Article(BaseModel):
    id = models.PositiveIntegerField(primary_key=True, blank=False, null=False,
                                     editable=False, help_text='Wikipedia page id')
    # title = models.CharField(max_length=1024, blank=False, db_index=True)
    title = models.CharField(max_length=1024, blank=False)
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
            select_related('label_revision', 'label_revision__editor').\
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
        if 'author_id' in parameters:
            annotate_dict['author_id'] = F('label_revision__editor__wikipedia_id')
            values_list.append('author_id')
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
            #                 "wikiwho_editor"."wikipedia_id" AS "author_id",
            #                 "wikiwho_revision"."timestamp"
            # FROM "wikiwho_token"
            # INNER JOIN "wikiwho_revision" ON ("wikiwho_token"."label_revision_id" = "wikiwho_revision"."id")
            # INNER JOIN "wikiwho_editor" ON ("wikiwho_revision"."editor_id" = "wikiwho_editor"."id")
            # WHERE ("wikiwho_revision"."article_id" = 2161298
            #        AND CASE
            #                WHEN "wikiwho_token"."outbound" IS NULL THEN NULL
            #                ELSE coalesce(array_length("wikiwho_token"."outbound", 1), 0)
            #            END > 5
            #        AND NOT ("wikiwho_token"."last_used" = 743570973))
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
    id = models.PositiveIntegerField(primary_key=True, blank=False, null=False,
                                     editable=False, help_text='Wikipedia revision id')
    article = models.ForeignKey(Article, blank=False, null=False, related_name='revisions')
    # article_id = models.PositiveIntegerField(blank=False, null=False)
    editor = models.ForeignKey(Editor, blank=False, related_name='revisions')
    # editor_id = models.UUIDField(blank=False, null=False, editable=False)
    timestamp = models.DateTimeField(blank=True, null=True)
    length = models.PositiveIntegerField(default=0)
    # size
    # created = models.DateTimeField(auto_now_add=True)
    # creation_duration = models.TimeField(blank=True, null=True)
    # relations = JSON

    # class Meta:
    #     ordering = ['timestamp', 'id']

    def __str__(self):
        # return 'Revision #{}: {}'.format(self.id, self.article.title)
        return str(self.id)

    @property
    def tokens(self):
        # TODO compare timing with this
        # tokens = self.article.tokens.\
        #     filter(sentences__sentence__paragraphs__paragraph__revisions__revision__id=self.id)
        tokens = Token.objects.\
            filter(sentences__sentence__paragraphs__paragraph__revisions__revision__id=self.id).\
            select_related('label_revision', 'label_revision__editor').\
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

    def to_json(self, parameters, content=False, deleted=False, threshold=5):
        annotate_dict = {'str': F('value')}
        values_list = ['str']
        if 'rev_id' in parameters:
            annotate_dict['rev_id'] = F('label_revision__id')
            values_list.append('rev_id')
        if 'author_id' in parameters:
            annotate_dict['author_id'] = F('label_revision__editor__wikipedia_id')
            values_list.append('author_id')
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
            json_data = {"author": self.editor.name,
                         # "time": str(self.timestamp),
                         "time": self.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         "tokens": list(tokens)}
            # SELECT "wikiwho_token"."token_id",
            #        "wikiwho_token"."inbound",
            #        "wikiwho_token"."outbound",
            #        "wikiwho_token"."label_revision_id" AS "rev_id",
            #        "wikiwho_token"."value" AS "str",
            #        "wikiwho_editor"."wikipedia_id" AS "author_id"
            # FROM "wikiwho_token"
            # INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
            # INNER JOIN "wikiwho_sentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_sentence"."id")
            # INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentence"."id" = "wikiwho_paragraphsentence"."sentence_id")
            # INNER JOIN "wikiwho_paragraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_paragraph"."id")
            # INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraph"."id" = "wikiwho_revisionparagraph"."paragraph_id")
            # INNER JOIN "wikiwho_revision" T8 ON ("wikiwho_token"."label_revision_id" = T8."id")
            # INNER JOIN "wikiwho_editor" ON (T8."editor_id" = "wikiwho_editor"."id")
            # WHERE "wikiwho_revisionparagraph"."revision_id" = 743570973
            # ORDER BY "wikiwho_revisionparagraph"."position" ASC,
            #          "wikiwho_paragraphsentence"."position" ASC,
            return json_data
        elif deleted:
            deleted_tokens = self.deleted_tokens(threshold).annotate(**annotate_dict).values(*values_list)
            return list(deleted_tokens)
        return False


class RevisionParagraph(BaseModel):
    revision = models.ForeignKey(Revision, blank=False, related_name='paragraphs')
    # revision_id = models.PositiveIntegerField(blank=False, null=False)
    paragraph = models.ForeignKey('Paragraph', blank=False, related_name='revisions')
    # paragraph_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.PositiveIntegerField(blank=False)
    # action

    # class Meta:
    #     ordering = ['revision__timestamp',
    #                 'position']

    def __str__(self):
        return 'RP #{}'.format(self.id)
        # return 'RP #{}: {}'.format(self.id, self.paragraph.hash_value)


class Paragraph(BaseModel):
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    hash_value = models.CharField(max_length=32, blank=False, default='')
    # value = models.TextField(default='')

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
    paragraph = models.ForeignKey(Paragraph, blank=False, related_name='sentences')
    # paragraph_id = models.UUIDField(blank=False, null=False, editable=False)
    sentence = models.ForeignKey('Sentence', blank=False, related_name='paragraphs')
    # sentence_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.PositiveIntegerField(blank=False)
    # action

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
    # value = models.TextField(default='')

    def __str__(self):
        return 'Sentence #{}'.format(self.id)

    @property
    def splitted(self):
        return self.tokens.select_related('token').values_list('token__value', flat=True)

    @property
    def text(self):
        return ' '.join(self.splitted)


class SentenceToken(BaseModel):
    sentence = models.ForeignKey(Sentence, blank=False, related_name='tokens')
    # sentence_id = models.UUIDField(blank=False, null=False, editable=False)
    token = models.ForeignKey('Token', blank=False, related_name='sentences')
    # token_id = models.UUIDField(blank=False, null=False, editable=False)
    position = models.PositiveIntegerField(blank=False)

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
    # unique per article
    id = models.UUIDField(primary_key=True, blank=False, null=False, editable=False)
    value = models.TextField(blank=False, null=False)
    last_used = models.PositiveIntegerField(blank=False, null=False, default=0)  # last used revision ids
    inbound = ArrayField(models.IntegerField(), blank=True, null=True)  # inbound/reintroduced in revision ids
    outbound = ArrayField(models.IntegerField(), blank=True, null=True)  # outbound/deleted in revision ids
    label_revision = models.ForeignKey(Revision, blank=False, related_name='introduced_tokens')
    # label_revision_id = models.PositiveIntegerField(blank=False, null=False)
    token_id = models.PositiveIntegerField(blank=False)  # sequential id in article, unique per article
    # article_id = models.PositiveIntegerField(blank=False, null=False, unique=True)
    # article = models.ForeignKey(Article, blank=False, related_name='tokens')

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
