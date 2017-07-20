# from django.views.generic.base import TemplateView
from django.http import JsonResponse

from .handler import WhoColorHandler, WhoColorException


# class WhoColorBaseView(TemplateView):
#     template_name = "whocolor/base.html"
#
#
# # TODO LoggingMixin
# class WhoColorDetailView(TemplateView):
#     template_name = "whocolor/detail.html"
#
#     def get_context_data(self, **kwargs):
#         context = super(WhoColorDetailView, self).get_context_data(**kwargs)
#         page_id = kwargs.get('page_id')
#         page_title = kwargs.get('page_title')
#         rev_id = kwargs.get('rev_id')
#         with WhoColorHandler(page_id, page_title, rev_id) as wc_handler:
#             context['extended_html'] = wc_handler.handle()
#         return context


def whocolor_api_view(request, version, page_title, rev_id=None):
    data = {}
    try:
        with WhoColorHandler(page_title=page_title, revision_id=rev_id) as wc_handler:
            extended_html, present_editors = wc_handler.handle()
            data['extended_html'] = extended_html
            data['present_editors'] = present_editors
            rev_id = wc_handler.rev_id
            # data['tokens'] = wc_handler.tokens
            # data['tokencount'] = len(wc_handler.tokens)
            # data['authors'] = []
            # data['revisions'] = []
    except WhoColorException as e:
        if e.code in []:  # TODO
            data['info'] = e.message
        else:
            data['error'] = e.message
        data['success'] = False
    else:
        data['success'] = True
    data['rev_id'] = rev_id
    return JsonResponse(data)
