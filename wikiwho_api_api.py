#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import division
import cgitb
import io
import logging
import cgi

from Wikiwho_simple import Wikiwho
import urllib  # , urllib2
import cPickle
# import sys
import requests
# import httplib
# from cStringIO import StringIO
# import json
# from time import time
# import dateutil.parser
from datetime import datetime, timedelta
import json
import sys

__author__ = 'psinger,ffloeck'

# enable debugging
cgitb.enable(format="html")
# logging
logging.basicConfig(filename='log_api_api.log', level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
# CGI
fs = cgi.FieldStorage()

print "Content-Type: application/json"
print


def print_fail(message=None, format_="json"):
    # import os
    response = {"success": "false",
                "revisions": None,
                "article": None}
    # dict_list = None

    if format_ == 'json':
        # response["tokens"] = dict_list
        response["message"] = message
        print json.dumps(response)
    sys.exit()
    # os._exit(1)


def pickle(article_name, obj, path_):
    logging.debug("pickling")
    pickle_file_path = path_ + article_name + ".p"
    # Protocol version 4 was added in Python 3.4. It adds support for very large objects,
    # pickling more kinds of objects, and some data format optimizations. Refer to PEP 3154 for
    # information about improvements brought by protocol 4.
    # FIXME for large objects
    with io.open(pickle_file_path, 'wb') as file_:
        cPickle.dump(obj, file_, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available


def get_latest_revision_id(article_name):
    if not article_name:
        return []
    # set up request for Wikipedia API.
    server = "en.wikipedia.org"
    wp_api_url = 'https://{}/w/api.php'.format(server)
    params = {'action': "query", 'prop': 'revisions', 'titles': article_name, 'format': 'json'}
    headers = {"User-Agent": "WikiWhoClient/0.1", "Accept": "*/*", "Host": server}
    # make get request
    resp_ = requests.get(wp_api_url, params, headers=headers)
    # convert response into dict
    response = resp_.json()
    first_page_id = response["query"]["pages"].keys()[0]
    if first_page_id == '-1':
        # article name does not exist
        return []
    latest_revision_id = response["query"]["pages"][first_page_id]["revisions"][0]["revid"]
    return [latest_revision_id]

if __name__ == '__main__':
    # time1 = time()

    # article_name = "Memex"
    # reviid = 601975046
    # format_ = "json"

    article_name = ''
    try:
        article_name = fs.getvalue('name')  # for running through browser
    except:
        # FIXME i guess it doesnt enter here
        print_fail(message="Name missing!")
    if not article_name:
        print_fail(message="Name missing!")

    try:
        revision_ids = [int(x) for x in fs.getvalue('revid').split('|')]  # for running through browser
    except:
        revision_ids = get_latest_revision_id(article_name)
        if not revision_ids:
            print_fail(message="The article you are trying to request does not exist!")
    if len(revision_ids) > 2:
        print_fail(message="Too many revision ids provided!")
    if len(revision_ids) == 2:
        # TODO instead of giving error, reorder it?
        if revision_ids[1] <= revision_ids[0]:
            print_fail(message="Second revision id has to be larger than first revision id!")

    try:
        format_ = fs.getvalue('format')
    except:
        format_ = "json"
    else:
        if not format_:
            format_ = "json"  # default
        elif format_ != "json":
            print_fail(message="Currently, only json works as format!")

    try:
        parameters = set(fs.getvalue('params').split('|'))
    except:
        parameters = set()
    if parameters.issubset({'revid', 'author', 'tokenid'}) is False:
        print_fail(message="Wrong parameter in list!")

    # article_name = 'graz'
    # reviid = 45618658
    # format_ = "json"

    logging.debug("--------")
    logging.debug(article_name)
    logging.debug(revision_ids)

    article_name = article_name.replace(" ", "_")

    # article_name = "test4"

    logging.debug("trying to load pickle")
    # FIXME loading large pickle files
    try:
        # see if exists in primary disk, load, extend
        with open("pickle_api/" + article_name + ".p", 'rb') as f:
            wikiwho = cPickle.load(f)
        path = "pickle_api/"
    except:
        try:
            # see if exists in secondary  disk, load, extend
            with open("../disk2/pickle_api_2/" + article_name + ".p", 'rb') as f:
                wikiwho = cPickle.load(f)
            path = "../disk2/pickle_api_2/"
        except:
            # a new pickle in secondary disk will be created
            wikiwho = Wikiwho(article_name)
            path = "../disk2/pickle_api_2/"

    assert (wikiwho.article == article_name)

    url = 'https://en.wikipedia.org/w/api.php'
    params = '?action=query&meta=tokens&type=login&format=json'
    headers = {'User-Agent': 'Wikiwho API',
               'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'}

    # bot credentials
    user = 'Fabian%20Fl%C3%B6ck@wikiwho'
    passw = 'o2l009t25ddtlefdt6cboctj8hk8nbfs'

    session = requests.session()
    # Login request and create session
    # TODO how to stay logged in for next queries and only login if logged out?
    r1 = session.post(url+params)
    # print r1.json()
    # r1 = json.loads(r1)
    token = r1.json()["query"]["tokens"]["logintoken"]
    token = urllib.quote(token)

    params2 = '?action=login&lgname={}&lgpassword={}&lgtoken={}&format=json'.format(user, passw, token)
    # print 'params2', params2
    # Confirm token; should give "Success"
    r2 = session.post(url+params2)
    # print r2.json()

    logging.debug("STARTING NOW")

    # revisions: Returns revisions for a given page
    params = {'titles': article_name, 'action': 'query', 'prop': 'revisions',
              'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
              'rvlimit': 'max', 'format': format_, 'continue': '', 'rvdir': 'newer'}
    # rvcontinue = timestamp|next_rev_id
    rvcontinue = wikiwho.rvcontinue
    start = rvcontinue  # holds the last revision id which is stored in pickle file
    # print rvcontinue
    # rvcontinue = '643899697'

    # THINK ABOUT NO RVCONTINUE

    # TODO get last_rev_id anyway and check if given rev_ids > last_rev_id or not.
    # if yes, print_fail(message="Revision ID does not exist!")
    # TODO first check if given rev_ids exist in wikiwho object already. if yes, dont get and print directly
    # wikiwho_rev_ids = wikiwho.revisions.keys()
    # if set(revision_ids).issubset(set(wikiwho_rev_ids)):
    i = 0
    while revision_ids[-1] >= int(rvcontinue.split('|')[-1]):
        # continue downloading as long as we reach to the rev_id limit
        # TODO do this until last_rev_id?
        # while latest_revision_id > int(rvcontinue.split('|')[-1]):
        logging.debug('doing partial download')
        logging.debug(rvcontinue)

        if rvcontinue != '0':
            params['rvcontinue'] = rvcontinue
        try:
            # TODO is it possible to get only given revisions not all? yes, check: elif not pages.get('revision')
            # params.update({'rvstartid': revision_ids[0], 'rvendid': revision_ids[1]})
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
            #     print_fail(message="Start and/or end revision ID does not exist!")
            try:
                wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
            except:
                # if there is a problem, save pickle file until last given unproblematic rev_id
                pickle(article_name, wikiwho, path)
                print_fail(message="Some problems with the JSON returned by Wikipedia!")
        if 'continue' not in result:
            # hackish: create a rvcontinue with last revision id of this article
            timestamp = datetime.strptime(wikiwho.revision_curr.time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
            wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') + "|" + str(wikiwho.revision_curr.wikipedia_id + 1)
            # print wikiwho.rvcontinue
            break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue  # used in the end to decide if a new pickle file should be saved or not
        # print rvcontinue

    logging.debug('final rvcontinue ' + str(wikiwho.rvcontinue))

    # print len(wikiwho.revisions)

    wikiwho_rev_ids = wikiwho.revisions.keys()
    for r in revision_ids:
        if r not in wikiwho_rev_ids:
            print_fail(message="Revision ID does not exist or is spam or deleted!")

    wikiwho.printRevision(revision_ids, parameters)

    logging.debug(wikiwho.rvcontinue)
    # logging.debug(wikiwho.lastrev_date)

    if wikiwho.rvcontinue != start:
        # if there is a new revision or first pickle of the article
        # save new pickle file
        pickle(article_name, wikiwho, path)
