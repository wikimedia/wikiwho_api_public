from django.contrib import admin

from .models import LongFailedArticle, RecursionErrorArticle


class LongFailedArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'modified'
    list_display = ('id', 'title', 'count', 'revisions', 'created', 'modified', )
    list_filter = ('id', )
    readonly_fields = ('created', 'modified', )
    ordering = ('-modified', )


class RecursionErrorArticleAdmin(LongFailedArticleAdmin):
    pass


admin.site.register(LongFailedArticle, LongFailedArticleAdmin)
admin.site.register(RecursionErrorArticle, RecursionErrorArticleAdmin)
