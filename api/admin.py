from os.path import exists

from django.contrib import admin

from .models import LongFailedArticle, RecursionErrorArticle
from .utils_pickles import get_pickle_folder


class LongFailedArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'modified'
    list_display = ('id', 'title_', 'language', 'count', 'revisions_', 'pickle_exists', 'created', 'modified', )
    list_filter = ('id', 'language', )
    readonly_fields = ('created', 'modified', )
    ordering = ('-modified', )

    def title_(self, obj):
        return '<a href="https://{}.wikipedia.org/wiki/{}">{}</a>'.format(obj.language, obj.title, obj.title)
    title_.short_description = 'Title'
    title_.allow_tags = True

    def revisions_(self, obj):
        revisions = []
        for rev in obj.revisions:
            revisions.append('<a href="https://{}.wikipedia.org/w/index.php?title={}&oldid={}">{}</a>'.
                             format(obj.language, obj.title, rev, rev))
        return ', '.join(revisions)
    revisions_.short_description = 'Revisions'
    revisions_.allow_tags = True

    def pickle_exists(self, obj):
        pickle_path = "{}/{}.p".format(get_pickle_folder(obj.language), obj.id)
        return exists(pickle_path)


class RecursionErrorArticleAdmin(LongFailedArticleAdmin):
    pass


admin.site.register(LongFailedArticle, LongFailedArticleAdmin)
admin.site.register(RecursionErrorArticle, RecursionErrorArticleAdmin)
