from django.contrib import sitemaps
from django.urls import reverse

from api.swagger_data import version_url


class BaseStaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    # protocol = 'https'
    i18n = False

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)


class ApiStaticViewSitemap(sitemaps.Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    i18n = False

    def items(self):
        return ['api:swagger']

    def location(self, item):
        return reverse(item, kwargs={'version': version_url})
