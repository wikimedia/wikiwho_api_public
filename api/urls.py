from django.conf.urls import url

from .views import WikiwhoApiView, schema_view

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),
    url(r'^content/(?P<article_name>.+)/(?P<start_revision_id>[0-9]+)/(?P<end_revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_slice'}), name='slice'),
    url(r'^content/(?P<article_name>.+)/(?P<revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_revision'}), name='article_name'),
    url(r'^content/(?P<article_name>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_by_name'}), name='article_name'),
    # TODO finish commented urls
    # url(r'^content/page_id/(?P<revision_id>[0-9]+)/$',
    #     WikiwhoApiView.as_view(actions={'get': 'get_article_by_page_id'}), name='page_id'),
    # url(r'^content/revision_id/(?P<revision_id>[0-9]+)/$',
    #     WikiwhoApiView.as_view(actions={'get': 'get_revision'}), name='rev_id'),
    url(r'^deleted/(?P<article_name>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_deleted_content_by_name'}), name='deleted_article_name'),
    # url(r'^deleted/(?P<page_id>.+)/$',
    #     WikiwhoApiView.as_view(actions={'get': 'get_deleted_content_by_page_id'}), name='deleted_page_id'),
    url(r'^revision_ids/(?P<article_name>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_revision_ids_by_name'}), name='ids_article_name'),
    # url(r'^revision_ids/(?P<page_id>.+)/$',
    #     WikiwhoApiView.as_view(actions={'get': 'get_revision_ids_by_page_id'}), name='ids_article_page_id'),
]
