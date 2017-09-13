from django import template
from django.urls import resolve, reverse
from django.utils.translation import activate, get_language

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_current_url(context, lang_code):
    request = context['request']
    url_parts = resolve(request.path)
    current_language = get_language()
    try:
        activate(lang_code)
        translated_url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        activate(current_language)
    return translated_url


@register.simple_tag(takes_context=False)
def translate_url(lang_code, view_name, *args):
    current_language = get_language()
    try:
        activate(lang_code)
        translated_url = reverse(view_name, args=args)
    finally:
        activate(current_language)
    return translated_url
