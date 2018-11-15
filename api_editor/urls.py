# from django.conf.urls import url

# from . import views

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]


from django.conf.urls import url

from .views import schema_view, EditorApiView

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),

    url(r'^editor/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_standard_api_format'}),
        name='editor_editions'),
    url(r'^page/(?P<page_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_standard_api_format'}),
        name='editors_editions_by_page'),
    url(r'^page/editor/(?P<page_id>([0-9]+))/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_standard_api_format'}),
        name='editor_editions_by_page'),

    url(r'^as_table/editor/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_matrix_api_format'}),
         name='data_editor_editions'),
    url(r'^as_table/page/(?P<page_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_matrix_api_format'}),
         name='data_editors_editions_by_page'),
    url(r'^as_table/page/editor/(?P<page_id>([0-9]+))/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(actions={'get': 'get_matrix_api_format'}),
         name='data_editor_editions_by_page'),

]