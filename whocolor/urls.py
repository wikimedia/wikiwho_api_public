from django.conf.urls import url

from .views import whocolor_api_view  # , WhoColorBaseView, WhoColorDetailView

urlpatterns = [
    # url(r'^$', WhoColorBaseView.as_view(), name='home'),
    # url(r'^page_id/(?P<page_id>[0-9]+)/(?P<rev_id>[0-9]+)/$',
    #     WhoColorDetailView.as_view(), name='page_id'),
    # url(r'^page_title/(?P<page_title>.+)/(?P<rev_id>[0-9]+)/$',
    #     WhoColorDetailView.as_view(), name='page_title'),
    url(r'^(?P<page_title>.+)/(?P<rev_id>[0-9]+)/$',
        whocolor_api_view, name='api'),
    url(r'^(?P<page_title>.+)/$',
        whocolor_api_view, name='api'),
]
