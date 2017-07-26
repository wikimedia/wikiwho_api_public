from django.conf.urls import url

from .views import schema_view, WhoColorApiView

urlpatterns = [
    url(r'^$', schema_view, name='swagger'),
    url(r'^(?P<page_title>.+)/(?P<rev_id>[0-9]+)/$',
        WhoColorApiView.as_view(), name='page_title_rev_id'),
    url(r'^(?P<page_title>.+)/$',
        WhoColorApiView.as_view(), name='page_title'),
]
