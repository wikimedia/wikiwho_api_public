from os.path import exists

from django.contrib import admin
from django.conf import settings

from .models import LongFailedArticle, RecursionErrorArticle


class LongFailedArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'modified'
    list_display = ('id', 'title_', 'count', 'revisions_', 'pickle_exists', 'created', 'modified', )
    list_filter = ('id', )
    readonly_fields = ('created', 'modified', )
    ordering = ('-modified', )

    def title_(self, obj):
        return '<a href="https://en.wikipedia.org/wiki/{}">{}</a>'.format(obj.title, obj.title)
    title_.short_description = 'Title'
    title_.allow_tags = True

    def revisions_(self, obj):
        revisions = []
        for rev in obj.revisions:
            revisions.append('<a href="https://en.wikipedia.org/w/index.php?title={}&oldid={}">{}</a>'.
                             format(obj.title, rev, rev))
        return ', '.join(revisions)
    revisions_.short_description = 'Revisions'
    revisions_.allow_tags = True

    def pickle_exists(self, obj):
        pickle_path = "{}/{}.p".format(settings.PICKLE_FOLDER, obj.id)
        return exists(pickle_path)


class RecursionErrorArticleAdmin(LongFailedArticleAdmin):
    pass


admin.site.register(LongFailedArticle, LongFailedArticleAdmin)
admin.site.register(RecursionErrorArticle, RecursionErrorArticleAdmin)
