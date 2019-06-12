from django.contrib import admin

from base.admin import BaseAdmin

from .models import EditorDataEnNotIndexed, EditorDataEn, EditorDataEuNotIndexed, EditorDataEu, \
    EditorDataDeNotIndexed, EditorDataDe, EditorDataEsNotIndexed, EditorDataEs, EditorDataTrNotIndexed, EditorDataTr


class EditorDataNotIndexedAdmin(BaseAdmin):
    list_display = ('id', 'page_id_', 'editor_id_', 'editor_name', 'year_month',
                    'adds', 'adds_surv_48h', 'adds_persistent', 'adds_stopword_count', 
                    'dels', 'dels_surv_48h', 'dels_persistent', 'dels_stopword_count', 
                    'reins', 'reins_surv_48h', 'reins_persistent', 'reins_stopword_count',
                    'conflict', 'elegibles', 'conflicts', 'revisions',)

    readonly_fields = ('id', 'page_id', 'editor_id', 'editor_name', 'year_month',
                    'adds', 'adds_surv_48h', 'adds_persistent', 'adds_stopword_count', 
                    'dels', 'dels_surv_48h', 'dels_persistent', 'dels_stopword_count', 
                    'reins', 'reins_surv_48h', 'reins_persistent', 'reins_stopword_count',
                    'conflict', 'elegibles', 'conflicts', 'revisions',)
    search_fields = ('editor_id', 'page_id', )
    date_hierarchy = 'year_month'

    def page_id_(self, obj):
        return '<a href="https://{}.wikipedia.org/w/api.php?action=query&prop=info&inprop=url&format=json&' \
               'pageids={}">{}</a>'.format(obj.language, obj.page_id, obj.page_id)
    page_id_.short_description = 'Page ID'
    page_id_.allow_tags = True

    def editor_id_(self, obj):
        return '<a href="https://{}.wikipedia.org/w/api.php?action=query&list=users&format=json&ususerids={}">' \
               '{}</a>'.format(obj.language, obj.editor_id, obj.editor_id)
    editor_id_.short_description = 'Editor ID'
    editor_id_.allow_tags = True


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


class EditorDataEsNotIndexedAdmin(EditorDataNotIndexedAdmin):
    pass


class EditorDataEsAdmin(EditorDataIndexedAdmin):
    pass


class EditorDataTrNotIndexedAdmin(EditorDataNotIndexedAdmin):
    pass


class EditorDataTrAdmin(EditorDataIndexedAdmin):
    pass

admin.site.register(EditorDataEnNotIndexed, EditorDataEnNotIndexedAdmin)
admin.site.register(EditorDataEn, EditorDataEnAdmin)
admin.site.register(EditorDataEuNotIndexed, EditorDataEuNotIndexedAdmin)
admin.site.register(EditorDataEu, EditorDataEuAdmin)
admin.site.register(EditorDataDeNotIndexed, EditorDataDeNotIndexedAdmin)
admin.site.register(EditorDataDe, EditorDataDeAdmin)
admin.site.register(EditorDataEsNotIndexed, EditorDataEsNotIndexedAdmin)
admin.site.register(EditorDataEs, EditorDataEsAdmin)
admin.site.register(EditorDataTrNotIndexed, EditorDataTrNotIndexedAdmin)
admin.site.register(EditorDataTr, EditorDataTrAdmin)
