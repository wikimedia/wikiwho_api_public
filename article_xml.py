# -*- coding: utf-8 -*-
"""
Script to import full revision history of an wikipedia article as a xml file. The format is changed to be able to used
by wikimedia utilities in original (paper) code.
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import requests
import urllib
from lxml import etree


def get_article_xml(article_name):
    article_name = article_name.replace(" ", "_")

    url = 'https://en.wikipedia.org/w/api.php'
    params = '?action=query&meta=tokens&type=login&format=json'
    headers = {'User-Agent': 'Wikiwho API',
               'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'}
    # bot credentials
    user = 'Fabian%20Fl%C3%B6ck@wikiwho'
    passw = 'o2l009t25ddtlefdt6cboctj8hk8nbfs'
    # Login request and create session
    session = requests.session()
    r1 = session.post(url + params)
    token = r1.json()["query"]["tokens"]["logintoken"]
    token = urllib.quote(token)

    params2 = '?action=login&lgname={}&lgpassword={}&lgtoken={}&format=json'.format(user, passw, token)
    r2 = session.post(url + params2)

    # revisions: Returns revisions for a given page
    params = {'titles': article_name, 'action': 'query', 'prop': 'revisions',
              'rvprop': 'content|ids|timestamp|sha1|comment|flags|user|userid',
              'rvlimit': 'max', 'format': 'xml', 'continue': '', 'rvdir': 'newer'}

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
        # root = etree.fromstring(result.content)
        p = etree.XMLParser(huge_tree=True)
        root = etree.fromstringlist(list(result.content), parser=p)
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
