# -*- coding: utf-8 -*-
import os
import subprocess

from django.conf import settings
from api.utils import create_wp_session, get_wp_api_url

from WhoColor.utils import WikipediaRevText as WikipediaRevTextBase, WikipediaUser as WikipediaUserBase


class WikipediaRevText(WikipediaRevTextBase):

    def _prepare_request(self, wiki_text=None):
        data = super(WikipediaRevText, self)._prepare_request(wiki_text)
        data['headers'] = settings.WP_HEADERS
        data['timeout'] = settings.WP_REQUEST_TIMEOUT
        return data

    def convert_wiki_text_to_html_parsoid(self, wiki_text):
        process = subprocess.Popen(['{}/parsoid.sh'.format(os.path.dirname(os.path.realpath(__file__))), '--wt2html', "'{}".format(wiki_text)],
                                   stdout=subprocess.PIPE)
        output, error = process.communicate()
        return error or output.decode()


class WikipediaUser(WikipediaUserBase):

    def __init__(self):
        self.session = create_wp_session(self.language)

    def _prepare_request(self, editor_ids):
        data = super(WikipediaUser, self)._prepare_request(editor_ids)
        data['headers'] = settings.WP_HEADERS
        data['timeout'] = settings.WP_REQUEST_TIMEOUT
        return data

    def _make_request(self, data):
        response = self.session.post(**data)
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

