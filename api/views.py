import hashlib
import json
from simplejson import JSONDecodeError
# import time

from rest_framework.decorators import detail_route, api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework import permissions, status, authentication, throttling
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.schemas import SchemaGenerator  # , as_query_fields
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from rest_framework_extensions.cache.decorators import cache_response, CacheResponse
# from rest_framework.compat import coreapi, urlparse

from django.utils.translation import get_language
from django.conf import settings
# from django.core.signals import request_started, request_finished
# from django.http import HttpResponse

from .handler import WPHandler, WPHandlerException

# TODO add descriptions
query_params = [
    {'description': 'Add some description', 'in': 'query', 'name': 'rev_id', 'required': True, 'type': 'boolean'},  # 'default': 'false',
    {'description': 'Add some description', 'in': 'query', 'name': 'author', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'token_id', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'inbound', 'required': True, 'type': 'boolean'},
    {'description': 'Add some description', 'in': 'query', 'name': 'outbound', 'required': True, 'type': 'boolean'}
]

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

    def get_parameters(self):
        """
        :return: Full parameters with default values.
        """
        parameters = []
        for parameter in query_params:
            parameters.append(parameter['name'])
        parameters.append(settings.DELETED_CONTENT_THRESHOLD_LIMIT)
        return parameters

    def get_revision_json(self, revision_ids, parameters, only_last_valid_revision=False, minimal=False):
        json_data = dict()
        json_data["article"] = self.article.title
        if not minimal:
            json_data["success"] = True
            json_data["message"] = None

        if only_last_valid_revision:
            json_data["revisions"] = [self.article.to_json(parameters, content=True)]
        else:
            revisions = []
            db_revision_ids = []
            if len(revision_ids) > 1:
                filter_ = {'id__range': revision_ids}
            else:
                filter_ = {'id': revision_ids[0]}
            for revision in self.article.revisions.filter(**filter_).order_by('timestamp'):
                revisions.append({revision.id: revision.to_json(parameters, content=True)})
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

    def get_deleted_tokens(self, parameters, minimal=False):
        json_data = dict()
        json_data["article"] = self.article.title
        if not minimal:
            json_data["success"] = True
            json_data["message"] = None
        threshold = parameters[-1]
        json_data["threshold"] = threshold

        # TODO use latest_revision_id from handler?
        data = self.article.to_json(parameters, deleted=True, threshold=threshold, last_rev_id=None)
        json_data.update(data)
        # OR TODO which way is faster?
        # revision = self.article.revisions.select_related('article').order_by('timestamp').last()
        # json_data["deleted_tokens"] = revision.to_json(parameters, deleted=True, threshold=threshold)
        # json_data["revision_id"] = revision.id

        # import json
        # with open('tmp_pickles/{}_deleted_tokens_db.json'.format(self.article.title), 'w') as f:
        #     f.write(json.dumps(json_data, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return json_data

    def get_revision_ids(self, minimal=False):
        json_data = dict()
        json_data["article"] = self.article.title
        if not minimal:
            json_data["success"] = True
            json_data["message"] = None
        json_data["revisions"] = list(self.article.revisions.order_by('timestamp').values_list('id', flat=True))
        return json_data


class WikiwhoApiView(WikiwhoView, ViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # TODO http://www.django-rest-framework.org/topics/third-party-resources/#authentication to account activation,
    # password reset ...
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    throttle_classes = (throttling.UserRateThrottle, throttling.AnonRateThrottle, BurstRateThrottle)
    # serializer_class = WikiWhoSerializer
    # filter_fields = ('query_option_1', 'query_option_2',)
    # query_fields = ('rev_id', 'author', 'token_id', )
    renderer_classes = [JSONRenderer]  # to disable browsable api
    article = None

    def get_parameters(self):
        parameters = []
        for parameter in query_params:
            if self.request.GET.get(parameter['name']) == 'true':
                parameters.append(parameter['name'])
        threshold = int(self.request.GET.get('threshold', settings.DELETED_CONTENT_THRESHOLD_LIMIT))
        threshold = 0 if threshold < 0 else threshold
        parameters.append(threshold)
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
            self.article = wp.article_obj
            if deleted:
                response = self.get_deleted_tokens(parameters)
                # response_ = wp.wikiwho.get_deleted_tokens(parameters)
                # assert response == response_
                status_ = status.HTTP_200_OK
            elif ids:
                response = self.get_revision_ids()
                # response_ = wp.wikiwho.get_revision_ids()
                # assert list(response["revisions"]) == response_["revisions"]
                status_ = status.HTTP_200_OK
            else:
                response = self.get_revision_json(wp.revision_ids, parameters)
                # response_ = wp.wikiwho.get_revision_json(wp.revision_ids, parameters)
                # assert response == response_
                if 'Error' in response:
                    status_ = status.HTTP_400_BAD_REQUEST
                else:
                    status_ = status.HTTP_200_OK
        # handler_time = time.time() - handler_start
        # return HttpResponse(json.dumps(response), content_type='application/json; charset=utf-8')
        return Response(response, status=status_)

    # TODO http://www.django-rest-framework.org/api-guide/renderers/
    @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_slice(self, request, version, article_name, start_revision_id, end_revision_id):
        # TODO do we need pagination with page=5?
        start_revision_id = int(start_revision_id)
        end_revision_id = int(end_revision_id)
        if start_revision_id >= end_revision_id:
            return Response({'Error': 'Second revision id has to be larger than first revision id!'},
                            status=status.HTTP_400_BAD_REQUEST)
        parameters = self.get_parameters()
        return self.get_response(article_name, parameters, [start_revision_id, end_revision_id])

    @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_article_revision(self, request, version, article_name, revision_id):
        # TODO cache this if only rev id is the last rev id
        parameters = self.get_parameters()
        return self.get_response(article_name, parameters, [int(revision_id)])

    # TODO update to cache only specific articles from rest_framework_extensions.cache.decorators import CacheResponse
    # @cache_response(key_func='calculate_cache_key')
    @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_article_by_name(self, request, version, article_name):
        # TODO when models are created, delete cache.delete(this_key) if last_rev_id is changed or obj is deleted!
        parameters = self.get_parameters()
        return self.get_response(article_name, parameters)

    def calculate_cache_key(self, view_instance, view_method, request, args, kwargs):
        # FIXME for different query parameters
        l = list(kwargs.values())
        l.remove(request.version)
        l.append(request.accepted_renderer.format)
        l.append(get_language())
        key = hashlib.sha256(json.dumps(l, sort_keys=True).encode('utf-8')).hexdigest()
        return key

    @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_deleted_content_by_name(self, request, version, article_name):
        parameters = self.get_parameters()
        return self.get_response(article_name, parameters, deleted=True)

    @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_revision_ids_by_name(self, request, version, article_name):
        parameters = self.get_parameters()
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
