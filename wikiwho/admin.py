from django.contrib import admin

# from django.utils.html import format_html
from .models import Article, Revision, RevisionParagraph, Paragraph, ParagraphSentence, Sentence, \
    SentenceToken, Token
from base.admin import BaseAdmin

# TODO make everything read only + base admin class + check list_filters, show_change_link + test searching


# class ArticleAdmin(BaseAdmin):
#     search_fields = ('id', 'title', )
#     list_display = ('id', 'title', 'rvcontinue', 'spam', )
#     readonly_fields = ('id', 'title', 'rvcontinue', 'spam', 'article_revisions', )
#
#     def article_revisions(self, obj):
#         table = '<table style="width:100%">'
#         table += '<thead><tr><th>REVISION</th><th>EDITOR</th><th>TIMESTAMP</th><th>CREATED</th></thead>'
#         table += '<tbody>'
#         i = 1
#         c = 0
#         for r in obj.revisions.order_by('-timestamp').all():
#             table += '<tr class="row{}"><td><a href="{}">{}</a></td><td>{}</td><td>{}</td><td>{}</td></tr>'.\
#                 format(i, r.get_admin_url(), r.id, r.editor, r.timestamp, r.created)
#             i = 1 if i == 2 else 2
#             c += 1
#         table += '</tbody>'
#         table += '</table>'
#         table = '<br><div># revisions: {}</div>'.format(c) + table
#         return format_html(table)
#     article_revisions.short_description = 'Article revisions'
#
#
# # class RevisionParagraphInline(admin.TabularInline):
# #     model = RevisionParagraph
#
#
# class RevisionAdmin(BaseAdmin):
#     # inlines = [RevisionParagraphInline]
#     search_fields = ('id', )
#     list_select_related = ('article', )
#     list_display = ('id', 'article', 'editor', 'timestamp', 'created', )
#     # list_filter = ('article', )
#     readonly_fields = ('id', 'article', 'editor', 'timestamp', 'length', 'created', 'revision_paragraphs', )
#
#     def revision_paragraphs(self, obj):
#         table = '<table style="width:100%">'
#         table += '<thead><tr><th>Paragraph</th><th>POSITION</th></thead>'
#         table += '<tbody>'
#         i = 1
#         c = 0
#         for rp in obj.paragraphs.select_related('paragraph').all():
#             table += '<tr class="row{}"><td><a href="{}">{}</a></td><td>{}</td></tr>'.\
#                 format(i, rp.paragraph.get_admin_url(), rp.paragraph, rp.position)
#             i = 1 if i == 2 else 2
#             c += 1
#         table += '</tbody>'
#         table += '</table>'
#         table = '<br><div># paragraphs: {}</div>'.format(c) + table
#         return format_html(table)
#     revision_paragraphs.short_description = 'Revision paragraphs'
#
#
# class RevisionParagraphAdmin(BaseAdmin):
#     list_select_related = ('revision', 'paragraph', )
#     list_display = ('id', 'revision', 'paragraph', 'position', )
#     # list_filter = ('revision', )
#     readonly_fields = ('revision', 'paragraph', 'position', )
#
#
# class ParagraphAdmin(BaseAdmin):
#     list_display = ('id', 'hash_value', )
#     readonly_fields = ('id', 'hash_value', 'paragraph_sentences', )
#
#     def paragraph_sentences(self, obj):
#         table = '<table style="width:100%">'
#         table += '<thead><tr><th>SENTENCE</th><th>POSITION</th></thead>'
#         table += '<tbody>'
#         i = 1
#         c = 0
#         for ps in obj.sentences.select_related('sentence').all():
#             table += '<tr class="row{}"><td><a href="{}">{}</a></td><td>{}</td></tr>'.\
#                 format(i, ps.sentence.get_admin_url(), ps.sentence, ps.position)
#             i = 1 if i == 2 else 2
#             c += 1
#         table += '</tbody>'
#         table += '</table>'
#         table = '<br><div># sentences: {}</div>'.format(c) + table
#         return format_html(table)
#     paragraph_sentences.short_description = 'Paragraph sentences'
#
#
# class ParagraphSentenceAdmin(BaseAdmin):
#     list_select_related = ('paragraph', 'sentence', )
#     list_display = ('id', 'paragraph', 'sentence', 'position', )
#     readonly_fields = ('paragraph', 'sentence', 'position', )
#
#
# class SentenceAdmin(BaseAdmin):
#     list_display = ('id', 'hash_value', )
#     readonly_fields = ('id', 'hash_value', 'sentence_tokens', )
#
#     def sentence_tokens(self, obj):
#         table = '<table style="width:100%">'
#         table += '<thead><tr><th>TOKEN</th><th>POSITION</th></thead>'
#         table += '<tbody>'
#         i = 1
#         c = 0
#         for st in obj.tokens.select_related('token').all():
#             table += '<tr class="row{}"><td><a href="{}">{}</a></td><td>{}</td></tr>'.\
#                 format(i, st.token.get_admin_url(), st.token, st.position)
#             i = 1 if i == 2 else 2
#             c += 1
#         table += '</tbody>'
#         table += '</table>'
#         table = '<br><div># tokens: {}</div>'.format(c) + table
#         return format_html(table)
#     sentence_tokens.short_description = 'Sentence tokens'
#
#
# class SentenceTokenAdmin(BaseAdmin):
#     list_select_related = ('sentence', 'token', )
#     list_display = ('id', 'sentence', 'token', 'position', )
#     readonly_fields = ('sentence', 'token', 'position', )
#
#
# class TokenAdmin(BaseAdmin):
#     list_select_related = ('label_revision', )
#     list_display = ('id', 'value', 'label_revision', 'token_id', 'last_used', 'len_inbound', 'len_outbound', )
#     readonly_fields = ('id', 'value', 'last_used', 'inbound', 'outbound', 'label_revision', 'token_id', )
#
#     def len_inbound(self, obj):
#         return len(obj.inbound)
#     len_inbound.short_description = 'len inbound'
#
#     def len_outbound(self, obj):
#         return len(obj.outbound)
#     len_outbound.short_description = 'len outbound'
#
# admin.site.register(Article, ArticleAdmin)
# admin.site.register(Revision, RevisionAdmin)
# admin.site.register(RevisionParagraph, RevisionParagraphAdmin)
# admin.site.register(Paragraph, ParagraphAdmin)
# admin.site.register(ParagraphSentence, ParagraphSentenceAdmin)
# admin.site.register(Sentence, SentenceAdmin)
# admin.site.register(SentenceToken, SentenceTokenAdmin)
# admin.site.register(Token, TokenAdmin)


