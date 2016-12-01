# -*- coding: utf-8 -*-
"""
These are integration tests to test behaviour of wikiwho algorithm.

To run only test_authorship test calls:
py.test test_wikiwho_simple.py::TestWikiwho::test_authorship
To run only test_json_output test calls:
py.test test_wikiwho_simple.py::TestWikiwho::test_json_output
To run tests on specific lines of input excel:
py.test test_wikiwho_simple.py --lines=3,9
py.test test_wikiwho_simple.py::TestWikiwho::test_authorship --lines=3,9
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import range

from openpyxl import load_workbook
import os
import sys
import pytest
import json
import filecmp
import io

from api.handler import WPHandler
from wikiwho.utils import splitIntoWords
from api.views import WikiwhoApiView

# TODO use django's default test tool: https://docs.djangoproject.com/en/1.10/topics/testing/


def pytest_generate_tests(metafunc):
    """
    Generates tests dynamically according to lines command option.
    :param metafunc:
    :return:
    """
    # print(metafunc)  # http://docs.pytest.org/en/latest/parametrize.html#the-metafunc-object
    # print(metafunc.config.option.lines)
    articles = set()
    lines = metafunc.config.option.lines
    lines = [] if lines == 'all' else [int(l) for l in lines.split(',')]
    if "article_name" in metafunc.fixturenames:
        input_file = '{}/{}'.format(os.path.dirname(os.path.realpath(__file__)), 'test_wikiwho_simple.xlsx')
        wb = load_workbook(filename=input_file, data_only=True, read_only=True)
        ws = wb[wb.sheetnames[0]]
        for i, row in enumerate(ws.iter_rows()):
            if i == 0 or lines and i+1 not in lines:
                continue
            if not row[0].value:
                break
            article_name = row[0].value.replace(' ', '_')
            if 'token' in metafunc.fixturenames:
                funcargs = {
                    'article_name': article_name,
                    'revision_ids': [int(row[2].value)],
                    'token': '{}'.format(row[3].value).lower(),
                    'context': '{}'.format(row[4].value).lower(),
                    'correct_rev_id': int(row[5].value),
                }
                metafunc.addcall(funcargs=funcargs)
            elif article_name not in articles and 'revision_id_start' in metafunc.fixturenames:
                articles.add(article_name)
                funcargs = {
                    'article_name': article_name,
                    'revision_id_start': int(row[5].value),
                    'revision_id_end': int(row[2].value),
                }
                metafunc.addcall(funcargs=funcargs)
            elif article_name not in articles:
                articles.add(article_name)
                funcargs = {
                    'article_name': article_name,
                    'revision_ids': [int(row[2].value)],
                }
                metafunc.addcall(funcargs=funcargs)

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestWikiwho:
    pytestmark = pytest.mark.django_db

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        # sys.path.append(os.path.dirname(os.path.realpath(__file__)))

    @pytest.fixture(scope='session')
    def temp_folder(self, tmpdir_factory):
        """
        Creates temporary folder for whole test session.
        :param tmpdir_factory:
        :return:
        """
        if int(sys.version[0]) > 2:
            tmp = 'tmp_test_3'
        else:
            tmp = 'tmp_test'
        if not os.path.exists(tmp):
            os.mkdir(tmp)
        tmp1 = '{}/test_authorship'.format(tmp)
        if not os.path.exists(tmp1):
            os.mkdir(tmp1)
        tmp2 = '{}/test_json_output'.format(tmp)
        if not os.path.exists(tmp2):
            os.mkdir(tmp2)
        tmp3 = '{}/test_continue_logic'.format(tmp)
        if not os.path.exists(tmp3):
            os.mkdir(tmp3)
        return tmp
        # in os' tmp dir
        # return tmpdir_factory.getbasetemp()

    def test_json_output(self, temp_folder, article_name, revision_ids):
        """
        Tests json outputs of articles in given revisions in gold standard. If there are expected differences in
        jsons, authorship of each token in gold standard should be checked manually.
        :param revision_ids: Revision id where authorship of token in gold standard is tested.
        """
        temp_folder = '{}/test_json_output'.format(temp_folder)
        test_json_folder = 'test_jsons'

        with WPHandler(article_name, temp_folder) as wp:
            wp.handle(revision_ids, 'json', is_api=False)
        # pickle_revision_json = wp.wikiwho.get_revision_json(wp.revision_ids, {'rev_id', 'author', 'token_id'})

        v = WikiwhoApiView()
        v.article = wp.article_obj

        # create json with rev and author ids
        revision_json_without_tokenid = v.get_revision_json(wp.revision_ids, {'rev_id', 'author'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        # compare jsons with rev and author ids
        test_json_file_path = '{}/{}_db_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same_1 = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)

        # create json with token ids
        revision_json = v.get_revision_json(wp.revision_ids, {'token_id'})
        # check if all token ids are unique
        for _, rev in revision_json['revisions'][0].items():
            token_ids = [t['token_id'] for t in rev['tokens']]
            assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(article_name)
            break
        # compare jsons with token ids
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        test_json_file_path = '{}/{}_db_ti.json'.format(test_json_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        is_content_same_2 = filecmp.cmp(json_file_path, test_json_file_path)

        # create json with in/outbounds
        revision_json_with_io = v.get_revision_json(wp.revision_ids, {'inbound', 'outbound'})
        json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
        with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        # compare jsons with in/outbounds
        test_json_file_path = '{}/{}_db_io.json'.format(test_json_folder, article_name)
        is_content_same_3 = filecmp.cmp(json_file_path_with_io, test_json_file_path)

        assert is_content_same_1, "{}: 'json with ri and ai doesn't match".format(article_name)
        assert is_content_same_2, "{}: json with ti doesn't match".format(article_name)
        assert is_content_same_3, "{}: 'json with in/outbounds doesn't match".format(article_name)

    def test_json_output_xml(self, temp_folder, article_name, revision_ids):
        """
        Tests json outputs of articles in given revisions in gold standard from xml dump.
        If there are expected differences in jsons, authorship of each token in gold standard should be
        checked manually.
        The xml file dumps taken from here: https://dumps.wikimedia.org/enwiki/20161101/
        :param revision_ids: Revision id where authorship of token in gold standard is tested.
        """
        temp_folder = '{}/test_json_output_xml'.format(temp_folder)
        test_json_folder = 'test_jsons'

        from mwxml import Dump
        from mwtypes.files import reader
        # faster: read from gold standard articles xml
        # xml_file_path = 'test_jsons/gold_standard_articles_20161101.xml'
        # slower: read from xml dumps (7z)
        xml_file_path = 'test_jsons/{}'.format(article_zips[article_name])
        dump = Dump.from_file(reader(xml_file_path))
        article_name = article_name.replace(' ', '_')
        title_matched = False
        for page in dump:
            if page.title.replace(' ', '_') == article_name:
                title_matched = True
                with WPHandler(article_name, temp_folder) as wp:
                    wp.handle_from_xml(page)
                break

        assert title_matched, '{}--{}'.format(article_name, page.title)

        v = WikiwhoApiView()
        v.article = wp.article_obj

        # create json with rev and author ids
        revision_json_without_tokenid = v.get_revision_json(revision_ids, {'rev_id', 'author'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        # compare jsons with rev and author ids
        test_json_file_path = '{}/{}_db_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same_1 = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)

        # create json with token ids
        revision_json = v.get_revision_json(revision_ids, {'token_id'})
        # check if all token ids are unique
        for _, rev in revision_json['revisions'][0].items():
            token_ids = [t['token_id'] for t in rev['tokens']]
            assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(article_name)
            break
        # compare jsons with token ids
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        test_json_file_path = '{}/{}_db_ti.json'.format(test_json_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        is_content_same_2 = filecmp.cmp(json_file_path, test_json_file_path)

        # create json with in/outbounds
        revision_json_with_io = v.get_revision_json(revision_ids, {'inbound', 'outbound'})
        json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
        with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        # compare jsons with in/outbounds
        # test_json_file_path = '{}/{}_db_io.json'.format(test_json_folder, article_name)
        # is_content_same_3 = filecmp.cmp(json_file_path_with_io, test_json_file_path)

        assert is_content_same_1, "{}: 'json with ri and ai doesn't match".format(article_name)
        assert is_content_same_2, "{}: json with ti doesn't match".format(article_name)
        # assert is_content_same_3, "{}: 'json with in/outbounds doesn't match".format(article_name)

    def test_continue_logic(self, temp_folder, article_name, revision_id_start, revision_id_end):
        """
        :param revision_id_start: Correct revision id of first token of article in gold standard.
        :param revision_id_end: Revision id where authorship of token in gold standard is tested.
        """
        temp_folder = '{}/test_continue_logic'.format(temp_folder)
        test_json_folder = 'test_jsons'

        # first create article and revisions until revision_id_start
        with WPHandler(article_name, temp_folder) as wp:
            wp.handle([revision_id_start], 'json', is_api=False)

        assert wp.article_obj is not None

        # continue creating revisions of this article until revision_id_end
        with WPHandler(article_name, temp_folder) as wp:
            wp.handle([revision_id_end], 'json', is_api=False)

        v = WikiwhoApiView()
        v.article = wp.article_obj

        # compare jsons without token ids
        revision_json_without_tokenid = v.get_revision_json(wp.revision_ids, {'rev_id', 'author'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_db_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)
        assert is_content_same, "{}: 'json without token ids' doesn't match".format(article_name)

        # compare jsons with token ids
        revision_json = v.get_revision_json(wp.revision_ids, {'token_id'})
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_db_ti.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path, test_json_file_path)
        assert is_content_same, "{}: json doesn't match".format(article_name)

        # compare jsons with in/outbounds
        revision_json_with_io = v.get_revision_json(wp.revision_ids, {'inbound', 'outbound'})
        json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
        with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_db_io.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_with_io, test_json_file_path)
        assert is_content_same, "{}: 'json with in/outbounds' doesn't match".format(article_name)

    def test_finger_lakes(self, temp_folder):
        """
        Tests in/outbounds through finger lake dummy article.
        """
        data = {
            0: {
                'used': [[0], [0], [0], [0], [0], [0], [0], [0]],
                'inbound': [[], [], [], [], [], [], [], []],
                'outbound': [[], [], [], [], [], [], [], []],
            },
            1: {
                'used': [[0, 1], [1], [0, 1], [0, 1], [0, 1], [1], [0, 1], [0, 1], [1], [1], [1], [1], [1], [1]],
                'inbound': [[], [], [], [], [], [], [], [], [], [], [], [], [], []],
                'outbound': [[], [], [], [], [], [], [], [], [], [], [], [], [], []],
            },
            2: {
                'used': [[0, 1, 2], [1, 2], [0, 1, 2], [0, 1, 2], [0, 1, 2], [1, 2], [0, 1, 2], [0, 1, 2]],
                'inbound': [[], [], [], [], [], [], [], []],
                'outbound': [[], [], [], [], [], [], [], []],
            },
            3: {
                'used': [[0, 1, 2, 3], [1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [1, 2, 3], [0, 1, 2, 3], [0, 1, 2, 3], [1, 3], [1, 3], [1, 3], [1, 3], [1, 3], [1, 3]],
                'inbound': [[], [], [], [], [], [], [], [], [3], [3], [3], [3], [3], [3]],
                'outbound': [[], [], [], [], [], [], [], [], [2], [2], [2], [2], [2], [2]],
            },
            4: {
                'used': [[0, 1, 2, 3, 4], [1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [1, 2, 3, 4], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4], [1, 3, 4], [1, 3, 4], [1, 3, 4], [1, 3, 4], [4], [4]],
                'inbound': [[], [], [], [], [], [], [], [], [3], [3], [3], [3], [], []],
                'outbound': [[], [], [], [], [], [], [], [], [2], [2], [2], [2], [], []],
            },
            5: {
                'used': [[0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [5], [5], [0, 1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5], [1, 3, 4, 5], [1, 3, 4, 5], [1, 3, 4, 5], [1, 3, 4, 5], [4, 5], [4, 5]],
                'inbound': [[], [], [], [], [], [], [], [], [3], [3], [3], [3], [], []],
                'outbound': [[], [], [], [], [], [], [], [], [2], [2], [2], [2], [], []],
            },
            6: {
                'used': [[0, 1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6], [0, 1, 2, 3, 4, 6], [0, 1, 2, 3, 4, 6], [0, 1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6], [0, 1, 2, 3, 4, 5, 6], [0, 1, 2, 3, 4, 5, 6], [1, 3, 4, 5, 6], [1, 3, 4, 5, 6], [1, 3, 4, 5, 6], [1, 3, 4, 5, 6], [4, 5, 6], [4, 5, 6]],
                'inbound': [[], [], [6], [6], [], [], [], [], [3], [3], [3], [3], [], []],
                'outbound': [[], [], [5], [5], [], [], [], [], [2], [2], [2], [2], [], []],
            },
            27: {
                'used': [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [26, 27], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27], [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [25, 26, 27], [25, 26, 27], [25, 26, 27], [4, 5, 6, 7, 8, 9, 10, 12, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [7, 8, 9, 10, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [7, 8, 9, 10, 12, 13, 15, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27], [8, 9, 10, 12, 13, 15, 17, 18, 19, 22, 23, 24, 25, 26, 27], [9, 10, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [8, 9, 10, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27], [27], [10, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]],
                'inbound': [[12, 15, 17], [12, 15, 17], [6, 12, 15, 17], [6, 12, 15, 17, 19], [12, 15, 17, 21], [12, 15, 17], [ ], [12, 15, 17], [12, 15, 17], [3, 12, 15, 17], [3, 12, 15, 17, 19], [3, 12, 15, 17], [3, 12, 15, 17], [], [], [], [12, 15, 17], [12, 15, 17], [12, 15, 17, 19], [12, 15, 17, 22], [12, 15, 17], [12, 15, 17], [], [12, 15, 17]],
                'outbound': [[11, 13, 16], [11, 13, 16], [5, 11, 13, 16], [5, 11, 13, 16, 18], [11, 13, 16, 20], [11, 13, 16], [ ], [11, 13, 16], [11, 13, 16], [2, 11, 13, 16], [2, 11, 13, 16, 18], [2, 11, 13, 16], [2, 11, 13, 16], [], [], [], [11, 13, 16], [11, 14, 16], [11, 14, 16, 18], [11, 14, 16, 20], [11, 14, 16], [11, 14, 16], [], [11, 14, 16]],
            }
        }
        article_name = 'Finger_Lakes'
        tests = os.path.dirname(os.path.realpath(__file__))
        from copy import deepcopy
        from django.core import management
        management.call_command('xml_to_pickle', *['--output', tests])

        with WPHandler(article_name, tests, save_into_pickle=True, save_into_db=False) as wp:
            for rev_id, rev in wp.wikiwho.revisions.items():
                if rev_id not in data.keys():
                    continue
                i = 0
                ps_copy = deepcopy(rev.paragraphs)
                for hash_paragraph in rev.ordered_paragraphs:
                    paragraph = ps_copy[hash_paragraph].pop(0)
                    for hash_sentence in paragraph.ordered_sentences:
                        sentence = paragraph.sentences[hash_sentence].pop(0)
                        for word in sentence.words:
                            # used = [x for x in word.used if x <= rev_id]
                            inbound = [x for x in word.inbound if x <= rev_id]
                            outbound = [x for x in word.outbound if x <= rev_id]
                            # assert used == data[rev_id]['used'][i], 'used does not match, rev id: {} - {}'.format(rev_id, i)
                            assert inbound == data[rev_id]['inbound'][i], 'inbound does not match, rev id: {} - {}'.format(rev_id, i)
                            assert outbound == data[rev_id]['outbound'][i], 'outbound does not match, rev id: {} - {}'.format(rev_id, i)
                            i += 1

            wp._save_article_into_db()
            for rev in wp.article_obj.revisions.all().order_by('id'):
                rev_id = rev.id
                if rev_id not in data.keys():
                    continue
                i = 0
                for p in rev.paragraphs.order_by('position'):
                    for s in p.paragraph.sentences.order_by('position'):
                        for t in s.sentence.tokens.order_by('position'):
                            used = [x for x in t.token.used if x <= rev_id]
                            inbound = [x for x in t.token.inbound if x <= rev_id]
                            outbound = [x for x in t.token.outbound if x <= rev_id]
                            assert used == data[rev_id]['used'][i], 'used does not match, rev id: {} - {} - db'.format(rev_id, i)
                            assert inbound == data[rev_id]['inbound'][i], 'inbound does not match, rev id: {} - {} - db'.format(rev_id, i)
                            assert outbound == data[rev_id]['outbound'][i], 'outbound does not match, rev id: {} - {} - db'.format(rev_id, i)
                            i += 1

    def test_authorship(self, temp_folder, article_name, revision_ids, token, context, correct_rev_id):
        """
        This is not needed anymore. Covered by 'test_json_output' case.
        """
        sub_text = splitIntoWords(context)
        with WPHandler(article_name, '{}/test_authorship'.format(temp_folder), save_into_pickle=True, save_into_db=False) as wp:
            wp.handle(revision_ids, 'json', is_api=False)

        # revision = wp.article_obj.revisions.get(id=revision_ids[0])
        # text_ = []
        # rev_ids_ = []
        # for data in revision.tokens.values('token', 'label_revision__id'):
        #     text_.append(data['token'])
        #     rev_ids_.append(data['label_revision__id'])
        # n = len(sub_text)
        # found = 0
        ww_db_rev_id = 0
        # for i in range(len(text_) - n + 1):
        #     if sub_text == text_[i:i + n]:
        #         token_i = i + sub_text.index(token)
        #         ww_db_rev_id = rev_ids_[token_i]
        #         found = 1
        #         break

        text, label_rev_ids = wp.wikiwho.get_revision_text(revision_ids[0])
        n = len(sub_text)
        found = 0
        # print(wp.wikiwho.spam)
        print(token, context)
        print(sub_text)
        for i in range(len(text) - n + 1):
            if sub_text == text[i:i + n]:
                token_i = i + sub_text.index(token)
                ww_rev_id = label_rev_ids[token_i]
                found = 1
                assert ww_rev_id == correct_rev_id, "1){}: {}: rev id was {} - {}, should be {}".format(article_name,
                                                                                                 token,
                                                                                                 ww_rev_id,
                                                                                                 ww_db_rev_id,
                                                                                                 correct_rev_id)
                # assert ww_db_rev_id == correct_rev_id, "2){}: {}: rev id was {} - {}, should be {}".format(article_name,
                #                                                                                  token,
                #                                                                                  ww_rev_id,
                #                                                                                  ww_db_rev_id,
                #                                                                                  correct_rev_id)
                break
        assert found, "{}: {} -> token not found".format(article_name, token)

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """
        # if sys.version[0] > 2:
        #     tmp = 'tmp_test_3'
        # else:
        #     tmp = 'tmp_test'
        # if os.path.exists(tmp):
        #     os.removedirs(tmp)


