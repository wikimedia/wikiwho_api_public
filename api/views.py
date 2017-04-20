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
from django.views.generic.base import RedirectView
from django.urls import reverse
# from django.core.signals import request_started, request_finished
# from django.http import HttpResponse

from wikiwho.models import Revision, Article
from rest_framework_tracking.mixins import LoggingMixin
from deployment.gunicorn_config import timeout as gunicorn_timeout
from deployment.celery_config import user_task_soft_time_limit
from .handler import WPHandler, WPHandlerException
from .swagger_data import custom_data, allowed_params, query_params, version_url
from .utils import get_revision_timestamp, Timeout
from .tasks import process_article_user


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
        data['basePath'] = custom_data['basePath']
        # data['externalDocs'] = custom_data['externalDocs']
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print(type(data))
        # pp.pprint(data)
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

    def __init__(self, article=None, page_id=None):
        self.article = article
        self.page_id = page_id

    @staticmethod
    def _set_default_type_parameters(query_type, parameters):
        if query_type == 'rev_content' or query_type == 'all_content' or query_type == 'deleted_content':
            parameters.append('str')
        if query_type == 'rev_ids':
            parameters.append('rev_id')

    def get_parameters(self, query_type):
        """
        :return: Full parameters with default values.
        """
        parameters = []
        self._set_default_type_parameters(query_type, parameters)
        allowed_parameters = allowed_params[query_type]
        for parameter in query_params:
            if parameter['name'] in allowed_parameters:
                parameters.append(parameter['name'])
        if 'timestamp' in allowed_parameters:
            parameters.append('timestamp')
        if 'threshold' in allowed_parameters:
            if query_type == 'all_content':
                parameters.append(settings.ALL_CONTENT_THRESHOLD_LIMIT)
            else:
                parameters.append(settings.DELETED_CONTENT_THRESHOLD_LIMIT)
        return parameters

    def get_revision_content(self, wp, parameters, only_last_valid_revision=False, minimal=False,
                             from_db=False, with_token_ids=True):
        if not from_db:
            if minimal:
                return wp.wikiwho.get_revision_min_content(wp.revision_ids)
            else:
                return wp.wikiwho.get_revision_content(wp.revision_ids, parameters)

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

    def get_all_content(self, wp, parameters, minimal=False, from_db=False):
        if not from_db:
            return wp.wikiwho.get_all_content(parameters)
            if minimal:
                # TODO
                return wp.wikiwho.get_all_min_content()
            else:
                return wp.wikiwho.get_all_content(parameters)
        # TODO from_db
        json_data = dict()
        return json_data

    def get_deleted_content(self, wp, parameters, minimal=False, last_rev_id=None, from_db=False):
        # TODO get deleted content for a specific revision
        if not from_db:
            return wp.wikiwho.get_deleted_content(parameters)
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


