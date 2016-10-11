# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import io
import logging
from datetime import datetime, timedelta
import six
from django.conf import settings
from six.moves import cPickle as pickle
import os
from time import time
# from builtins import open

from wikiwho.wikiwho_simple import Wikiwho
from .utils import pickle_, get_latest_revision_id, create_wp_session

session = create_wp_session()


class WPHandlerException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class WPHandler(object):
    def __init__(self, article_name, pickle_folder='', *args, **kwargs):
        # super(WPHandler, self).__init__(article_name, pickle_folder=pickle_folder, *args, **kwargs)
        self.article_name = article_name
        self.revision_ids = []
        self.wikiwho = None
        self.pickle_folder = pickle_folder
        self.pickle_path = ''
        self.rvcontinue_in_pickle = ''

    def __enter__(self):
        # time1 = time()
        logging.debug("--------")
        logging.debug(self.article_name)
        logging.debug("trying to load pickle")

        article_name = self.article_name.replace(" ", "_")
        pickle_folder = self.pickle_folder or settings.PICKLE_FOLDER
        self.pickle_path = "{}/{}.p".format(pickle_folder, article_name.replace("/", "0x2f"))  # 0x2f is UTF-8 hex of /
        if os.path.exists(self.pickle_path):
            create_new = False
        else:
            pickle_folder = self.pickle_folder or settings.PICKLE_FOLDER_2
            self.pickle_path = "{}/{}.p".format(pickle_folder, article_name.replace("/", "0x2f"))
            create_new = not os.path.exists(self.pickle_path)
        if create_new:
            # a new pickle in secondary disk will be created
            self.wikiwho = Wikiwho(article_name)
        else:
            with io.open(self.pickle_path, 'rb') as f:
                self.wikiwho = pickle.load(f)
                # print(self.article_name, '-> rvcontinue_in_pickle:', self.wikiwho.rvcontinue)

        assert (self.wikiwho.article == article_name)

        self.rvcontinue_in_pickle = self.wikiwho.rvcontinue
        # time2 = time()
        # print("Execution time enter: {}".format(time2-time1))
        return self

    def handle(self, revision_ids, format_='json', is_api=True):
        # time1 = time()
        # check if article exists
        latest_revision_id = get_latest_revision_id(self.article_name)
        if not latest_revision_id:
            raise WPHandlerException('The article ({}) you are trying to request does not exist'.format(self.article_name))
        self.revision_ids = revision_ids or [latest_revision_id]
        latest_revision_id_used = not any(revision_ids)

        # holds the last revision id which is stored in pickle file. 0 for new article
        rvcontinue = self.rvcontinue_in_pickle

        if self.revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
            # if given rev_id is bigger than last one in pickle
            logging.debug("STARTING NOW")
            headers = {'User-Agent': settings.WP_HEADERS_USER_AGENT,
                       'From': settings.WP_HEADERS_FROM}
            # Login request
            url = 'https://en.wikipedia.org/w/api.php'
            # revisions: Returns revisions for a given page
            params = {'titles': self.article_name, 'action': 'query', 'prop': 'revisions',
                      'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
                      'rvlimit': 'max', 'format': format_, 'continue': '', 'rvdir': 'newer'}

        while self.revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
            # continue downloading as long as we reach to the given rev_id limit
            # if rvcontinue > self.revision_ids[-1], it means this rev_id is already in pickle file,
            # so no calculation is needed
            logging.debug('doing partial download')
            logging.debug(rvcontinue)

            if rvcontinue != '0' and rvcontinue != '1':
                params['rvcontinue'] = rvcontinue
            try:
                # TODO ? get revisions until revision_ids[-1], check line: elif not pages.get('revision')
                # params.update({'rvendid': self.revision_ids[-1]})  # gets from beginning
                result = session.get(url=url, headers=headers, params=params).json()
            except Exception as e:
                if is_api:
                    raise WPHandlerException('HTTP Response error! Try again later!'.format(self.article_name))
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
                    raise WPHandlerException('The article ({}) you are trying to request does not exist!'.format(self.article_name))
                # elif not pages.get('revision'):
                #     raise WPHandlerException(message="End revision ID does not exist!")
                try:
                    # page_id, page = result['query']['pages'].popitem()
                    # wikiwho.analyse_article(page.get('revisions', []))
                    # pass first item in pages dict
                    self.wikiwho.analyse_article(six.next(six.itervalues(result['query']['pages'])).
                                                 get('revisions', []))
                except Exception as e:
                    # if there is a problem, save pickle file until last given unproblematic rev_id
                    self.wikiwho._clean()
                    pickle_(self.wikiwho, self.pickle_path)
                    # TODO raise exception if it comes from wikiwho code
                    logging.exception(self.article_name)
                    raise WPHandlerException("Some problems with the JSON returned by Wikipedia!")
            if 'continue' not in result:
                # hackish: create a rvcontinue with last revision id of this article
                if self.wikiwho.revision_curr.time == 0:
                    # if # revisions < 500 and all revisions were detected as spam
                    # wikiwho object holds no information (it is in initial status, rvcontinue=0)
                    self.wikiwho.rvcontinue = '1'  # assign 1 to be able to save this article without any revisions
                else:
                    timestamp = datetime.strptime(self.wikiwho.revision_curr.time, '%Y-%m-%dT%H:%M:%SZ') \
                                + timedelta(seconds=1)
                    self.wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') \
                                              + "|" \
                                              + str(self.wikiwho.revision_curr.wikipedia_id + 1)
                # print wikiwho.rvcontinue
                break
            rvcontinue = result['continue']['rvcontinue']
            self.wikiwho.rvcontinue = rvcontinue  # used at end to decide if a new pickle file should be saved or not
            # print rvcontinue

        # print(self.article_name, self.wikiwho.revision_curr.time, self.wikiwho.revision_curr.wikipedia_id,
        #       len(self.wikiwho.revisions), len(self.wikiwho.spam))
        logging.debug('final rvcontinue ' + str(self.wikiwho.rvcontinue))
        # print len(wikiwho.revisions)

        for r in self.revision_ids:
            # sometimes latest_rev_id is a spam and this is important to us only if this is api query
            if is_api:
                # when user gives no rev_id as input to api
                condition = r not in self.wikiwho.revisions
            else:
                # condition is always False if not api and we raise no exception.
                # because we get the last rev id from wp
                condition = not latest_revision_id_used and r not in self.wikiwho.revisions
            if condition:
                raise WPHandlerException('Revision ID ({}) does not exist or is spam or deleted!'.format(r))
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
        logging.debug(self.wikiwho.rvcontinue)
        # logging.debug(wikiwho.lastrev_date)
        if self.wikiwho.rvcontinue != self.rvcontinue_in_pickle:
            # if there is a new revision or first pickle of the article
            # save new pickle file
            pickle_(self.wikiwho, self.pickle_path)
            # print(self.article_name, 'pickle saved')
        # return True
        # time2 = time()
        # print("Execution time exit: {}".format(time2-time1))