class ArticleAdmin(BaseAdmin):
    list_display = ('id', 'title', 'rvcontinue', 'spam', )
    readonly_fields = ('id', 'title', 'rvcontinue', 'spam', )


class RevisionAdmin(BaseAdmin):
    list_display = ('id', 'article_id', 'editor', 'timestamp', 'created', )
    readonly_fields = ('id', 'article_id', 'editor', 'timestamp', 'length', 'created', )


class RevisionParagraphAdmin(BaseAdmin):
    list_display = ('id', 'revision_id', 'paragraph_id', 'position', )
    readonly_fields = ('revision_id', 'paragraph_id', 'position', )


class ParagraphAdmin(BaseAdmin):
    list_display = ('id', 'hash_value', )
    readonly_fields = ('id', 'hash_value', )


class ParagraphSentenceAdmin(BaseAdmin):
    list_display = ('id', 'paragraph_id', 'sentence_id', 'position', )
    readonly_fields = ('paragraph_id', 'sentence_id', 'position', )


class SentenceAdmin(BaseAdmin):
    list_display = ('id', 'hash_value', )
    readonly_fields = ('id', 'hash_value', )


class SentenceTokenAdmin(BaseAdmin):
    list_display = ('id', 'sentence_id', 'token_id', 'position', )
    readonly_fields = ('sentence_id', 'token_id', 'position', )


class TokenAdmin(BaseAdmin):
    list_display = ('id', 'value', 'label_revision_id', 'token_id', 'last_used', 'len_inbound', 'len_outbound', )
    readonly_fields = ('id', 'value', 'last_used', 'inbound', 'outbound', 'label_revision_id', 'token_id', )

    def len_inbound(self, obj):
        return len(obj.inbound)
    len_inbound.short_description = 'len inbound'

    def len_outbound(self, obj):
        return len(obj.outbound)
    len_outbound.short_description = 'len outbound'

admin.site.register(Article, ArticleAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(RevisionParagraph, RevisionParagraphAdmin)
admin.site.register(Paragraph, ParagraphAdmin)
admin.site.register(ParagraphSentence, ParagraphSentenceAdmin)
admin.site.register(Sentence, SentenceAdmin)
admin.site.register(SentenceToken, SentenceTokenAdmin)
admin.site.register(Token, TokenAdmin)