class WikiwhoApiView(LoggingMixin, WikiwhoView, ViewSet):
    """
    import requests
    session = requests.session()

    from requests.auth import HTTPBasicAuth
    r1 = session.get(url, auth=HTTPBasicAuth('username', 'password'))
    OR
    session.auth = ('username', 'pass')

    r2 = session.get('http://127.0.0.1:8000/api/v1.0.0-beta/rev_content/thomas_Bellut/?origin_rev_id=true&editor=true&token_id=true&inbound=true&outbound=true')
    r2.json()
    """
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )  # TODO attention here!
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # authentication_classes = (authentication.TokenAuthentication, )
    throttle_classes = (throttling.UserRateThrottle, throttling.AnonRateThrottle, BurstRateThrottle)
    renderer_classes = [JSONRenderer]  # to disable browsable api

    def get_parameters(self, query_type):
        all_parameters = super(WikiwhoApiView, self).get_parameters(query_type)
        parameters = []
        self._set_default_type_parameters(query_type, parameters)
        for parameter in all_parameters:
            if type(parameter) == int:
                if query_type == 'all_content':
                    threshold = int(self.request.GET.get('threshold', settings.ALL_CONTENT_THRESHOLD_LIMIT))
                else:
                    threshold = int(self.request.GET.get('threshold', settings.DELETED_CONTENT_THRESHOLD_LIMIT))
                parameters.append(0 if threshold < 0 else threshold)
            elif self.request.GET.get(parameter) == 'true':
                parameters.append(parameter)
        return parameters

    def get_response(self, parameters, article_title=None, page_id=None, revision_ids=list(),
                     all_content=False, deleted=False, rev_ids=False):
        # if not parameters:
        #     return Response({'Error': 'At least one query parameter should be selected.'},
        #                     status=status.HTTP_400_BAD_REQUEST)

        # global handler_time
        # handler_start = time.time()
        timeout = gunicorn_timeout - 60  # 5 mins
        timeout_message = 'Process took more than {} seconds. ' \
                          'Requested data will be available soon (Max {} seconds). ' \
                          'Please try again later.'.format(timeout, user_task_soft_time_limit)
        try:
            revision_id = revision_ids[0] if revision_ids else None
            if settings.DEBUG:
                # to run locally with Timeout: runserver --noreload --nothreading
                with WPHandler(article_title, page_id=page_id, revision_id=revision_id) as wp:
                    self.page_id = wp.page_id
                    wp.handle(revision_ids, is_api_call=True)
            else:
                with Timeout(seconds=timeout, error_message=timeout_message):
                    with WPHandler(article_title, page_id=page_id, revision_id=revision_id) as wp:
                        self.page_id = wp.page_id
                        wp.handle(revision_ids, is_api_call=True, timeout=timeout)
        except TimeoutError as e:
            process_article_user.delay(article_title, page_id, revision_id)
            response = {'Info': timeout_message}
            status_ = status.HTTP_408_REQUEST_TIMEOUT
        except WPHandlerException as e:
            if e.code == '03':
                response = {'Info': e.message}
                status_ = status.HTTP_200_OK
            else:
                response = {'Error': e.message}
                if e.code in ['10', '11']:
                    # WP errors
                    status_ = status.HTTP_503_SERVICE_UNAVAILABLE
                else:
                    status_ = status.HTTP_400_BAD_REQUEST
        except JSONDecodeError as e:
            response = {'Error': 'HTTP Response error from Wikipedia! Please try again later.'}
            status_ = status.HTTP_400_BAD_REQUEST
        else:
            if all_content:
                response = self.get_all_content(wp, parameters)
                status_ = status.HTTP_200_OK
            elif deleted:
                response = self.get_deleted_content(wp, parameters)
                status_ = status.HTTP_200_OK
            elif rev_ids:
                response = self.get_revision_ids(wp, parameters)
                status_ = status.HTTP_200_OK
            else:
                response = self.get_revision_content(wp, parameters, from_db=False)
                if 'Error' in response:
                    status_ = status.HTTP_400_BAD_REQUEST
                else:
                    status_ = status.HTTP_200_OK
        # handler_time = time.time() - handler_start
        # return HttpResponse(json.dumps(response), content_type='application/json; charset=utf-8')
        # import json
        # with open('tmp_pickles/{}_ri.json'.format(article_title), 'w') as f:
        #     f.write(json.dumps(response, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        return Response(response, status=status_)

    def get_rev_content_by_rev_id(self, request, version, rev_id):
        parameters = self.get_parameters('rev_content')
        return self.get_response(parameters, revision_ids=[int(rev_id)])

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_range_rev_content(self, request, version, article_title, start_rev_id, end_rev_id):
        timestamps = get_revision_timestamp([start_rev_id, end_rev_id])
        if 'error' in timestamps:
            return Response({'Error': timestamps['error']},
                            status=status.HTTP_400_BAD_REQUEST)
        elif timestamps[0] > timestamps[1]:
            return Response({'Error': 'End revision id has to be older than start revision id!'},
                            status=status.HTTP_400_BAD_REQUEST)
        parameters = self.get_parameters('rev_content')
        return self.get_response(parameters, article_title, revision_ids=[int(start_rev_id), int(end_rev_id)])

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_article_rev_content(self, request, version, article_title, rev_id):
        parameters = self.get_parameters('rev_content')
        return self.get_response(parameters, article_title, revision_ids=[int(rev_id)])

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_rev_content_by_title(self, request, version, article_title):
        parameters = self.get_parameters('rev_content')
        return self.get_response(parameters, article_title)

    def get_rev_content_by_page_id(self, request, version, page_id):
        parameters = self.get_parameters('rev_content')
        return self.get_response(parameters, page_id=page_id)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_deleted_content_by_title(self, request, version, article_title):
        parameters = self.get_parameters('deleted_content')
        return self.get_response(parameters, article_title, deleted=True)

    def get_deleted_content_by_page_id(self, request, version, page_id):
        parameters = self.get_parameters('deleted_content')
        return self.get_response(parameters, page_id=page_id, deleted=True)

    def get_all_content_by_title(self, request, version, article_title):
        parameters = self.get_parameters('all_content')
        return self.get_response(parameters, article_title, all_content=True)

    def get_all_content_by_page_id(self, request, version, page_id):
        parameters = self.get_parameters('all_content')
        return self.get_response(parameters, page_id=page_id, all_content=True)

    # @detail_route(renderer_classes=(StaticHTMLRenderer,))
    def get_rev_ids_by_title(self, request, version, article_title):
        parameters = self.get_parameters('rev_ids')
        return self.get_response(parameters, article_title, rev_ids=True)

    def get_rev_ids_by_page_id(self, request, version, page_id):
        parameters = self.get_parameters('rev_ids')
        return self.get_response(parameters, page_id=page_id, rev_ids=True)

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


class ApiRedirectView(RedirectView):
    permanent = False  # 302
    # pattern_name = 'api:swagger'

    def get_redirect_url(self, *args, **kwargs):
        return reverse('api:swagger', kwargs={'version': version_url})
