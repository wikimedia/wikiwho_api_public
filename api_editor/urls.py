# from django.conf.urls import url

# from . import views

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]


from django.conf.urls import url

from .views import schema_view, EditorApiView, EditorDataApiView

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),

    url(r'^editor/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(), name='editor_editions'),
    url(r'^page/(?P<page_id>([0-9]+))/$',
        EditorApiView.as_view(), name='editors_editions_by_page'),
    url(r'^page/editor/(?P<page_id>([0-9]+))/(?P<editor_id>([0-9]+))/$',
        EditorApiView.as_view(), name='editor_editions_by_page'),

    url(r'^editor_data/(?P<page_id>([0-9]+))/$',
        EditorDataApiView.as_view(), name='apieditordata_page_id'),

]
