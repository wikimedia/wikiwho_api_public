# from django.shortcuts import render

# from django.http import HttpResponse


# def index(request):
#     return HttpResponse("Hello, world. You're at the editor index.")


from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
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

from .models import EditorDataEn, EditorDataEu, EditorDataDe, EditorDataEs, EditorDataTr


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


class EditorApiView(LoggingMixin, ViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    authentication_classes = (
        authentication.SessionAuthentication, authentication.BasicAuthentication)
    renderer_classes = [JSONRenderer]  # to disable browsable api

    models = {
        'en': EditorDataEn,
        'eu': EditorDataEu,
        'de': EditorDataDe,
        'es': EditorDataEs,
        'tr': EditorDataTr
    }

    columns = ['year_month', 'page_id', 'editor_id',
               'adds', 'adds_surv_48h', 'adds_persistent', 'adds_stopword_count',
               'dels', 'dels_surv_48h', 'dels_persistent', 'dels_stopword_count',
               'reins', 'reins_surv_48h', 'reins_persistent', 'reins_stopword_count']

    def get_queryset(self, request, version, page_id=None, editor_id=None):

        # query parameters
        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')

        qs = EditorApiView.models[get_language()].objects.values(
            *EditorApiView.columns)

        if page_id:
            self.page_id = int(page_id)
            qs = qs.filter(page_id=self.page_id)

        if editor_id:
            self.editor_id = int(editor_id)
            qs = qs.filter(editor_id=self.editor_id)

        if start_date:
            qs = qs.filter(year_month__gte=start_date)

        if end_date:
            qs = qs.filter(year_month__lte=end_date)

        return qs

    def get_standard_api_format(self, request, version, page_id=None, editor_id=None):

        qs = self.get_queryset(request, version, page_id, editor_id)

        response = {
            'editions': list(qs),
            'success': True
        }

        return Response(response, status=status.HTTP_200_OK)

    def get_matrix_api_format(self, request, version, page_id=None, editor_id=None):

        qs = self.get_queryset(request, version, page_id, editor_id)

        cols = EditorApiView.columns

        response = {
            'success': True,
            'editions_columns': cols,
            'editions_types': ['string', 'integer', 'integer',
                               'integer', 'integer', 'integer', 'integer',
                               'integer', 'integer', 'integer', 'integer',
                               'integer', 'integer', 'integer', 'integer'],
            'editions_formats': ['date', 'int64', 'int64',
                                 'int64', 'int64', 'int64', 'int64',
                                 'int64', 'int64', 'int64', 'int64',
                                 'int64', 'int64', 'int64', 'int64'],

            'editions_data': qs.values_list(*cols)
        }

        return Response(response, status=status.HTTP_200_OK)
