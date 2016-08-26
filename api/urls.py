from django.conf.urls import url

from .views import WikiwhoApiView, schema_view

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),
    url(r'^authorship/(?P<article_name>.+)/(?P<start_revision_id>[0-9]+)/(?P<end_revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_slice'}), name='slice'),
    url(r'^authorship/(?P<article_name>.+)/(?P<revision_id>[0-9]+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_revision'}), name='article_name'),
    url(r'^authorship/(?P<article_name>.+)/$',
        WikiwhoApiView.as_view(actions={'get': 'get_article_by_name'}), name='article_name'),
    # url(r'^authorship/(?P<revision_id>[0-9]+)/$',
    #     WikiwhoApiView.as_view(actions={'get': 'get_article_by_revision'}), name='rev_id'),
]
