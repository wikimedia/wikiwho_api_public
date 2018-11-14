# from django.conf.urls import url

# from . import views

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]


from django.conf.urls import url

from .views import schema_view, EditorApiView, EditorDataApiView

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),
    # url(r'^(?P<editor_id>.+)/(?P<page_id>[0-9]+)/$',
    #     EditorApiView.as_view(), name='wc_page_title_rev_id'),
    url(r'^(?P<page_id>([0-9]+))/$',
        EditorApiView.as_view(), name='apieditor_page_id'),
    url(r'^editor_data/(?P<page_id>([0-9]+))/$',
        EditorDataApiView.as_view(), name='apieditordata_page_id'),
]
