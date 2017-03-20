from django.conf.urls import url

from .views import WikiwhoApiView, schema_view

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),
    url(r'^content/page_id/(?P<page_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_by_page_id'}), name='content_page_id'),
    url(r'^content/revision_id/(?P<revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_content_by_revision_id'}), name='content_revision_id'),
    url(r'^content/(?P<article_title>.+)/(?P<start_revision_id>[0-9]+)/(?P<end_revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_slice'}), name='content_slice'),
    url(r'^content/(?P<article_title>.+)/(?P<revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_revision'}), name='content_article_title_rev_id'),
    url(r'^content/(?P<article_title>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_by_name'}), name='content_article_title'),
    url(r'^deleted/page_id/(?P<page_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_deleted_content_by_page_id'}), name='deleted_page_id'),
    url(r'^deleted/(?P<article_title>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_deleted_content_by_name'}), name='deleted_article_title'),
    url(r'^revision_ids/page_id/(?P<page_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_revision_ids_by_page_id'}), name='ids_page_id'),
    url(r'^revision_ids/(?P<article_title>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_revision_ids_by_name'}), name='ids_article_title'),
]
