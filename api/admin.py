from os.path import exists

from django.contrib import admin
from django.utils.html import format_html

from .models import LongFailedArticle, RecursionErrorArticle
from .utils_pickles import get_pickle_folder, pickle_load


class LongFailedArticleAdmin(admin.ModelAdmin):
    date_hierarchy = 'modified'
    list_display = ('id', 'page_id_', 'title_', 'language', 'count', 'revisions_', 'pickle_exists', 'created', 'modified', )
    list_filter = ('language', 'page_id', 'id', )
    readonly_fields = ('created', 'modified', )
    ordering = ('-modified', )

    def page_id_(self, obj):
        return '<a href="https://{}.wikipedia.org/w/api.php?action=query&prop=info&inprop=url&format=json&' \
               'pageids={}">{}</a>'.format(obj.language, obj.page_id, obj.page_id)
    page_id_.short_description = 'Page ID'
    page_id_.allow_tags = True

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
        pickle_path = "{}/{}.p".format(get_pickle_folder(obj.language), obj.page_id)
        if exists(pickle_path):
            ww = pickle_load(pickle_path)
            if ww.ordered_revisions:
                last_rev_in_pickle = ww.ordered_revisions[-1]
                return format_html('<a href="https://{}.wikipedia.org/w/index.php?title={}&oldid={}">{}</a>'.
                                   format(obj.language, obj.title, last_rev_in_pickle, last_rev_in_pickle))
            else:
                return 'No rev in pickle'
        return False


class RecursionErrorArticleAdmin(LongFailedArticleAdmin):
    pass


admin.site.register(LongFailedArticle, LongFailedArticleAdmin)
admin.site.register(RecursionErrorArticle, RecursionErrorArticleAdmin)
