# -*- coding: utf-8 -*-
from django.conf import settings
from api.utils import create_wp_session, get_wp_api_url

from WhoColor.utils import WikipediaRevText as WikipediaRevTextBase, WikipediaUser as WikipediaUserBase


class WikipediaRevText(WikipediaRevTextBase):

    def __init__(self, page_title=None, page_id=None, rev_id=None, language=None):
        """
        :param page_title: Title of an article.
        :param page_id: ID of an article
        :param rev_id: Revision id to get wiki text.
        """
        self.page_id = page_id
        self.page_title = page_title
        self.rev_id = rev_id
        self.language = language

    def _prepare_request(self, wiki_text=None):
        data = super(WikipediaRevText, self)._prepare_request(wiki_text)
        data['headers'] = settings.WP_HEADERS
        data['url'] = get_wp_api_url(self.language)
        data['timeout'] = settings.WP_REQUEST_TIMEOUT
        return data


class WikipediaUser(WikipediaUserBase):

    def _prepare_request(self):
        data = super(WikipediaUser, self)._prepare_request()
        data['headers'] = settings.WP_HEADERS
        data['url'] = get_wp_api_url('en')
        data['timeout'] = settings.WP_REQUEST_TIMEOUT
        return data

    def _make_request(self, data):
        session = create_wp_session('en')
        response = session.post(**data)
        response = response.json()
        return response

# def get_wp_rev_text(page_id=None, page_title=None, rev_id=None):
#         """
#         If no rev id is given, text of latest revision is returned.
#         If both article id and title are given, id is used in query.
#         :param page_id: ID of an article
#         :param page_title: Title of an article.
#         :param rev_id: Revision id to get text.
#         :return: Markup text of revision.
#         """
#     params = {'action': 'query', 'prop': 'revisions', 'rvprop': 'content|ids',
#               'rvlimit': '1', 'format': 'json'}
#     if page_id:
#         params.update({'pageids': page_id})
#     elif page_title:
#         params.update({'titles': page_title})
#     else:
#         raise Exception('Please provide id or title of the article.')
#
#     if rev_id is not None:
#         params.update({'rvstartid': rev_id})  # , 'rvendid': rev_id})
#
#     headers = {'User-Agent': settings.WP_HEADERS_USER_AGENT,
#                'From': settings.WP_HEADERS_FROM}
#     result = requests.get(url=settings.WP_API_URL, headers=headers, params=params,
#                           timeout=settings.WP_REQUEST_TIMEOUT)
#     result = result.json()
#
#     if 'error' in result:
#         return result
#
#     pages = result['query']['pages']
#     if '-1' in pages:
#         return pages
#
#     page_id, page = result['query']['pages'].popitem()
#     namespace = page['ns']
#     for rev_data in page.get('revisions', []):
#         return {
#             'page_id': int(page_id),
#             'namespace': namespace,
#             'rev_id': rev_data['revid'],
#             'rev_text': rev_data['*']
#         }

