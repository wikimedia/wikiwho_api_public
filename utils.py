# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
import io
import logging
import requests
import json
import sys
import six
import six.moves.cPickle as pickle


def print_fail(message=None, format_="json"):
    # import os
    response = {"success": "false",
                "revisions": None,
                "article": None}
    # dict_list = None

    if format_ == 'json':
        # response["tokens"] = dict_list
        response["message"] = message
        print(json.dumps(response))
    sys.exit()
    # os._exit(1)


def pickle_(article_name, obj, path_):
    logging.debug("pickling")
    pickle_file_path = path_ + article_name + ".p"
    # Protocol version 4 was added in Python 3.4. It adds support for very large objects,
    # pickling more kinds of objects, and some data format optimizations. Refer to PEP 3154 for
    # information about improvements brought by protocol 4.
    # FIXME for large objects
    with io.open(pickle_file_path, 'wb') as file_:
        pickle.dump(obj, file_, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available


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
    first_page_id = six.next(six.iterkeys(response["query"]["pages"]))
    if first_page_id == '-1':
        # article name does not exist
        return []
    latest_revision_id = response["query"]["pages"][first_page_id]["revisions"][0]["revid"]
    return [latest_revision_id]
