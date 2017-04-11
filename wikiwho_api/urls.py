"""wikiwho_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns, static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap

from base.views import clear_cache, clear_sessions
from base.sitemaps import BaseStaticViewSitemap, ApiStaticViewSitemap
from api.views import ApiRedirectView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^admin/clear_cache', clear_cache, name='clear_cache'),
    url(r'^admin/clear_sessions', clear_sessions, name='clear_sessions'),
    url(r'^api/(?P<version>(v1.0.0-beta|v1.0.0))/', include('api.urls', namespace='api')),
    url(r'^api/', ApiRedirectView.as_view()),
    # url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^account/', include('account_app.urls', namespace='account')),
    url(r'^contact/$', TemplateView.as_view(template_name='contact/contact.html'), name='contact'),
    # url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^$', TemplateView.as_view(template_name='home/home.html'), name='home'),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': {'api': ApiStaticViewSitemap, 'base': BaseStaticViewSitemap}},
        name='django.contrib.sitemaps.views.sitemap')]


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
