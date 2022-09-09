from rest_framework.views import APIView
from simplejson import JSONDecodeError

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework import permissions, status, authentication
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from django.utils.translation import get_language

from api.tasks import process_article_user
from api.messages import MESSAGES

from rest_framework_tracking.mixins import LoggingMixin
from .handler import WhoColorHandler, WhoColorException
from .swagger_data import custom_data


class MyOpenAPIRenderer(OpenAPIRenderer):
    """
    Custom OpenAPIRenderer to update field types and descriptions.
    """
    def get_customizations(self):
        """
        Adds settings, overrides, etc. to the specification.
        """
        data = super(MyOpenAPIRenderer, self).get_customizations()
        # print(type(data), data)
        data['paths'] = custom_data['paths']
        data['info'] = custom_data['info']
        data['basePath'] = '/{}{}'.format(get_language(), custom_data['basePath'])
        # data['externalDocs'] = custom_data['externalDocs']
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print(type(data))
        # pp.pprint(data)
        return data


@api_view()
@renderer_classes([MyOpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request, version):
    generator = SchemaGenerator(title='WhoColor API', urlconf='whocolor.urls')
    schema = generator.get_schema(request=request)
    # print(type(schema), schema)
    return Response(schema)


class WhoColorApiView(LoggingMixin, APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    renderer_classes = [JSONRenderer]  # to disable browsable api

    def __init__(self, page_id=None):
        super(WhoColorApiView, self).__init__()
        self.page_id = page_id

    def get(self, request, version, page_title, rev_id=None):
        # This is a workaround for titles that have a `/` in them.
        # You can pass rev_id 0 and it will treat it the same way as if no rev_id was passed.
        # This is necessary for page titles like "Post-9/11" where — even when encoded as "%2f" —
        # the slash in the title causes the urlpattern to mis-match the title as a truncated title
        # followed by a rev_id.
        # For example, /en/whocolor/v1.0.0-beta/Post-9%2f11/0/?origin=* will work for "Post-9/11".
        if (rev_id == '0'):
            rev_id = None

        response = {}
        try:
            language = get_language()
            with WhoColorHandler(page_title=page_title, revision_id=rev_id, language=language) as wc_handler:
                extended_html, present_editors, whocolor_data = wc_handler.handle()
                self.page_id = wc_handler.page_id
                if extended_html is None and present_editors is None:
                    process_article_user.delay(language, wc_handler.page_title,
                                               wc_handler.page_id, wc_handler.rev_id)
                    response['info'] = 'Requested data is not currently available in WikiWho database. ' \
                                       'It will be available soon.'
                    response['success'] = False
                elif extended_html is False and present_editors is False:
                    response['info'] = 'Requested revision ({}) is detected as vandalism by WikiWho.'.\
                                       format(wc_handler.rev_id)
                    response['success'] = False
                else:
                    response['extended_html'] = extended_html
                    response['present_editors'] = present_editors
                    response.update(whocolor_data)
                    response['success'] = True
                status_ = status.HTTP_200_OK
                rev_id = wc_handler.rev_id
        except WhoColorException as e:
            response['error'] = e.message
            response['success'] = False
            if e.code in ['11']:
                # WP errors
                status_ = status.HTTP_503_SERVICE_UNAVAILABLE
            else:
                status_ = status.HTTP_400_BAD_REQUEST
        except JSONDecodeError as e:
            response['error'] = MESSAGES['wp_http_error'][0]
            response['success'] = False
            status_ = status.HTTP_503_SERVICE_UNAVAILABLE
        response['rev_id'] = rev_id
        response['page_title'] = page_title
        return Response(response, status=status_)
