from simplejson import JSONDecodeError
# import time

from rest_framework.decorators import detail_route, api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework import permissions, status, authentication, throttling
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.schemas import SchemaGenerator  # , as_query_fields
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
# from rest_framework_extensions.cache.decorators import cache_response, CacheResponse
# from rest_framework.compat import coreapi, urlparse

# from django.utils.translation import get_language
from django.conf import settings
# from django.core.signals import request_started, request_finished
# from django.http import HttpResponse
from wikiwho.models import Revision, Article
from .handler import WPHandler, WPHandlerException

# TODO add descriptions
query_params = [
    {'description': 'Add some description', 'in': 'query', 'name': 'rev_id', 'required': True, 'type': 'boolean'},  # 'default': 'false',
    {'description': 'Add some description', 'in': 'query', 'name': 'editor', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'token_id', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'inbound', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'outbound', 'required': True, 'type': 'boolean'}
]

allowed_params = {
    'deleted_content': ['rev_id', 'editor', 'token_id', 'inbound', 'outbound', 'threshold'],
    'content': ['rev_id', 'editor', 'token_id', 'inbound', 'outbound'],
    'rev_ids': ['editor', 'timestamp']
}

custom_data = {
    # 'info': {'title': 'WikiWho API', 'version': ''},
    'paths':
        {'/content/{article_name}/':
             {'get': {'description': '# Some description \n **with** *markdown* \n\n '
                                     '[Markdown Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)',
                      'parameters': [{'description': 'Add some description',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': {'200': {'description': ''}},
                      'tags': ['Revision content'],
                      'summary': 'Get content of last revision of article'
                      }
              },
         '/content/{article_name}/{revision_id}/':
             {'get': {'description': '',
                      'parameters': [{'description': '',
                                      'in': 'path',
                                      'name': 'revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': '',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': {'200': {'description': ''}},
                      'tags': ['Revision content'],
                      'summary': 'Get content of given revision of article'
                      }
              },
         '/content/{article_name}/{start_revision_id}/{end_revision_id}/':
             {'get': {'description': '',
                      'parameters': [{'description': '',
                                      'in': 'path',
                                      'name': 'end_revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': '',
                                      'in': 'path',
                                      'name': 'start_revision_id',
                                      'required': True,
                                      'type': 'integer'},
                                     {'description': '',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] + query_params,
                      'responses': {'200': {'description': ''}},
                      'tags': ['Revision content'],
                      'summary': 'Get content of given revisions of article'
                      }
              },
         '/deleted/{article_name}/':
             {'get': {'description': '',
                      'parameters': [{'description': 'Add some description',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     {'description': 'Default is {}'.format(settings.DELETED_CONTENT_THRESHOLD_LIMIT),
                                      'in': 'query',
                                      'name': 'threshold',
                                      'required': False,
                                      'type': 'integer'},
                                     ] + query_params,
                      'responses': {'200': {'description': ''}},
                      'tags': ['Deleted content'],
                      'summary': 'Get deleted content of last revision of article'
                      }
              },
         '/revision_ids/{article_name}/':
             {'get': {'description': '',
                      'parameters': [{'description': 'Add some description',
                                      'in': 'path',
                                      'name': 'article_name',
                                      'required': True,
                                      'type': 'string'},
                                     ] +
                                    [
                                        query_params[1],
                                        {'description': 'Add some description',
                                         'in': 'query',
                                         'name': 'timestamp',
                                         'required': True,
                                         'type': 'boolean'}
                                    ],
                      'responses': {'200': {'description': ''}},
                      'tags': ['Revision ids'],
                      'summary': 'Get all revision ids of article'
                      }
              },
         },
}


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
        # TODO update
        data['paths'] = custom_data['paths']
        version = '1.0.0-beta'
        data['info'] = {
            'version': version,
            'description': 'A short description of the application. GFM syntax can be used for rich text '
                           'representation. \n\nSpecification: http://swagger.io/specification \n\n'
                           'Example api: http://petstore.swagger.io/',
            'contact': {
                'name': 'GESIS - Leibniz Institute for the Social Sciences',
                # 'email': 'kenan.erdogan@gesis.org',
                'url': 'http://www.gesis.org/en/institute/gesis-scientific-departments/computational-social-science/'},
        }
        data['basePath'] = '/api/v{}'.format(version)
        # print(type(data), data)
        return data


@api_view()
@renderer_classes([MyOpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request, version):
    generator = SchemaGenerator(title='WikiWho API', urlconf='api.urls')
    schema = generator.get_schema(request=request)
    # print(type(schema), schema)
    return Response(schema)


class BurstRateThrottle(throttling.UserRateThrottle):
    """
    Limit authenticated users when they burst the api. Check DEFAULT_THROTTLE_RATES settings: 100/min
    """
    scope = 'burst'


class WikiwhoView(object):

    def __init__(self, article=None):
        self.article = article

    @staticmethod
    def _set_default_type_parameters(query_type, parameters):
        if query_type == 'content' or query_type == 'deleted_content':
            parameters.append('str')
        if query_type == 'rev_ids':
            parameters.append('rev_id')

    def get_parameters(self, query_type):
        """
        :return: Full parameters with default values.
        """
        parameters = []
        self._set_default_type_parameters(query_type, parameters)
        for parameter in query_params:
            if parameter['name'] in allowed_params[query_type]:
                parameters.append(parameter['name'])
        if 'timestamp' in allowed_params[query_type]:
            parameters.append('timestamp')
        if 'threshold' in allowed_params[query_type]:
            parameters.append(settings.DELETED_CONTENT_THRESHOLD_LIMIT)
        return parameters

    def get_revision_json(self, wp, parameters, only_last_valid_revision=False, minimal=False, from_db=False, with_token_ids=True):
        if not from_db:
            if minimal:
                return wp.wikiwho.get_revision_min_json(wp.revision_ids)
            else:
                return wp.wikiwho.get_revision_json(wp.revision_ids, parameters)

        # TODO minimal
        revision_ids = wp.revision_ids
        json_data = dict()
        json_data["article"] = wp.saved_article_title
        json_data["success"] = True
        json_data["message"] = None

        if only_last_valid_revision:
            data = self.article.to_json(parameters, content=True, last_rev_id=None, ordered=True)
            json_data["revisions"] = [data] if data else []
        else:
            revisions = []
            db_revision_ids = []
            if len(revision_ids) > 1:
                # FIXME revision ids are not ordered
                filter_ = {'id__range': revision_ids}
                order_fields = ['timestamp']
            else:
                filter_ = {'id': revision_ids[0]}
                order_fields = []
            for revision in Revision.objects.filter(**filter_).order_by(*order_fields):
                revisions.append({revision.id: revision.to_json(parameters, content=True, ordered=True, with_token_ids=with_token_ids)})
                db_revision_ids.append(revision.id)

            for rev_id in revision_ids:
                if rev_id not in db_revision_ids:
                    return {'Error': 'Revision ID ({}) does not exist or is spam or deleted!'.format(rev_id)}

            json_data["revisions"] = sorted(revisions, key=lambda x: sorted(x.keys())) \
                if len(revision_ids) > 1 else revisions

        # import json
        # with open('tmp_pickles/{}_db.json'.format(self.article.title), 'w') as f:
        #     f.write(json.dumps(json_data, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return json_data

    def get_deleted_tokens(self, wp, parameters, minimal=False, last_rev_id=None, from_db=False):
        # TODO get deleted content for a specific revision
        if not from_db:
            return wp.wikiwho.get_deleted_tokens(parameters)
        if not self.article:
            self.article = Article.objects.get(id=wp.page_id)
        json_data = dict()
        json_data["article"] = self.article.title
        json_data["success"] = True
        json_data["message"] = None
        threshold = parameters[-1]
        json_data["threshold"] = threshold

        # TODO use latest_revision_id from handler?
        data = self.article.to_json(parameters, deleted=True, threshold=threshold, last_rev_id=last_rev_id, ordered=False)
        json_data.update(data)
        # OR TODO which way is faster?
        # revision = self.article.revisions.select_related('article').order_by('timestamp').last()
        # json_data["deleted_tokens"] = revision.to_json(parameters, deleted=True, threshold=threshold)
        # json_data["revision_id"] = revision.id

        # import json
        # with open('tmp_pickles/{}_deleted_tokens_db.json'.format(self.article.title), 'w') as f:
        #     f.write(json.dumps(json_data, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return json_data

    def get_revision_ids(self, wp, parameters=None, from_db=False):
        if not from_db:
            return wp.wikiwho.get_revision_ids(parameters)
        json_data = dict()
        json_data["article"] = wp.saved_article_title
        json_data["success"] = True
        json_data["message"] = None
        annotate_dict, values_list = Revision.get_annotate_and_values(parameters, ids=True)
        order_fields = ['timestamp']
        json_data["revisions"] = list(Revision.objects.filter(article_id=wp.page_id).order_by(*order_fields).
                                      annotate(**annotate_dict).values(*values_list))
        # """
        # EXPLAIN SELECT "wikiwho_revision"."editor",
        #                "wikiwho_revision"."timestamp",
        #                "wikiwho_revision"."id" AS "rev_id"
        #         FROM "wikiwho_revision"
        #         WHERE "wikiwho_revision"."article_id" = 662
        #         ORDER BY "wikiwho_revision"."timestamp" ASC
        # """
        # json_data["revisions"] = list(self.revisions.order_by(*order_fields).annotate(**annotate_dict).values_list(*values_list, flat=True))
        return json_data


class WikiwhoApiView(WikiwhoView, ViewSet):
    """
    import requests
    session = requests.session()

    from requests.auth import HTTPBasicAuth
    r1 = session.get(url, auth=HTTPBasicAuth('username', 'password'))
    OR
    session.auth = ('username', 'pass')

    r2 = session.get('http://127.0.0.1:8000/api/v1.0.0-beta/content/thomas_Bellut/?rev_id=true&author=true&token_id=true&inbound=true&outbound=true')
    r2.json()
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # TODO http://www.django-rest-framework.org/topics/third-party-resources/#authentication to account activation,
    # password reset ...
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # authentication_classes = (authentication.TokenAuthentication, )
    # TODO Note: If you use BasicAuthentication in production you must ensure that your API is only available over https.
    # You should also ensure that your API clients will always re-request the username and password at login, and will
    # never store those details to persistent storage.
    throttle_classes = (throttling.UserRateThrottle, throttling.AnonRateThrottle, BurstRateThrottle)
    # serializer_class = WikiWhoSerializer
    # filter_fields = ('query_option_1', 'query_option_2',)
    # query_fields = ('rev_id', 'editor', 'token_id', )
    renderer_classes = [JSONRenderer]  # to disable browsable api
    # article = None

    def get_parameters(self, query_type):
        all_parameters = super(WikiwhoApiView, self).get_parameters(query_type)
        parameters = []
        self._set_default_type_parameters(query_type, parameters)
        for parameter in all_parameters:
            if type(parameter) == int:
                threshold = int(self.request.GET.get('threshold', settings.DELETED_CONTENT_THRESHOLD_LIMIT))
                parameters.append(0 if threshold < 0 else threshold)
            elif self.request.GET.get(parameter) == 'true':
                parameters.append(parameter)
        return parameters

    def get_response(self, article_name, parameters, revision_ids=list(), deleted=False, ids=False):
        # if not parameters:
        #     return Response({'Error': 'At least one query parameter should be selected.'},
        #                     status=status.HTTP_400_BAD_REQUEST)

        # global handler_time
        # handler_start = time.time()
        try:
            with WPHandler(article_name) as wp:
                wp.handle(revision_ids, 'json')
        except WPHandlerException as e:
            response = {'Error': e.message}
            status_ = status.HTTP_400_BAD_REQUEST
        except JSONDecodeError as e:
            response = {'Error': 'HTTP Response error from Wikipedia! Please try again later.'}
            status_ = status.HTTP_400_BAD_REQUEST
        else:
            if deleted:
                response = self.get_deleted_tokens(wp, parameters)
                status_ = status.HTTP_200_OK
            elif ids:
                response = self.get_revision_ids(wp, parameters)
                status_ = status.HTTP_200_OK
            else:
                response = self.get_revision_json(wp, parameters, from_db=False)
                if 'Error' in response:
                    status_ = status.HTTP_400_BAD_REQUEST
                else:
                    status_ = status.HTTP_200_OK
        # handler_time = time.time() - handler_start
        # return HttpResponse(json.dumps(response), content_type='application/json; charset=utf-8')
        return Response(response, status=status_)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_slice(self, request, version, article_name, start_revision_id, end_revision_id):
        # TODO do we need pagination with page=5?
        # maybe this is helpful: http://www.django-rest-framework.org/api-guide/pagination/
        start_revision_id = int(start_revision_id)
        end_revision_id = int(end_revision_id)
        if start_revision_id >= end_revision_id:
            return Response({'Error': 'Second revision id has to be larger than first revision id!'},
                            status=status.HTTP_400_BAD_REQUEST)
        parameters = self.get_parameters('content')
        return self.get_response(article_name, parameters, [start_revision_id, end_revision_id])

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_article_revision(self, request, version, article_name, revision_id):
        parameters = self.get_parameters('content')
        return self.get_response(article_name, parameters, [int(revision_id)])

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_article_by_name(self, request, version, article_name):
        parameters = self.get_parameters('content')
        return self.get_response(article_name, parameters)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_deleted_content_by_name(self, request, version, article_name):
        parameters = self.get_parameters('deleted_content')
        return self.get_response(article_name, parameters, deleted=True)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_revision_ids_by_name(self, request, version, article_name):
        parameters = self.get_parameters('rev_ids')
        return self.get_response(article_name, parameters, ids=True)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    # def get_article_by_revision(self, request, revision_id):
    #     return Response({'test': 'get_article_by_revision'})

    # def dispatch(self, request, *args, **kwargs):
    #     global dispatch_time
    #     global render_time
    #
    #     dispatch_start = time.time()
    #     ret = super(WikiwhoApiView, self).dispatch(request, *args, **kwargs)
    #
    #     render_start = time.time()
    #     # ret.render()
    #     render_time = time.time() - render_start
    #
    #     dispatch_time = time.time() - dispatch_start
    #     return ret
    #
    # def started(sender, **kwargs):
    #     global started
    #     started = time.time()
    #
    # def finished(sender, **kwargs):
    #     total = time.time() - started
    #     api_view_time = dispatch_time - (render_time + handler_time)
    #     request_response_time = total - dispatch_time
    #
    #     # print ("Database lookup               | %.4fs" % db_time)
    #     # print ("Serialization                 | %.4fs" % serializer_time)
    #     print ("Django request/response       | %.4fs" % request_response_time)
    #     print ("API view                      | %.4fs" % api_view_time)
    #     print ("Response rendering            | %.4fs" % render_time)
    #     print ("handler_time                  | %.4fs" % handler_time)
    #     print ("total                         | %.4fs" % total)
    #
    # request_started.connect(started)
    # request_finished.connect(finished)


# class MySchemaGenerator(SchemaGenerator):
#     """
#     Custom SchemaGenerator to enable adding query fields.
#     """
#     def get_query_fields(self, view):
#         """
#         Return query fields of given views.
#         """
#         query_fields = getattr(view, 'query_fields', [])
#         fields = as_query_fields(query_fields)
#         return fields
#
#     def get_link(self, path, method, callback):
#         """
#         Return a `coreapi.Link` instance for the given endpoint.
#         """
#         view = callback.cls()
#
#         fields = self.get_path_fields(path, method, callback, view)
#         fields += self.get_serializer_fields(path, method, callback, view)
#         fields += self.get_pagination_fields(path, method, callback, view)
#         fields += self.get_filter_fields(path, method, callback, view)
#         # add query fields
#         fields += self.get_query_fields(view)
#
#         if fields and any([field.location in ('form', 'body') for field in fields]):
#             encoding = self.get_encoding(path, method, callback, view)
#         else:
#             encoding = None
#
#         return coreapi.Link(
#             url=urlparse.urljoin(self.url, path),
#             action=method.lower(),
#             encoding=encoding,
#             fields=fields
#         )
