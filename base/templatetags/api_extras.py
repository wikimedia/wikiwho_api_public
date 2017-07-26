from django import template

from api.swagger_data import version_url as ww_version_url
from whocolor.swagger_data import version_url as wc_version_url

register = template.Library()


@register.simple_tag(takes_context=False)
def ww_api_version():
    return ww_version_url


@register.simple_tag(takes_context=False)
def wc_api_version():
    return wc_version_url