article_zips = {
    'Amstrad_CPC': 'enwiki-20161101-pages-meta-history1.xml-p000000010p000002289.7z',
    'Antarctica': 'enwiki-20161101-pages-meta-history20.xml-p018754736p018984527.7z',
    'Apollo_11': 'enwiki-20161101-pages-meta-history1.xml-p000000010p000002289.7z',
    'Armenian_Genocide': 'enwiki-20161101-pages-meta-history3.xml-p000118475p000143283.7z',
    'Barack_Obama': 'enwiki-20161101-pages-meta-history5.xml-p000518010p000549136.7z',
    'Bioglass': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Bothrops_jararaca': 'enwiki-20161101-pages-meta-history15.xml-p007991091p008292517.7z',
    'Chlorine': 'enwiki-20161101-pages-meta-history1.xml-p000004536p000006546.7z',
    'Circumcision': 'enwiki-20161101-pages-meta-history15.xml-p008592059p008821460.7z',
    'Communist_Party_of_China': 'enwiki-20161101-pages-meta-history1.xml-p000006547p000008653.7z',
    'Democritus': 'enwiki-20161101-pages-meta-history1.xml-p000006547p000008653.7z',
    'Diana,_Princess_of_Wales': 'enwiki-20161101-pages-meta-history1.xml-p000022917p000025445.7z',
    'Encryption': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Eritrean_Defence_Forces': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'European_Free_Trade_Association': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Evolution': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Geography_of_El_Salvador': 'enwiki-20161101-pages-meta-history1.xml-p000008654p000010882.7z',
    'Germany': 'enwiki-20161101-pages-meta-history1.xml-p000010883p000013026.7z',
    'Home_and_Away': 'enwiki-20161101-pages-meta-history3.xml-p000161222p000169747.7z',
    'Homeopathy': 'enwiki-20161101-pages-meta-history1.xml-p000013027p000015513.7z',
    'Iraq_War': 'enwiki-20161101-pages-meta-history13.xml-p005040438p005137507.7z',
    'Islamophobia': 'enwiki-20161101-pages-meta-history3.xml-p000161222p000169747.7z',
    'Jack_the_Ripper': 'enwiki-20161101-pages-meta-history14.xml-p006733138p006933850.7z',
    'Jesus': 'enwiki-20161101-pages-meta-history7.xml-p001063241p001127973.7z',
    'KLM_destinations': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Lemur': 'enwiki-20161101-pages-meta-history5.xml-p000466359p000489651.7z',
    'Macedonians_(ethnic_group)': 'enwiki-20161101-pages-meta-history5.xml-p000420318p000440017.7z',
    'Muhammad': 'enwiki-20161101-pages-meta-history1.xml-p000017892p000020545.7z',
    'Newberg,_Oregon': 'enwiki-20161101-pages-meta-history3.xml-p000118475p000143283.7z',
    'Race_and_intelligence': 'enwiki-20161101-pages-meta-history1.xml-p000025446p000028258.7z',
    'Rhapsody_on_a_Theme_of_Paganini': 'enwiki-20161101-pages-meta-history4.xml-p000215173p000232405.7z',
    'Robert_Hues': 'enwiki-20161101-pages-meta-history20.xml-p019630121p020023800.7z',
    "Saturn's_moons_in_fiction": 'enwiki-20161101-pages-meta-history14.xml-p006733138p006933850.7z',
    'Sergei_Korolev': 'enwiki-20161101-pages-meta-history2.xml-p000078261p000088444.7z',
    'South_Western_Main_Line': 'enwiki-20161101-pages-meta-history8.xml-p001348476p001442630.7z',
    'Special_Air_Service': 'enwiki-20161101-pages-meta-history2.xml-p000050799p000057690.7z',
    'The_Holocaust': 'enwiki-20161101-pages-meta-history16.xml-p010182412p010463377.7z',
    'Toshitsugu_Takamatsu': 'enwiki-20161101-pages-meta-history9.xml-p002071291p002171781.7z',
    'Vladimir_Putin': 'enwiki-20161101-pages-meta-history2.xml-p000032259p000034487.7z',
    'Wernher_von_Braun': 'enwiki-20161101-pages-meta-history2.xml-p000032259p000034487.7z'
}


