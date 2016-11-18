# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from lxml import etree
import io
# import logging
import requests
import hashlib
# import six
from six.moves import cPickle as pickle, urllib

from django.conf import settings


def pickle_(obj, pickle_path):
    # logging.debug("pickling")
    # Protocol version 4 was added in Python 3.4. It adds support for very large objects,
    # pickling more kinds of objects, and some data format optimizations. Refer to PEP 3154 for
    # information about improvements brought by protocol 4.
    with io.open(pickle_path, 'wb') as file_:
        pickle.dump(obj, file_, protocol=-1)  # -1 to select HIGHEST_PROTOCOL available


def get_latest_revision_data(article_name):
    if not article_name:
        return ''
    # set up request for Wikipedia API.
    server = "en.wikipedia.org"
    wp_api_url = 'https://{}/w/api.php'.format(server)
    params = {'action': "query", 'prop': 'revisions', 'titles': article_name, 'format': 'json', 'rvlimit': '1'}
    # params = {'action': "query", 'titles': article_name, 'format': 'json'}
    # headers = {"User-Agent": "WikiWhoClient/0.1", "Accept": "*/*", "Host": server}
    headers = {'User-Agent': settings.WP_HEADERS_USER_AGENT,
               'From': settings.WP_HEADERS_FROM,
               "Accept": "*/*", "Host": server}
    # make get request
    resp_ = requests.get(wp_api_url, params, headers=headers)
    # convert response into dict
    # print(resp_)
    response = resp_.json()
    _, page = response["query"]["pages"].popitem()
    if 'missing' in page or _ == '-1':
        # article title does not exist or contains invalid character
        return None, None, None
    page_id = page['pageid']
    title = page['title'].replace(' ', '_')
    latest_revision_id = page["revisions"][0]["revid"]
    return latest_revision_id, page_id, title


def create_wp_session():
    # create session
    session = requests.session()
    session.auth = (settings.WP_USER, settings.WP_PASSWORD)
    headers = {'User-Agent': settings.WP_HEADERS_USER_AGENT,
               'From': settings.WP_HEADERS_FROM}
    session.headers.update(headers)
    # Login request
    url = 'https://en.wikipedia.org/w/api.php'
    params = '?action=query&meta=tokens&type=login&format=json'
    # get token
    r1 = session.post(url + params)
    token = r1.json()["query"]["tokens"]["logintoken"]
    token = urllib.parse.quote(token)
    # log in
    params2 = '?action=login&lgname={}&lgpassword={}&lgtoken={}&format=json'.format(settings.WP_USER,
                                                                                    settings.WP_PASSWORD,
                                                                                    token)
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
                        print("The article ({}) you are trying to request does not exist!".format(article_name))
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


def get_dumps_download_urls(url, date_time):
    r = requests.get(url)
    parser = etree.HTMLParser()
    from io import StringIO
    tree = etree.parse(StringIO(r.text), parser)
    links = []
    for li in tree.findall('body')[0].findall('ul')[0].findall('li'):
        # print(li.findall('span')[0].text)
        if li.findall('span')[0].text == date_time:
            for sub_li in li.find('ul').findall('li'):
                links.append('{}{}'.format('https://dumps.wikimedia.org', sub_li.find('a').get('href')))
            break
    return links


