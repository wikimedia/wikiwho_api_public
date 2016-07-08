# -*- coding: utf-8 -*-
# TODO make a CLASS WikiwhoHandler
from __future__ import division
import logging
import urllib
import cPickle
import requests
from datetime import datetime, timedelta

from Wikiwho_simple import Wikiwho
from utils import print_fail, pickle


def handle(article_name, revision_ids, format_, parameters, is_api=True):
    # TODO get last_rev_id anyway and check if given rev_ids[-1] > last_rev_id or not.
    # if yes, print_fail(message="Revision ID does not exist!")

    if is_api:
        logging.debug("--------")
        logging.debug(article_name)
        logging.debug(revision_ids)
        logging.debug("trying to load pickle")

        article_name = article_name.replace(" ", "_")
        # FIXME loading large pickle files
        pickle_folder = 'pickle_api'
        # pickle_folder = 'test_pickles'
        """
        path = "{}/".format(pickle_folder)
        if os.path.exists(path + article_name + ".p"):
            create_new = False
        else:
            pickle_folder = 'pickle_api_2'
            # pickle_folder = 'test_pickles'
            path = "../disk2/{}/".format(pickle_folder)
            if os.path.exists(path + article_name + ".p"):
                create_new = False
            else:
                create_new = True
        """
        try:
            # see if exists in primary disk, load, extend
            path = "{}/".format(pickle_folder)
            with open(path + article_name + ".p", 'rb') as f:
                wikiwho = cPickle.load(f)
        except:
            pickle_folder = 'pickle_api_2'
            # pickle_folder = 'test_pickles'
            try:
                # see if exists in secondary  disk, load, extend
                path = "../disk2/{}/".format(pickle_folder)
                with open(path + article_name + ".p", 'rb') as f:
                    wikiwho = cPickle.load(f)
            except:
                # a new pickle in secondary disk will be created
                path = "../disk2/{}/".format(pickle_folder)
                wikiwho = Wikiwho(article_name)
        assert (wikiwho.article == article_name)

        # holds the last revision id which is stored in pickle file. 0 for new article
        rvcontinue_in_pickle = wikiwho.rvcontinue
    else:
        wikiwho = Wikiwho(article_name)

    rvcontinue = wikiwho.rvcontinue

    if revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
        # if given rev_id is bigger than last one in pickle
        url = 'https://en.wikipedia.org/w/api.php'
        params = '?action=query&meta=tokens&type=login&format=json'
        headers = {'User-Agent': 'Wikiwho API',
                   'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'}
        # bot credentials
        user = 'Fabian%20Fl%C3%B6ck@wikiwho'
        passw = 'o2l009t25ddtlefdt6cboctj8hk8nbfs'
        # Login request and create session
        session = requests.session()
        # TODO how to stay logged in for next queries and only login if logged out?
        r1 = session.post(url + params)
        # print r1.json()
        # r1 = json.loads(r1)
        token = r1.json()["query"]["tokens"]["logintoken"]
        token = urllib.quote(token)

        params2 = '?action=login&lgname={}&lgpassword={}&lgtoken={}&format=json'.format(user, passw, token)
        # print 'params2', params2
        # Confirm token; should give "Success"
        r2 = session.post(url + params2)
        # print r2.json()

        logging.debug("STARTING NOW")

        # revisions: Returns revisions for a given page
        params = {'titles': article_name, 'action': 'query', 'prop': 'revisions',
                  'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
                  'rvlimit': 'max', 'format': format_, 'continue': '', 'rvdir': 'newer'}
        # rvcontinue = timestamp|next_rev_id
        # print rvcontinue
        # rvcontinue = '643899697'

        # THINK ABOUT NO RVCONTINUE

    while revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
        # continue downloading as long as we reach to the given rev_id limit
        # if rvcontinue > revision_ids[-1], it means this rev_id is already in pickle file, so no calculation is needed
        # TODO do this until last_rev_id?
        # while latest_revision_id > int(rvcontinue.split('|')[-1]):
        logging.debug('doing partial download')
        logging.debug(rvcontinue)

        if rvcontinue != '0':
            params['rvcontinue'] = rvcontinue
        try:
            # TODO get revisions until revision_ids[1], check line: elif not pages.get('revision')
            # if len(revision_ids) == 2:
            #     params.update({'rvendid': revision_ids[1]})  # gets from beginning
            result = session.get(url=url, headers=headers, params=params).json()
        except:
            print_fail(message="HTTP Response error! Try again later!")

        if 'error' in result:
            print_fail(message="Wikipedia API returned the following error:" + str(result['error']))
        # if 'warnings' in result:
        #   print_fail(reviid, message="Wikipedia API returned the following warning:" + result['warnings'])
        if 'query' in result:
            pages = result['query']['pages']
            if "-1" in pages:
                print_fail(message="The article you are trying to request does not exist!")
            # elif not pages.get('revision'):
            #     print_fail(message="End revision ID does not exist!")
            try:
                wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
            except:
                if is_api:
                    # if there is a problem, save pickle file until last given unproblematic rev_id
                    pickle(article_name, wikiwho, path)
                print_fail(message="Some problems with the JSON returned by Wikipedia!")
        if 'continue' not in result:
            # hackish: ?
            # create a rvcontinue with last revision id of this article
            timestamp = datetime.strptime(wikiwho.revision_curr.time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
            wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') + "|" + str(wikiwho.revision_curr.wikipedia_id + 1)
            # print wikiwho.rvcontinue
            break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue  # used in the end to decide if a new pickle file should be saved or not
        # print rvcontinue

    if is_api:
        logging.debug('final rvcontinue ' + str(wikiwho.rvcontinue))

    # print len(wikiwho.revisions)

    wikiwho_rev_ids = wikiwho.revisions.keys()
    for r in revision_ids:
        if r not in wikiwho_rev_ids:
            print_fail(message="Revision ID does not exist or is spam or deleted!")

    if is_api:
        wikiwho.print_revision(revision_ids, parameters)

        logging.debug(wikiwho.rvcontinue)
        # logging.debug(wikiwho.lastrev_date)

        if wikiwho.rvcontinue != rvcontinue_in_pickle:
            # if there is a new revision or first pickle of the article
            # save new pickle file
            pickle(article_name, wikiwho, path)
    else:
        wikiwho.print_revision_console(revision_ids, parameters)