def create_gold_xml():
    from collections import defaultdict
    files = defaultdict(list)
    for title, file_ in article_zips.items():
        file_ = 'wikiwho/tests/test_jsons/{}'.format(file_)
        files[file_].append(title)
    header = """
    <mediawiki xmlns="http://www.mediawiki.org/xml/export-0.5/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.5/
                 http://www.mediawiki.org/xml/export-0.5.xsd" version="0.5"
               xml:lang="en">
    <siteinfo>
    </siteinfo>
    """
    footer = "</mediawiki>"
    p = list(header)

    import os
    for xml_file, titles in files.items():
        # print(os.path.dirname(xml_file))
        os.system('7z x {} -o{}'.format(xml_file, os.path.dirname(xml_file)))
        xml_file = xml_file[:-3]
        p.append('<page>\n')
        add = False
        with open(xml_file, 'r') as f:
            for line in f:
                if not add:
                    for title in titles:
                        if '<title>{}</title>'.format(title) in line or '<title>{}</title>'.format(title.replace(' ', '_')) in line:
                            add = True
                            titles.remove(title)
                if add:
                    p.append(line)
                if add and '</page>' in line:
                    add = False
                    if not titles:
                        break
                    else:
                        p.append('<page>\n')
        os.remove(xml_file)

    p.append(footer)
    with open('gold_standard_articles_20161101.xml', 'a') as f:
        for line in p:
            f.write(line)

    print('done')
    return p