def download_file(folder, url):
    local_file_name = url.split('/')[-1]
    local_file_path = '{}/{}'.format(folder, local_file_name)
    from os.path import exists
    if not exists(local_file_path):
        # NOTE the stream=True parameter
        r = requests.get(url, stream=True)
        with open(local_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        print('downloaded: ', local_file_name)
    else:
        print('already existed: ', local_file_name)
    return local_file_path


def get_file_hash(file_path, blocksize=65536):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hash_md5.update(buf)
            buf = f.read(blocksize)
    return hash_md5.hexdigest()


def download_wp_dumps(folder, url='https://dumps.wikimedia.org/enwiki/20161101', date_time='2016-11-11 00:06:44'):
    download_urls = get_dumps_download_urls(url, date_time)
    for download_url in download_urls:
        local_file_path = download_file(folder, download_url)
        file_hash = get_file_hash(local_file_path)
        if file_hash != md5_hashes[local_file_path.split('/')[-1]]:
            print('corrupted: ', local_file_path)
        # print('+', local_file_path)
    print('Done')


md5_hashes = {
    'enwiki-20161101-pages-meta-history1.xml-p000000010p000002289.7z': '7b010cf0d76669945043dfd955f990a7',
    'enwiki-20161101-pages-meta-history1.xml-p000002290p000004531.7z': '5b79c7574d860b1111d689693e91997a',
    'enwiki-20161101-pages-meta-history1.xml-p000004536p000006546.7z': '7505950deef88792f1089421986c7d10',
    'enwiki-20161101-pages-meta-history1.xml-p000006547p000008653.7z': '22167c6138d48c5a2f92ddb01d706875',
    'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z': '6ed19d0e6fdded7bd1aa2bef41b42c1e',
    'enwiki-20161101-pages-meta-history1.xml-p000010883p000013026.7z': 'e7c57d6379d7f97de0c8909a2d8bdb29',
    'enwiki-20161101-pages-meta-history1.xml-p000013027p000015513.7z': '1faed52c1d6e2919dd5bfef77cec3580',
    'enwiki-20161101-pages-meta-history1.xml-p000015514p000017891.7z': '5acb51d717c188fe9b3a73a0adab76e0',
    'enwiki-20161101-pages-meta-history1.xml-p000017892p000020545.7z': '18d44fc94fdc1083c31c1c81d54bb4df',
    'enwiki-20161101-pages-meta-history1.xml-p000020546p000022915.7z': '7cb4bc8a9a54e098ae7f002fa65b42c0',
    'enwiki-20161101-pages-meta-history1.xml-p000022917p000025445.7z': '674c48c49994b844ae585fb84066db57',
    'enwiki-20161101-pages-meta-history1.xml-p000025446p000028258.7z': '9048eb4705ceee61297475c39f986891',
    'enwiki-20161101-pages-meta-history1.xml-p000028259p000030303.7z': 'f2a858aebd7d05fb6ecd65c9249c62ae',
    'enwiki-20161101-pages-meta-history2.xml-p000030304p000032258.7z': '3f6c10591971d9f2c2c40fdb31ad6537',
    'enwiki-20161101-pages-meta-history2.xml-p000032259p000034487.7z': 'e2c13a7024e9f9f7c9b26d649e8130b5',
    'enwiki-20161101-pages-meta-history2.xml-p000034488p000038769.7z': 'b56609e3945d8682e5213a5bf053f54d',
    'enwiki-20161101-pages-meta-history2.xml-p000038770p000042148.7z': 'd2366c528617942b5b4df7f9ab857176',
    'enwiki-20161101-pages-meta-history2.xml-p000042149p000046183.7z': 'e68ed98dc17a93e5a9eec6372db02592',
    'enwiki-20161101-pages-meta-history2.xml-p000046184p000050798.7z': 'e2d145b524eb7af508202add311df4cf',
    'enwiki-20161101-pages-meta-history2.xml-p000050799p000057690.7z': '9f2d0729f61e7f42db1486be7a76a5f2',
    'enwiki-20161101-pages-meta-history2.xml-p000057691p000066488.7z': 'a7844e080a5a020a6a53d29d69b5e142',
    'enwiki-20161101-pages-meta-history2.xml-p000066489p000078258.7z': '62a6199d42d54faab29fd7495d396565',
    'enwiki-20161101-pages-meta-history2.xml-p000078261p000088444.7z': 'e525d74cdb59653de45bd60bf7e75b23',
    'enwiki-20161101-pages-meta-history3.xml-p000088445p000101359.7z': '05c5ae6e5f1004f043b815834db113f0',
    'enwiki-20161101-pages-meta-history3.xml-p000101360p000118474.7z': 'fa19f595f1f5a58e035e1ef36ea3f89a',
    'enwiki-20161101-pages-meta-history3.xml-p000118475p000143283.7z': '4330f37dd427c40979faf4c68ca4c995',
    'enwiki-20161101-pages-meta-history3.xml-p000143284p000151682.7z': '0983fa8246a959ad9c1b1cebf8b7d8e4',
    'enwiki-20161101-pages-meta-history3.xml-p000151683p000161221.7z': '3d3fddf434065fad4e7189a907852458',
    'enwiki-20161101-pages-meta-history3.xml-p000161222p000169747.7z': '3d1322292e2a052e7234aafad001233a',
    'enwiki-20161101-pages-meta-history3.xml-p000169749p000185865.7z': '9fd379d092f5fd24d42fcb1df8b75c5f',
    'enwiki-20161101-pages-meta-history3.xml-p000185866p000200507.7z': '9b4519f75c94d86b54a80d4845e47a95',
    'enwiki-20161101-pages-meta-history4.xml-p000200511p000215170.7z': '70bf1bd43eda99edb96ab69c45fbf230',
    'enwiki-20161101-pages-meta-history4.xml-p000215173p000232405.7z': '6a53147cfcf671083b11af5c1d805013',
    'enwiki-20161101-pages-meta-history4.xml-p000232407p000248449.7z': 'ff284643c4f545988074d18506dc4177',
    'enwiki-20161101-pages-meta-history4.xml-p000248450p000266300.7z': 'd46fc11a439f8f3bc8f869eaf3d37078',
    'enwiki-20161101-pages-meta-history4.xml-p000266301p000289893.7z': '8a8ca6ca066745c6df250f7e58a3a8c4',
    'enwiki-20161101-pages-meta-history4.xml-p000289894p000305538.7z': 'cee4d76c4e34094c647c673dbdcd0142',
    'enwiki-20161101-pages-meta-history4.xml-p000305539p000333012.7z': '91f31d1d773af3552246a7875bdc0324',
    'enwiki-20161101-pages-meta-history4.xml-p000333013p000352689.7z': 'e05e313837505b49b2d9ce6c2be03e63',
    'enwiki-20161101-pages-meta-history5.xml-p000352690p000374090.7z': 'fb8527d262d0a3477b8ec4b8cd444239',
    'enwiki-20161101-pages-meta-history5.xml-p000374091p000399401.7z': '6f0ffdf21a87d7be368b4a9fb8e3cdd8',
    'enwiki-20161101-pages-meta-history5.xml-p000399402p000420317.7z': 'a03db8fe36bc8c711d717c898596a369',
    'enwiki-20161101-pages-meta-history5.xml-p000420318p000440017.7z': '78e15ec2b5714ec8a325a8eaff911d08',
    'enwiki-20161101-pages-meta-history5.xml-p000440018p000466358.7z': '87cec3223230be26dcd577f4a8cea9a2',
    'enwiki-20161101-pages-meta-history5.xml-p000466359p000489651.7z': 'f848ce74ee59ed938a227e10c3cc9360',
    'enwiki-20161101-pages-meta-history5.xml-p000489652p000518009.7z': '2d26efe02cec3ebab9319fbe41e48bd5',
    'enwiki-20161101-pages-meta-history5.xml-p000518010p000549136.7z': 'e07b1c2fd2e30afd660b8b36a2c61b6e',
    'enwiki-20161101-pages-meta-history5.xml-p000549137p000565313.7z': 'bb129fd6ca7fb08f7b6e9eb0b6a89360',
    'enwiki-20161101-pages-meta-history6.xml-p000565314p000599275.7z': '0f41fe5020851b58f42a944fc3ba3a68',
    'enwiki-20161101-pages-meta-history6.xml-p000599276p000630613.7z': '54be5be98c04623116e6ebd852068548',
    'enwiki-20161101-pages-meta-history6.xml-p000630614p000670279.7z': '8964ce954b328995884bccf650798d85',
    'enwiki-20161101-pages-meta-history6.xml-p000670280p000714309.7z': '27ab9d1a98f6f320b0c7a1a62d5df140',
    'enwiki-20161101-pages-meta-history6.xml-p000714310p000762037.7z': 'dc6298f08b113e612bb6c1d03570ba63',
    'enwiki-20161101-pages-meta-history6.xml-p000762038p000839347.7z': '78993e20abbf03ec97e4145d30e11513',
    'enwiki-20161101-pages-meta-history6.xml-p000839348p000892912.7z': 'b0a67b668364f0fefad4500e56722af7',
    'enwiki-20161101-pages-meta-history7.xml-p000892914p000939583.7z': '588444f64946f6cdaa63d2ae9c34930e',
    'enwiki-20161101-pages-meta-history7.xml-p000939584p000972034.7z': '5f41f93ef52031b4c7aed70152f9ebcf',
    'enwiki-20161101-pages-meta-history7.xml-p000972035p001011001.7z': 'b53eca9eb6127d0d8841b46fccbdae15',
    'enwiki-20161101-pages-meta-history7.xml-p001011002p001063240.7z': 'b2544f95a85c93f937c73a78df4327c0',
    'enwiki-20161101-pages-meta-history7.xml-p001063241p001127973.7z': 'e460d79bd40c3cc0cc17d451a2e9d3c2',
    'enwiki-20161101-pages-meta-history7.xml-p001127976p001203587.7z': 'e53ef2747aac138b30943687bb245d0a',
    'enwiki-20161101-pages-meta-history7.xml-p001203588p001268691.7z': '7de36cbb1592c75342b0f429dddb79d0',
    'enwiki-20161101-pages-meta-history8.xml-p001268692p001348475.7z': '222c76baccd0735738867ed262077bf1',
    'enwiki-20161101-pages-meta-history8.xml-p001348476p001442630.7z': '75c1b42662f89a5df7442a01d800154f',
    'enwiki-20161101-pages-meta-history8.xml-p001442631p001509377.7z': '1f8cc935d81e1d707da1f5456960281b',
    'enwiki-20161101-pages-meta-history8.xml-p001509378p001589660.7z': '4538579b9cc9d7578039682f2fde9ec7',
    'enwiki-20161101-pages-meta-history8.xml-p001589661p001658629.7z': '8289337a16b0ca1c8e727258d736b054',
    'enwiki-20161101-pages-meta-history8.xml-p001658632p001743794.7z': '2f8486e073c9010a31a4d64ac6892fc2',
    'enwiki-20161101-pages-meta-history8.xml-p001743795p001791079.7z': '22746d66aec7458d960181b623f27bc7',
    'enwiki-20161101-pages-meta-history9.xml-p001791080p001882142.7z': '5f115d6fae48455fb8c163ba3e0f5a47',
    'enwiki-20161101-pages-meta-history9.xml-p001882144p001966369.7z': '9b5cef1bf74a3792ae942ea2a14a407c',
    'enwiki-20161101-pages-meta-history9.xml-p001966373p002071290.7z': 'fc7810a3aee3e2e2b399eebda7246fed',
    'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z': '89b744f3ed3d7ebde47c3ac6f41fd35f',
    'enwiki-20161101-pages-meta-history9.xml-p002171782p002234301.7z': 'dd1d6fe5c9bdf0c6a923747e1977f081',
    'enwiki-20161101-pages-meta-history9.xml-p002234302p002300053.7z': '5ca01bb604300b7d845285c0f902c428',
    'enwiki-20161101-pages-meta-history9.xml-p002300055p002336422.7z': '503a704ef40a9897a131e4a8002f5be9',
    'enwiki-20161101-pages-meta-history10.xml-p002336425p002435847.7z': 'e4f381b19a428b59665a4e2001aae412',
    'enwiki-20161101-pages-meta-history10.xml-p002435851p002535875.7z': '591b39bd3e65b0fff68f370cdc89d85d',
    'enwiki-20161101-pages-meta-history10.xml-p002535877p002581444.7z': 'f066f68d58a3977ef544b77b78d5efcc',
    'enwiki-20161101-pages-meta-history10.xml-p002581445p002691952.7z': '2694160fbb14495d34e5506b67aa7c24',
    'enwiki-20161101-pages-meta-history10.xml-p002691956p002849569.7z': '236c6fa2e843e34f66626669a6a339c1',
    'enwiki-20161101-pages-meta-history10.xml-p002849571p003005539.7z': 'eb756ba0da5de59031a8c1061182c687',
    'enwiki-20161101-pages-meta-history10.xml-p003005540p003046511.7z': '832b82c23269200341c1944f928e9fa4',
    'enwiki-20161101-pages-meta-history11.xml-p003046514p003194626.7z': '5328d5ae0f64a332c119d5e75f4a203a',
    'enwiki-20161101-pages-meta-history11.xml-p003194627p003302194.7z': '02ba70e492fcb2971eb23eeea595eb2a',
    'enwiki-20161101-pages-meta-history11.xml-p003302196p003440074.7z': '882eee2b00d8b64658ebcedace7f95b8',
    'enwiki-20161101-pages-meta-history11.xml-p003440077p003551190.7z': '70ef3e803500a47cd52404072057d5a6',
    'enwiki-20161101-pages-meta-history11.xml-p003551191p003706897.7z': '34137937949e8e1ec958222bf9326cc8',
    'enwiki-20161101-pages-meta-history11.xml-p003706899p003851163.7z': '7780f0a0cad0629600b5708858837da5',
    'enwiki-20161101-pages-meta-history11.xml-p003851164p003926861.7z': '697b9d73dd3930a60b5a8d987350eff1',
    'enwiki-20161101-pages-meta-history12.xml-p003926863p004118137.7z': 'c5d1446cebda1ee2d3e73e25767566d3',
    'enwiki-20161101-pages-meta-history12.xml-p004118138p004287575.7z': 'e06180d64ff4188056cf5fcaa4a77bd9',
    'enwiki-20161101-pages-meta-history12.xml-p004287576p004490437.7z': '2e13fa1533e92b8df661f7fd58b01d31',
    'enwiki-20161101-pages-meta-history12.xml-p004490438p004676548.7z': 'afdeb9c77b90f4af9d0ae9be815e2f96',
    'enwiki-20161101-pages-meta-history12.xml-p004676550p004885254.7z': 'abf263ce87d81957c1648242f10053d0',
    'enwiki-20161101-pages-meta-history12.xml-p004885256p005040436.7z': '1f50ba67d3203d17ab7017bc4a586ca1',
    'enwiki-20161101-pages-meta-history13.xml-p005040438p005137507.7z': 'cc4bf2020555633308d87dcafa4f86b0',
    'enwiki-20161101-pages-meta-history13.xml-p005137508p005241141.7z': '4e4c10566fe0448b60cfe6704b274760',
    'enwiki-20161101-pages-meta-history13.xml-p005241144p005474162.7z': '3e166ba970b285e624395a3c6e818f9f',
    'enwiki-20161101-pages-meta-history13.xml-p005474163p005713311.7z': 'c1124d378016da75accb051bb61174d9',
    'enwiki-20161101-pages-meta-history13.xml-p005713312p006029141.7z': '0b031321a083639b75a64c5f84565db9',
    'enwiki-20161101-pages-meta-history13.xml-p006029142p006197594.7z': 'eeb54bccb6648d7270eddb0be79a2379',
    'enwiki-20161101-pages-meta-history14.xml-p006197598p006450254.7z': '1cb65a43b21e6cf335d380de1d798056',
    'enwiki-20161101-pages-meta-history14.xml-p006450255p006733137.7z': '824e285f5da4dfe5b1f5a2ac47a58e36',
    'enwiki-20161101-pages-meta-history14.xml-p006733138p006933850.7z': '72a545b9ae07fa93f4afeb98324ecfd8',
    'enwiki-20161101-pages-meta-history14.xml-p006933851p007213418.7z': 'ee74a9fd95beb3628bea747199c7b5d2',
    'enwiki-20161101-pages-meta-history14.xml-p007213419p007527410.7z': '4072b56220e5f35d7d8919374177dbd6',
    'enwiki-20161101-pages-meta-history14.xml-p007527411p007744799.7z': '6f39cb79fa9e74c3227c5901834c244f',
    'enwiki-20161101-pages-meta-history15.xml-p007744803p007991087.7z': 'f81799da3ffe88e74db8010f88b5bf69',
    'enwiki-20161101-pages-meta-history15.xml-p007991091p008292517.7z': '94da86ccf32ae861fb7bd9d9c005cca3',
    'enwiki-20161101-pages-meta-history15.xml-p008292519p008592058.7z': '7dc1a5239fe54af9c2c453da427c76a5',
    'enwiki-20161101-pages-meta-history15.xml-p008592059p008821460.7z': '99946e2343e289232bbd6ec22471672e',
    'enwiki-20161101-pages-meta-history15.xml-p008821462p009133229.7z': '229b70a9d4443f78ebb6cbf601a4b79e',
    'enwiki-20161101-pages-meta-history15.xml-p009133230p009467930.7z': '0f9decaf910732c7ffe6832b25dc0352',
    'enwiki-20161101-pages-meta-history15.xml-p009467931p009518048.7z': '3396ae3de96ef7587004d8fe18b31457',
    'enwiki-20161101-pages-meta-history16.xml-p009518050p009870625.7z': '4d030c54c94b0cc64ec9c31ddbfc458d',
    'enwiki-20161101-pages-meta-history16.xml-p009870626p010182410.7z': '7c5d070e766ca2ba439584899cd11998',
    'enwiki-20161101-pages-meta-history16.xml-p010182412p010463377.7z': '63e09d461a022fc3b78fcc77817f7dbf',
    'enwiki-20161101-pages-meta-history16.xml-p010463379p010678733.7z': 'e9b4b0524c3474972eb70302eeffbdde',
    'enwiki-20161101-pages-meta-history16.xml-p010678734p010846406.7z': 'eac69253346676f2c59c9fefd66cb94c',
    'enwiki-20161101-pages-meta-history16.xml-p010846407p011035889.7z': 'a14f48ff20dac6e9fd410350844e6645',
    'enwiki-20161101-pages-meta-history16.xml-p011035891p011281693.7z': 'a3c0e3f30255871c2ee6f448942d0600',
    'enwiki-20161101-pages-meta-history16.xml-p011281695p011539266.7z': 'b7d1420a7d4477ea6b482bf903755105',
    'enwiki-20161101-pages-meta-history17.xml-p011539268p011923328.7z': '69046f1bddc39247eee482379d6a0a32',
    'enwiki-20161101-pages-meta-history17.xml-p011923329p012230730.7z': '90e4a54caa939ed8a2d80776b8c1412f',
    'enwiki-20161101-pages-meta-history17.xml-p012230731p012650082.7z': '5b7425235aca70c3a38ec786390f2eec',
    'enwiki-20161101-pages-meta-history17.xml-p012650083p012981701.7z': 'f0b31522f3d880ac628ee74021f8bec6',
    'enwiki-20161101-pages-meta-history17.xml-p012981702p013196977.7z': 'f5c50de4f8753cc09df535503b232158',
    'enwiki-20161101-pages-meta-history17.xml-p013196978p013553422.7z': '888e5446340ad42cf3ab022fcfaf0fc4',
    'enwiki-20161101-pages-meta-history17.xml-p013553424p013693071.7z': '8da9dd0e95dc429e90b21f1c7ef32f4c',
    'enwiki-20161101-pages-meta-history18.xml-p013693074p014138941.7z': '132c911d32421cab60be91e1e5c24b25',
    'enwiki-20161101-pages-meta-history18.xml-p014138942p014545880.7z': '45e16d74cc2ba26bbc1e9c3e7c02af5f',
    'enwiki-20161101-pages-meta-history18.xml-p014545881p014981310.7z': '9de4a88595261445eef0ce71bdb5edd2',
    'enwiki-20161101-pages-meta-history18.xml-p014981311p015365487.7z': '11d694c9fb2c79e06c12f52e47efac33',
    'enwiki-20161101-pages-meta-history18.xml-p015365489p015794038.7z': 'f3dc46fc635a04724117c44890634a90',
    'enwiki-20161101-pages-meta-history18.xml-p015794039p016120542.7z': 'd2876bcaffc68640f2c5f30b1be3edd1',
    'enwiki-20161101-pages-meta-history19.xml-p016120543p016666495.7z': '0f544f80cf352d6c37beee3201c1e43a',
    'enwiki-20161101-pages-meta-history19.xml-p016666496p017005674.7z': '9ce9588c4620108a52346bb0b3b8a82f',
    'enwiki-20161101-pages-meta-history19.xml-p017005675p017473337.7z': '7dce1301dc90d5afe6381d855d738817',
    'enwiki-20161101-pages-meta-history19.xml-p017473338p017895853.7z': '165d169e773c5bda5b7f077ee10fb40a',
    'enwiki-20161101-pages-meta-history19.xml-p017895854p018401310.7z': 'ed3c47b3c4cb07048cd78a81079242d7',
    'enwiki-20161101-pages-meta-history19.xml-p018401311p018707123.7z': '49d93bbbbb88cc8eb73dbf9877c22ef5',
    'enwiki-20161101-pages-meta-history19.xml-p018707124p018754735.7z': 'e26b9fa05bfff50498d239928651dbc4',
    'enwiki-20161101-pages-meta-history20.xml-p018754736p018984527.7z': 'e27f70c81f9359685ce3cc856e186bb1',
    'enwiki-20161101-pages-meta-history20.xml-p018984530p019283913.7z': '85b9eeaf4649aa41ee46633d81016d84',
    'enwiki-20161101-pages-meta-history20.xml-p019283915p019630120.7z': '8632cc2b8705ead37571d64eae830e21',
    'enwiki-20161101-pages-meta-history20.xml-p019630121p020023800.7z': '64de89bf74302b8ce2b74e3aee17db0b',
    'enwiki-20161101-pages-meta-history20.xml-p020023802p020568030.7z': 'a9284cda88892ab1b934d6bcc9816263',
    'enwiki-20161101-pages-meta-history20.xml-p020568031p020947270.7z': '4909140f34c19eaf4ace062a76bb4fc6',
    'enwiki-20161101-pages-meta-history20.xml-p020947271p021222156.7z': '50a82233d08d60892a8235b0302cc946',
    'enwiki-20161101-pages-meta-history21.xml-p021222158p021597628.7z': '238afa2fc66d2d6c34442d31ac678767',
    'enwiki-20161101-pages-meta-history21.xml-p021597629p022144990.7z': '1599f0e4c0e478746b6f1086b0448ccb',
    'enwiki-20161101-pages-meta-history21.xml-p022144991p022644924.7z': 'b76c43d78ebfdda14cc3cb1064b5acd7',
    'enwiki-20161101-pages-meta-history21.xml-p022644925p023075753.7z': '6678882d32c321ae6f85bebc2321b104',
    'enwiki-20161101-pages-meta-history21.xml-p023075754p023450469.7z': '12c0e0df97bd62f39af22c6b34184e18',
    'enwiki-20161101-pages-meta-history21.xml-p023450470p023881940.7z': '59810eb7bee80e375eafb85a17bbae5b',
    'enwiki-20161101-pages-meta-history21.xml-p023881941p023927983.7z': '0e7672f51a3c3277caabc814526635c9',
    'enwiki-20161101-pages-meta-history22.xml-p023927984p024402957.7z': '5488adcababe56eeeca86d106072d1ae',
    'enwiki-20161101-pages-meta-history22.xml-p024402958p024971758.7z': '8c0129d36135087fc2e37b0e3284763f',
    'enwiki-20161101-pages-meta-history22.xml-p024971759p025465210.7z': '77b1ffbc4ab5d908d05c133f8028bbf4',
    'enwiki-20161101-pages-meta-history22.xml-p025465211p025862556.7z': '102976a8c9982a54f18ec3de98f9ff14',
    'enwiki-20161101-pages-meta-history22.xml-p025862557p026401197.7z': 'f5d87ddaabcc31f694ef5b4a0f97c6d7',
    'enwiki-20161101-pages-meta-history22.xml-p026401199p026823660.7z': '31b51aec196c014dc7a465e78ab199ee',
    'enwiki-20161101-pages-meta-history23.xml-p026823661p027412020.7z': '7eca7d49acb8e48d8e6409f66d1d6c21',
    'enwiki-20161101-pages-meta-history23.xml-p027412021p027888808.7z': '700183ab482662a5a3004e8a06fc839a',
    'enwiki-20161101-pages-meta-history23.xml-p027888812p028517606.7z': '71b09cf78ffa87294efb2ce9f62944ec',
    'enwiki-20161101-pages-meta-history23.xml-p028517607p029252556.7z': '7f97b773f8381f71cf5915b1ff730243',
    'enwiki-20161101-pages-meta-history23.xml-p029252557p030010039.7z': '346ee279e27e86f7756a8f5d85c9c842',
    'enwiki-20161101-pages-meta-history23.xml-p030010040p030503449.7z': '74eb996139821d898fe0ca09033a05ba',
    'enwiki-20161101-pages-meta-history24.xml-p030503451p030986053.7z': 'cfb6410ff1e0f548545e8f5e505e8684',
    'enwiki-20161101-pages-meta-history24.xml-p030986054p031586084.7z': '6d5f580f6f47f416e3bf079933b9707c',
    'enwiki-20161101-pages-meta-history24.xml-p031586085p031964579.7z': 'edff45258109839f78879a42bd45a81c',
    'enwiki-20161101-pages-meta-history24.xml-p031964580p032320879.7z': '4f87c1d8cfa27fa7cce2a9bac5f05594',
    'enwiki-20161101-pages-meta-history24.xml-p032320880p033018116.7z': '0eb524998ade5e024881df919b1f7d7d',
    'enwiki-20161101-pages-meta-history24.xml-p033018117p033710212.7z': '22ed19a7c94a7c1aa39fd68259ac75f7',
    'enwiki-20161101-pages-meta-history24.xml-p033710213p033952815.7z': '2d0423c9b713d42cf477c376d8bbfefe',
    'enwiki-20161101-pages-meta-history25.xml-p033952816p034560493.7z': '2c6e236c28df6b9f80918a36673d2294',
    'enwiki-20161101-pages-meta-history25.xml-p034560494p035220547.7z': 'f3d61133ff06c30562a2e6a2a91c7192',
    'enwiki-20161101-pages-meta-history25.xml-p035220549p035966255.7z': 'ab9aa135902274d1f356bf4a9c4ef2ce',
    'enwiki-20161101-pages-meta-history25.xml-p035966256p036622171.7z': '2c325a425b69202d4634a38518494bc5',
    'enwiki-20161101-pages-meta-history25.xml-p036622172p037245040.7z': 'd117f88f9b1eb7e6600f8177ac6ea781',
    'enwiki-20161101-pages-meta-history25.xml-p037245041p037969115.7z': 'bfa5bd87a075bd4308c9c113a8bc7c73',
    'enwiki-20161101-pages-meta-history25.xml-p037969116p038067202.7z': '99e5b002d25c62adfc2087c2bd545c36',
    'enwiki-20161101-pages-meta-history26.xml-p038067203p038758344.7z': '8f7271d6063b64ea6265984683459a31',
    'enwiki-20161101-pages-meta-history26.xml-p038758347p039469556.7z': '957ac8deead421433ead9190f22247a5',
    'enwiki-20161101-pages-meta-history26.xml-p039469557p040183377.7z': 'c9f7e03f439e1e4cb8eb25bc32fc09c9',
    'enwiki-20161101-pages-meta-history26.xml-p040183379p041054777.7z': '410ce87ec62fb11ccef06ed0b4f66c45',
    'enwiki-20161101-pages-meta-history26.xml-p041054778p041814100.7z': '7cfeacb20915142a28a109718ec66387',
    'enwiki-20161101-pages-meta-history26.xml-p041814101p042658202.7z': '1c76a7e5a2ad15a82316333fea48113f',
    'enwiki-20161101-pages-meta-history26.xml-p042658203p042663461.7z': '0a9a0df6000c64699440c578ab7bddef',
    'enwiki-20161101-pages-meta-history27.xml-p042663462p043359606.7z': '87937f2602fe962075cb3e73a5bbcb8a',
    'enwiki-20161101-pages-meta-history27.xml-p043359607p044069413.7z': 'c3fd8721470ff2b23bd0d8a0f142c686',
    'enwiki-20161101-pages-meta-history27.xml-p044069415p044983273.7z': 'ddd9230df3b5520fa2219cff855a8ed5',
    'enwiki-20161101-pages-meta-history27.xml-p044983274p046398887.7z': '6bcbd213edd65fe6f6762d799fdc75e0',
    'enwiki-20161101-pages-meta-history27.xml-p046398889p047253367.7z': 'a669bb9f676976328e9ec69ab60845ee',
    'enwiki-20161101-pages-meta-history27.xml-p047253368p048414110.7z': 'cb3205eaeaca6495bd4bad50fdf01125',
    'enwiki-20161101-pages-meta-history27.xml-p048414111p050501579.7z': '6c1c5dfe8c18001ef2614cd0f80d3170',
    'enwiki-20161101-pages-meta-history27.xml-p050501581p052158771.7z': '49e07b8af892605319213e329143b920',
}
