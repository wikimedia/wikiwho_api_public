from django.contrib import admin

from django.utils.html import format_html

from base.admin import BaseAdmin

from .models import Article, Revision, Token
# TODO make everything read only + base admin class + check list_filters, show_change_link + test searching


class ArticleAdmin(BaseAdmin):
    search_fields = ('id', 'title', )
    list_display = ('id', 'title', 'rvcontinue', 'spam_ids', )
    readonly_fields = ('id', 'title', 'rvcontinue', 'spam_ids', 'article_revisions', )

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

admin.site.register(Article, ArticleAdmin)
# admin.site.register(Article)
admin.site.register(Revision, RevisionAdmin)
# admin.site.register(Revision)
admin.site.register(Token, TokenAdmin)
# admin.site.register(Token)
