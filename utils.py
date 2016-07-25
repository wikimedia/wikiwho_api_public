# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from lxml import etree
import io
import logging
import requests
import json
import sys
import six
from six.moves import cPickle as pickle, urllib


def print_fail(message=None, format_="json", is_api=True):
    if is_api:
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
    else:
        raise Exception(message)


def pickle_(obj, pickle_path):
    logging.debug("pickling")
    # Protocol version 4 was added in Python 3.4. It adds support for very large objects,
    # pickling more kinds of objects, and some data format optimizations. Refer to PEP 3154 for
    # information about improvements brought by protocol 4.
    with io.open(pickle_path, 'wb') as file_:
        pickle.dump(obj, file_, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available


def get_latest_revision_id(article_name):
    if not article_name:
        return ''
    # set up request for Wikipedia API.
    server = "en.wikipedia.org"
    wp_api_url = 'https://{}/w/api.php'.format(server)
    params = {'action': "query", 'prop': 'revisions', 'titles': article_name, 'format': 'json', 'rvlimit': '1'}
    # params = {'action': "query", 'titles': article_name, 'format': 'json'}
    headers = {"User-Agent": "WikiWhoClient/0.1", "Accept": "*/*", "Host": server}
    # make get request
    resp_ = requests.get(wp_api_url, params, headers=headers)
    # convert response into dict
    response = resp_.json()
    first_page_id = six.next(six.iterkeys(response["query"]["pages"]))
    if first_page_id == '-1':
        # article name does not exist
        return ''
    latest_revision_id = response["query"]["pages"][first_page_id]["revisions"][0]["revid"]
    return latest_revision_id


def create_wp_session():
    # bot credentials
    user = 'Fabian%20Fl%C3%B6ck@wikiwho'
    passw = 'o2l009t25ddtlefdt6cboctj8hk8nbfs'
    # create session
    session = requests.session()
    session.auth = (user, passw)
    headers = {'User-Agent': 'Wikiwho API',
               'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'}
    session.headers.update(headers)
    # Login request
    url = 'https://en.wikipedia.org/w/api.php'
    params = '?action=query&meta=tokens&type=login&format=json'
    # get token
    r1 = session.post(url + params)
    token = r1.json()["query"]["tokens"]["logintoken"]
    token = urllib.parse.quote(token)
    # log in
    params2 = '?action=login&lgname={}&lgpassword={}&lgtoken={}&format=json'.format(user, passw, token)
    r2 = session.post(url + params2)
    return session


def get_article_xml(article_name):
    """
    Imports full revision history of an wikipedia article as a xml file. The format is changed to be able to
    used by wikimedia utilities in original (paper) code.
    """
    article_name = article_name.replace(" ", "_")

    session = create_wp_session()

    # revisions: Returns revisions for a given page
    params = {'titles': article_name, 'action': 'query', 'prop': 'revisions',
              'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
              'rvlimit': 'max', 'format': 'xml', 'continue': '', 'rvdir': 'newer'}
    headers = {'User-Agent': 'Wikiwho API',
               'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'}
    url = 'https://en.wikipedia.org/w/api.php'

    rvcontinue = True
    # document = None
    # xml_file = '/home/kenan/PycharmProjects/wikiwho_api/local/original_code_xml_tests/{}.xml'.format(article_name)
    xml_file = '{}.xml'.format(article_name)
    mediawiki = etree.Element("mediawiki")
    etree.SubElement(mediawiki, "siteinfo")
    mediawiki_page = etree.SubElement(mediawiki, "page")
    while rvcontinue:
        if rvcontinue is not True and rvcontinue != '0':
            params['rvcontinue'] = rvcontinue
            print(rvcontinue)
        try:
            result = session.get(url=url, headers=headers, params=params)
        except:
            print("HTTP Response error! Try again later!")
        p = etree.XMLParser(huge_tree=True, encoding='utf-8')
        try:
            root = etree.fromstringlist(list(result.content), parser=p)
        except TypeError:
            root = etree.fromstring(result.content, parser=p)
        if root.find('error') is not None:
            print("Wikipedia API returned the following error: " + str(root.find('error').get('info')))
        query = root.find('query')
        if query is not None:
            pages = query.find('pages')
            if pages is not None:
                page = pages.find('page')
                if page is not None:
                    if page.get('_idx') == '-1':
                        print("The article you are trying to request does not exist!")
                    else:
                        if mediawiki_page.find('title') is None:
                            title = etree.SubElement(mediawiki_page, "title")
                            title.text = page.get('title', '')
                            ns = etree.SubElement(mediawiki_page, "ns")
                            ns.text = page.get('ns', '')
                            id = etree.SubElement(mediawiki_page, "id")
                            id.text = page.get('pageid', '')
                        for rev in root.find('query').find('pages').find('page').find('revisions').findall('rev'):
                            revision = etree.SubElement(mediawiki_page, "revision")
                            id = etree.SubElement(revision, "id")
                            id.text = rev.get('revid')
                            timestamp = etree.SubElement(revision, "timestamp")
                            timestamp.text = rev.get('timestamp', '')
                            contributor = etree.SubElement(revision, "contributor")
                            username = etree.SubElement(contributor, "username")
                            username.text = rev.get('user', '')
                            id = etree.SubElement(contributor, "id")
                            id.text = rev.get('userid', '0')
                            text = etree.SubElement(revision, "text")
                            text.text = rev.text
                            sha1 = etree.SubElement(revision, "sha1")
                            sha1.text = rev.get('sha1', '')
                            model = etree.SubElement(revision, "model")
                            model.text = rev.get('contentmodel', '')
                            format = etree.SubElement(revision, "format")
                            format.text = rev.get('contentformat', '')
        continue_ = root.find('continue')
        if continue_ is not None:
            rvcontinue = continue_.get('rvcontinue')
        else:
            rvcontinue = False
    document = etree.ElementTree(mediawiki)
    document.write(xml_file)
    # document.write(xml_file, pretty_print=True, xml_declaration=True, encoding)
