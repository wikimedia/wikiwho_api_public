from django import template

from api.swagger_data import version_url

register = template.Library()


@register.simple_tag(takes_context=False)
def api_version():
    return version_url
