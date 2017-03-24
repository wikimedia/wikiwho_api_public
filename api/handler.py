# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from datetime import datetime, timedelta
import os
import sys
# import logging
# from time import time
# from builtins import open

from django.conf import settings

from wikiwho.wikiwho_simple import Wikiwho
from .utils import get_latest_revision_data, create_wp_session, Timeout
from .utils_pickles import pickle_dump, pickle_load
from wikiwho.utils_db import wikiwho_to_db

sys.setrecursionlimit(5000)  # default is 1000
# http://neopythonic.blogspot.de/2009/04/tail-recursion-elimination.html
# session = create_wp_session()


class WPHandlerException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class WPHandler(object):
    def __init__(self, article_title, page_id=None, pickle_folder='', save_tables=(),
                 check_exists=True, is_xml=False, revision_id=None, *args, **kwargs):
        # super(WPHandler, self).__init__(article_title, pickle_folder=pickle_folder, *args, **kwargs)
        self.article_title = article_title
        self.saved_article_title = ''
        self.revision_ids = []
        self.wikiwho = None
        self.pickle_folder = pickle_folder
        self.pickle_path = ''
        self.saved_rvcontinue = ''
        self.latest_revision_id = None
        self.page_id = page_id
        self.revision_id = revision_id
        self.save_tables = save_tables
        self.check_exists = check_exists
        self.already_exists = False
        self.is_xml = is_xml
        self.namespace = 0

    def __enter__(self):
        # time1 = time()
        # logging.debug("--------")
        # logging.debug(self.article_title)
        # check if given page_id valid
        if self.page_id:
            self.page_id = int(self.page_id)
            if not 0 < self.page_id < 2147483647:
                raise WPHandlerException('Please enter a valid page id ({}).'.format(self.page_id))

        if self.is_xml:
            self.saved_article_title = self.article_title.replace(' ', '_')
            # self.page_id = self.page_id
        else:
            # get db title from wp api
            d = get_latest_revision_data(self.page_id, self.article_title, self.revision_id)
            self.latest_revision_id = d['latest_revision_id']
            self.page_id = d['page_id']
            self.saved_article_title = d['article_db_title']
            self.namespace = d['namespace']

        # logging.debug("trying to load pickle")
        pickle_folder = self.pickle_folder or settings.PICKLE_FOLDER
        self.pickle_path = "{}/{}.p".format(pickle_folder, self.page_id)
        self.already_exists = os.path.exists(self.pickle_path)
        if not self.already_exists:
            # a new pickle will be created
            self.wikiwho = Wikiwho(self.saved_article_title)
            self.wikiwho.page_id = self.page_id
        else:
            self.wikiwho = pickle_load(self.pickle_path)
            self.wikiwho.title = self.saved_article_title
        self.saved_rvcontinue = self.wikiwho.rvcontinue
        # if self.save_tables:
        #     update titles of other articles with other page ids by using wp api (celery task)
        #     articles = [a for a in Article.objects.filter(title=self.saved_article_title)]
        #     for article in articles:
        #         if article.id == page_id:
        #             self.article_obj = article
        #             articles.remove(article)
        #             break
        #     if articles:
        #         update_titles_task(articles)

        # time2 = time()
        # print("Execution time enter: {}".format(time2-time1))
        return self

    def handle_from_xml_dump(self, page, timeout=None):
        # this handle is used only to fill the db so if already exists, skip this article
        # here we don't have rvcontinue check to analyse article as we have in handle method
        if self.check_exists and self.already_exists:
            # no continue logic for xml processing
            # return
            raise WPHandlerException('Article ({}) already exists.'.format(self.page_id))

        try:
            if timeout:
                with Timeout(seconds=timeout,
                             error_message='Timeout in analyse_article_from_xml_dump ({} seconds)'.format(timeout)):
                    self.wikiwho.analyse_article_from_xml_dump(page)
            else:
                self.wikiwho.analyse_article_from_xml_dump(page)
        except TimeoutError:
            # if timeout, nothing is saved
            raise
        except Exception:
            if self.wikiwho.revision_curr.timestamp == 0:
                # if all revisions were detected as spam
                # wikiwho object holds no information (it is in initial status, rvcontinue=0)
                self.wikiwho.rvcontinue = '1'  # assign 1 to be able to save this article without any revisions
            else:  # NOTE: revision_prev is used to determine rvcontinue
                timestamp = datetime.strptime(self.wikiwho.revision_prev.timestamp, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
                self.wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') \
                                          + "|" \
                                          + str(self.wikiwho.revision_prev.id + 1)
            raise

        if self.wikiwho.revision_curr.timestamp == 0:
            # if all revisions were detected as spam
            # wikiwho object holds no information (it is in initial status, rvcontinue=0)
            self.wikiwho.rvcontinue = '1'  # assign 1 to be able to save this article without any revisions
        else:  # NOTE: revision_curr is used to determine rvcontinue
            timestamp = datetime.strptime(self.wikiwho.revision_curr.timestamp, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
            self.wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') \
                                      + "|" \
                                      + str(self.wikiwho.revision_curr.id + 1)

    def handle(self, revision_ids, is_api_call=True):
        # time1 = time()
        # check if article exists
        if self.latest_revision_id is None:
            raise WPHandlerException('The article ({}) you are trying to request does not exist'.
                                     format(self.article_title or self.page_id))
        elif self.namespace != 0:
            raise WPHandlerException('Only articles! Namespace {} is not accepted.'.format(self.namespace))
        self.revision_ids = revision_ids or [self.latest_revision_id]

        if settings.ONLY_READ_ALLOWED:
            if self.already_exists:
                return
            else:
                raise WPHandlerException('Only read is allowed for now.')

        # holds the last revision id which is saved. 0 for new article
        rvcontinue = self.saved_rvcontinue

        if self.revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
            # if given rev_id is bigger than saved one
            # logging.debug("STARTING NOW")
            session = create_wp_session()
            headers = {'User-Agent': settings.WP_HEADERS_USER_AGENT,
                       'From': settings.WP_HEADERS_FROM}
            params = {'pageids': self.page_id, 'action': 'query', 'prop': 'revisions',
                      'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
                      'rvlimit': 'max', 'format': 'json', 'continue': '', 'rvdir': 'newer'}

        while self.revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
            # continue downloading as long as we reach to the given rev_id limit
            # if rvcontinue > self.revision_ids[-1], it means this rev_id is saved,
            # so no calculation is needed
            # logging.debug('doing partial download')
            # logging.debug(rvcontinue)

            if rvcontinue != '0' and rvcontinue != '1':
                params['rvcontinue'] = rvcontinue
            try:
                # TODO ? get revisions until revision_ids[-1], check line: elif not pages.get('revision')
                # params.update({'rvendid': self.revision_ids[-1]})  # gets from beginning
                result = session.get(url=settings.WP_API_URL, headers=headers, params=params,
                                     timeout=settings.WP_REQUEST_TIMEOUT).json()
            except Exception as e:
                if is_api_call:
                    raise WPHandlerException('HTTP Response error from Wikipedia! Please try again later.')
                else:
                    # if not api query, raise the original exception
                    raise e

            if 'error' in result:
                raise WPHandlerException('Wikipedia API returned the following error:' + str(result['error']))
            # if 'warnings' in result:
            #   raise WPHandlerException('Wikipedia API returned the following warning:" + result['warnings']))
            if 'query' in result:
                pages = result['query']['pages']
                if "-1" in pages:
                    raise WPHandlerException('The article ({}) you are trying to request does not exist!'.
                                             format(self.article_title or self.page_id))
                # elif not pages.get('revision'):
                #     raise WPHandlerException(message="End revision ID does not exist!")
                try:
                    # pass first item in pages dict
                    _, page = result['query']['pages'].popitem()
                    self.wikiwho.analyse_article(page.get('revisions', []))
                except Exception:
                    if self.wikiwho.revision_curr.timestamp == 0:
                        # if all revisions were detected as spam
                        # wikiwho object holds no information (it is in initial status, rvcontinue=0)
                        self.wikiwho.rvcontinue = '1'  # assign 1 to be able to save this article without any revisions
                    else:  # NOTE: revision_prev is used to determine rvcontinue
                        timestamp = datetime.strptime(self.wikiwho.revision_prev.timestamp,
                                                      '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
                        self.wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') \
                                                  + "|" \
                                                  + str(self.wikiwho.revision_prev.id + 1)
                    raise
            if 'continue' not in result:
                # hackish: create a rvcontinue with last revision id of this article
                if self.wikiwho.revision_curr.timestamp == 0:
                    # if # revisions < 500 and all revisions were detected as spam
                    # wikiwho object holds no information (it is in initial status, rvcontinue=0)
                    self.wikiwho.rvcontinue = '1'  # assign 1 to be able to save this article without any revisions
                else:  # NOTE: revision_curr is used to determine rvcontinue
                    timestamp = datetime.strptime(self.wikiwho.revision_curr.timestamp, '%Y-%m-%dT%H:%M:%SZ') \
                                + timedelta(seconds=1)
                    self.wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') \
                                              + "|" \
                                              + str(self.wikiwho.revision_curr.id + 1)
                # print wikiwho.rvcontinue
                break
            rvcontinue = result['continue']['rvcontinue']
            self.wikiwho.rvcontinue = rvcontinue  # used at end to decide if there is new revisions to be saved
            # print rvcontinue

        # logging.debug('final rvcontinue ' + str(self.wikiwho.rvcontinue))

        # time2 = time()
        # print("Execution time handle: {}".format(time2-time1))

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        If the context was exited without an exception, all three arguments will be None.
        If an exception is supplied, and the method wishes to suppress the exception (i.e., prevent it from being
        propagated), it should return a true value. Otherwise, the exception will be processed normally upon exit
        from this method.
        Note that __exit__() methods should not reraise the passed-in exception; this is the caller’s responsibility.
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        # time1 = time()
        # print(exc_type, exc_val, exc_tb)
        # logging.debug(self.wikiwho.rvcontinue, self.saved_rvcontinue)
        # logging.debug(wikiwho.lastrev_date)
        if self.wikiwho and self.wikiwho.rvcontinue != self.saved_rvcontinue:
            # if there is a new revision or first revision of the article
            self.wikiwho.clean_attributes()
            pickle_dump(self.wikiwho, self.pickle_path)
            if self.save_tables:
                wikiwho_to_db(self.wikiwho, save_tables=self.save_tables)
        # return True
        # time2 = time()
        # print("Execution time exit: {}".format(time2-time1))
