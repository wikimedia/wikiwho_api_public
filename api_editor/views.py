# from django.shortcuts import render

# from django.http import HttpResponse


# def index(request):
#     return HttpResponse("Hello, world. You're at the editor index.")


from rest_framework.views import APIView
from simplejson import JSONDecodeError

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework import permissions, status, authentication
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from django.utils.translation import get_language


from rest_framework_tracking.mixins import LoggingMixin
from api_editor.swagger_data import custom_data

from .models import EditorDataEn


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
        data['basePath'] = '/{}{}'.format(get_language(),
                                          custom_data['basePath'])

        return data


@api_view()
@renderer_classes([MyOpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request, version):
    generator = SchemaGenerator(
        title='WikiWho Editor API', urlconf='api_editor.urls')
    schema = generator.get_schema(request=request)
    # print(type(schema), schema)
    return Response(schema)


class EditorApiView(LoggingMixin, APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    authentication_classes = (
        authentication.SessionAuthentication, authentication.BasicAuthentication)
    renderer_classes = [JSONRenderer]  # to disable browsable api

    def get(self, request, version, page_id):  # , page_id=None):
        response = {}

        # there is a bug related to the page_id
        self.page_id = int(page_id)

        cols = ['year_month', 'editor_id',
                'adds', 'adds_surv_48h', 'adds_persistent', 'adds_stopword_count',
                'dels', 'dels_surv_48h', 'dels_persistent', 'dels_stopword_count',
                'reins', 'reins_surv_48h', 'reins_persistent', 'reins_stopword_count']

        response['success'] = True
        response['page_id'] = self.page_id
        response['editions_columns'] = cols
        response['editions_types'] = ['string', 'integer',
                'integer', 'integer', 'integer', 'integer',
                'integer', 'integer', 'integer', 'integer',
                'integer', 'integer', 'integer', 'integer']
        response['editions_formats'] = ['date', 'int64',
                'int64', 'int64', 'int64', 'int64',
                'int64', 'int64', 'int64', 'int64',
                'int64', 'int64', 'int64', 'int64']

        response['editions_data'] = EditorDataEn.objects.values(
            *cols).filter(page_id=self.page_id).values_list(*cols)

        return Response(response, status=status.HTTP_200_OK)
