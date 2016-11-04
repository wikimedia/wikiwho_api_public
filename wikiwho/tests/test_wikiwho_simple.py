# -*- coding: utf-8 -*-
"""
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

    def test_authorship(self, temp_folder, article_name, revision_ids, token, context, correct_rev_id):
        sub_text = splitIntoWords(context)
        with WPHandler(article_name, '{}/test_authorship'.format(temp_folder)) as wp:
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

    def test_json_output(self, temp_folder, article_name, revision_ids):
        temp_folder = '{}/test_json_output'.format(temp_folder)
        test_json_folder = 'test_jsons'

        with WPHandler(article_name, temp_folder) as wp:
            wp.handle(revision_ids, 'json', is_api=False)
        # pickle_revision_json = wp.wikiwho.get_revision_json(wp.revision_ids, {'rev_id', 'author_id', 'token_id'})

        v = WikiwhoApiView()
        v.article = wp.article_obj

        # create json without token ids
        revision_json_without_tokenid = v.get_revision_json(wp.revision_ids, {'rev_id', 'author_id'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))

        # compare jsons without token ids
        test_json_file_path = '{}/{}_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)
        assert is_content_same, "{}: 'json without token ids' doesn't match".format(article_name)

        # check if all token ids are unique
        revision_json = v.get_revision_json(wp.revision_ids, {'token_id'})
        for _, rev in revision_json['revisions'][0].items():
            token_ids = [t['token_id'] for t in rev['tokens']]
            assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(article_name)
            break

        # compare jsons with token ids
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        test_json_file_path = '{}/{}_ti.json'.format(test_json_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        is_content_same = filecmp.cmp(json_file_path, test_json_file_path)
        assert is_content_same, "{}: json doesn't match".format(article_name)

        # create json with in/outbounds
        revision_json_with_io = v.get_revision_json(wp.revision_ids, {'inbound', 'outbound'})
        json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
        with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))

        # compare jsons with in/outbounds
        test_json_file_path = '{}/{}_io.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_with_io, test_json_file_path)
        assert is_content_same, "{}: 'json with in/outbounds' doesn't match".format(article_name)

    def test_continue_logic(self, temp_folder, article_name, revision_id_start, revision_id_end):
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
        revision_json_without_tokenid = v.get_revision_json(wp.revision_ids, {'rev_id', 'author_id'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)
        assert is_content_same, "{}: 'json without token ids' doesn't match".format(article_name)

        # compare jsons with token ids
        revision_json = v.get_revision_json(wp.revision_ids, {'token_id'})
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_ti.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path, test_json_file_path)
        assert is_content_same, "{}: json doesn't match".format(article_name)

        # compare jsons with in/outbounds
        revision_json_with_io = v.get_revision_json(wp.revision_ids, {'inbound', 'outbound'})
        json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
        with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_io.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_with_io, test_json_file_path)
        assert is_content_same, "{}: 'json with in/outbounds' doesn't match".format(article_name)

    def test_finger_lakes(self, temp_folder):
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

        with WPHandler(article_name, tests, save_pickle=True) as wp:
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
