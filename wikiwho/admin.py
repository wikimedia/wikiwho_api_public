from django.contrib import admin

from base.admin import BaseAdmin

from .models import Article, EditorDataEnNotIndexed, EditorDataEn, EditorDataEuNotIndexed, EditorDataEu, \
    EditorDataDeNotIndexed, EditorDataDe


class ArticleAdmin(BaseAdmin):
    search_fields = ('page_id', 'title', )
    list_display = ('page_id', 'title', 'language', 'rvcontinue', 'spam_ids', )
    readonly_fields = ('id', 'page_id', 'title', 'rvcontinue', 'spam_ids', 'language', )
    list_filter = ('language', )

    """
    def article_revisions(self, obj):
        table = '<table style="width:100%">'
        table += '<thead><tr><th>REVISION</th><th>EDITOR</th><th>TIMESTAMP</th><th>CREATED</th></thead>'
        table += '<tbody>'
        i = 1
        c = 0
        for r in obj.revisions.order_by('-timestamp').all():
            table += '<tr class="row{}"><td><a href="{}">{}</a></td><td>{}</td><td>{}</td><td>{}</td></tr>'.\
                format(i, r.get_admin_url(), r.id, r.editor, r.timestamp, r.created)
            i = 1 if i == 2 else 2
            c += 1
        table += '</tbody>'
        table += '</table>'
        table = '<br><div># revisions: {}</div>'.format(c) + table
        return format_html(table)
    article_revisions.short_description = 'Article revisions'
    """


class EditorDataNotIndexedAdmin(BaseAdmin):
    list_display = ('id', 'article_id', 'editor_id', 'editor_name', 'year_month',
                    'o_adds', 'o_adds_surv_48h', 'dels', 'dels_surv_48h',
                    'reins', 'reins_surv_48h', 'persistent_o_adds', 'persistent_actions',)
    readonly_fields = ('id', 'article_id', 'editor_id', 'editor_name', 'year_month',
                       'o_adds', 'o_adds_surv_48h', 'dels', 'dels_surv_48h',
                       'reins', 'reins_surv_48h', 'persistent_o_adds', 'persistent_actions',)
    search_fields = ('editor_id', 'article_id', )
    date_hierarchy = 'year_month'


class EditorDataIndexedAdmin(EditorDataNotIndexedAdmin):
    ordering = ('-year_month', )


class EditorDataEnNotIndexedAdmin(EditorDataNotIndexedAdmin):
    pass


class EditorDataEnAdmin(EditorDataIndexedAdmin):
    pass


class EditorDataEuNotIndexedAdmin(EditorDataNotIndexedAdmin):
    pass


class EditorDataEuAdmin(EditorDataIndexedAdmin):
    pass


class EditorDataDeNotIndexedAdmin(EditorDataNotIndexedAdmin):
    pass


class EditorDataDeAdmin(EditorDataIndexedAdmin):
    pass


admin.site.register(Article, ArticleAdmin)
admin.site.register(EditorDataEnNotIndexed, EditorDataEnNotIndexedAdmin)
admin.site.register(EditorDataEn, EditorDataEnAdmin)
admin.site.register(EditorDataEuNotIndexed, EditorDataEuNotIndexedAdmin)
admin.site.register(EditorDataEu, EditorDataEuAdmin)
admin.site.register(EditorDataDeNotIndexed, EditorDataDeNotIndexedAdmin)
admin.site.register(EditorDataDe, EditorDataDeAdmin)

"""
from .models import Revision, Token


class RevisionAdmin(BaseAdmin):
    # inlines = [RevisionParagraphInline]
    search_fields = ('id', )
    # list_select_related = ('article', )
    list_display = ('id', 'article_id', 'editor', 'timestamp', 'created', )
    # list_filter = ('article', )
    readonly_fields = ('id', 'article_id', 'editor', 'timestamp', 'length', 'created', )


class TokenAdmin(BaseAdmin):
    list_display = ('id', 'value', 'origin_rev_id', 'token_id', 'last_rev_id', 'len_inbound', 'len_outbound', )
    readonly_fields = ('id', 'value', 'last_rev_id', 'inbound', 'outbound', 'origin_rev_id', 'token_id', )

    def len_inbound(self, obj):
        return len(obj.inbound)
    len_inbound.short_description = 'len inbound'

    def len_outbound(self, obj):
        return len(obj.outbound)
    len_outbound.short_description = 'len outbound'

admin.site.register(Revision, RevisionAdmin)
admin.site.register(Token, TokenAdmin)
"""
