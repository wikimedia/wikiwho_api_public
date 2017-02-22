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

import os
import sys
import pytest
import json
import filecmp
import io
from builtins import range

from openpyxl import load_workbook
from mwxml import Dump
from mwtypes.files import reader

from api.handler import WPHandler
from wikiwho.tests.utils import article_zips
from wikiwho.utils import split_into_tokens
from api.views import WikiwhoApiView, WikiwhoView
from django.utils.dateparse import parse_datetime

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
                # test_authorship
                funcargs = {
                    'article_name': article_name,
                    'revision_id': int(row[2].value),
                    'token': '{}'.format(row[3].value).lower(),
                    'context': '{}'.format(row[4].value).lower(),
                    'correct_rev_id': int(row[5].value),
                }
                metafunc.addcall(funcargs=funcargs)
            elif article_name not in articles and 'revision_id_start' in metafunc.fixturenames:
                # test_continue_logic
                articles.add(article_name)
                funcargs = {
                    'article_name': article_name,
                    'revision_id_start': int(row[5].value),
                    'revision_id_end': int(row[2].value),
                }
                metafunc.addcall(funcargs=funcargs)
            elif article_name not in articles:
                # test_json_output(_xml)
                articles.add(article_name)
                funcargs = {
                    'article_name': article_name,
                    'revision_id': int(row[2].value),
                }
                metafunc.addcall(funcargs=funcargs)


def _test_json(wp, temp_folder, article_name, test_io=True, from_db=False):
    test_json_folder = 'test_jsons/after_newer_splitting'

    v = WikiwhoView()
    # create json with rev and editor ids
    revision_json_without_tokenid = v.get_revision_json(wp, {'str', 'rev_id', 'editor'}, from_db=from_db, with_token_ids=False)
    json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
    with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
        f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                           sort_keys=True, ensure_ascii=False))
    # compare jsons with rev and editor ids
    test_json_file_path = '{}/{}_db_ri_ai.json'.format(test_json_folder, article_name)
    is_content_same_1 = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)

    # create json with token ids
    revision_json = v.get_revision_json(wp, {'str', 'token_id'}, from_db=from_db, with_token_ids=True)
    # check if all token ids are unique
    for _, rev in revision_json['revisions'][0].items():
        token_ids = [t['token_id'] for t in rev['tokens']]
        assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(
            article_name)
        break
    # compare jsons with token ids
    json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
    test_json_file_path = '{}/{}_db_ti.json'.format(test_json_folder, article_name)
    with io.open(json_file_path, 'w', encoding='utf-8') as f:
        f.write(
            json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
    is_content_same_2 = filecmp.cmp(json_file_path, test_json_file_path)

    # create json with in/outbounds
    in_out_test_len = True
    in_out_test_spam = True
    in_out_test_ts = True
    # last_used_test_spam = True
    revision_json_with_io = v.get_revision_json(wp, {'str', 'inbound', 'outbound'}, from_db=from_db, with_token_ids=False)
    for i, ri in enumerate(wp.revision_ids):
        for t in revision_json_with_io['revisions'][i][ri]['tokens']:
            in_out_test_len = 0 <= len(t['outbound']) - len(t['inbound']) <= 1
            for r in t['outbound']:
                if r in wp.wikiwho.spam_ids:
                    in_out_test_spam = False
            for r in t['inbound']:
                if r in wp.wikiwho.spam_ids:
                    in_out_test_spam = False
            for o, i in zip(t['outbound'], t['inbound']):
                ts_diff = (parse_datetime(wp.wikiwho.revisions[i].timestamp) -
                           parse_datetime(wp.wikiwho.revisions[o].timestamp)).total_seconds()
                if ts_diff < 0:
                    in_out_test_ts = True
            if len(t['outbound']) > len(t['inbound']) and t['inbound']:
                ts_diff = (parse_datetime(wp.wikiwho.revisions[t['outbound'][-1]].timestamp) -
                           parse_datetime(wp.wikiwho.revisions[t['inbound'][-1]].timestamp)).total_seconds()
                if ts_diff < 0:
                    in_out_test_ts = True
            # last_used_test_spam = not (t['last_used'] in wp.wikiwho.spam_ids)
            if not in_out_test_len or not in_out_test_spam or not in_out_test_ts:
                # print(t['str'], len(t['outbound']), len(t['inbound']), t['outbound'], t['inbound'])
                break
    json_file_path_with_io = '{}/{}_db_io.json'.format(temp_folder, article_name)
    with io.open(json_file_path_with_io, 'w', encoding='utf-8') as f:
        f.write(json.dumps(revision_json_with_io, indent=4, separators=(',', ': '),
                           sort_keys=True, ensure_ascii=False))
    # compare jsons with in/outbounds
    test_json_file_path = '{}/{}_db_io.json'.format(test_json_folder, article_name)
    is_content_same_3 = filecmp.cmp(json_file_path_with_io, test_json_file_path)

    # test spams: api and xml dumps don't contain same revisions, so it is not possible to compare them
    # file_path_spams = '{}/{}_spams.txt'.format(temp_folder, article_name)
    # with io.open(file_path_spams, 'w', encoding='utf-8') as f:
    #     for spam_id in wp.wikiwho.spam_ids:
    #         f.write('{}\n'.format(spam_id))
    # test_file_path_spams = '{}/{}_spams.txt'.format(test_json_folder, article_name)
    # is_content_same_4 = filecmp.cmp(file_path_spams, test_file_path_spams)

    # TODO rev_ids.txt + deleted_content.json with threshold=0

    # print(wp.wikiwho.spam_ids)
    assert is_content_same_1, "{}: 'json with ri and ai doesn't match".format(article_name)
    assert is_content_same_2, "{}: json with ti doesn't match".format(article_name)
    assert in_out_test_len and in_out_test_spam and in_out_test_ts, "len: {}, spam: {}, ts: {}".format(
        in_out_test_len,  in_out_test_spam, in_out_test_ts)
    assert not test_io or is_content_same_3, "{}: 'json with in/outbounds doesn't match".format(article_name)
    # assert is_content_same_4, "{}: spam ids don't match".format(article_name)
    # assert last_used_test_spam, 'last used in spam'


class TestWikiwho:

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
        tmp_test_authorship = '{}/test_authorship'.format(tmp)
        if not os.path.exists(tmp_test_authorship):
            os.mkdir(tmp_test_authorship)
        tmp_test_json_output = '{}/test_json_output'.format(tmp)
        if not os.path.exists(tmp_test_json_output):
            os.mkdir(tmp_test_json_output)
        test_json_output_xml = '{}/test_json_output_xml'.format(tmp)
        if not os.path.exists(test_json_output_xml):
            os.mkdir(test_json_output_xml)
        tmp_test_continue_logic = '{}/test_continue_logic'.format(tmp)
        if not os.path.exists(tmp_test_continue_logic):
            os.mkdir(tmp_test_continue_logic)
        return tmp
        # in os' tmp dir
        # return tmpdir_factory.getbasetemp()

    def test_json_output(self, temp_folder, article_name, revision_id):
        """
        Tests json outputs of articles in given revisions in gold standard. If there are expected differences in
        jsons, authorship of each token in gold standard should be checked manually.
        :param revision_id: Revision id where authorship of token in gold standard is tested.
        """
        pickle_folder = temp_folder
        temp_folder = '{}/test_json_output'.format(temp_folder)
        with WPHandler(article_name, pickle_folder=pickle_folder) as wp:
            wp.handle([revision_id], is_api_call=False)
        _test_json(wp, temp_folder, article_name)

    @pytest.mark.django_db
    def test_json_output_db(self, temp_folder, article_name, revision_id):
        """
        Tests json outputs of articles in given revisions in gold standard. If there are expected differences in
        jsons, authorship of each token in gold standard should be checked manually.
        :param revision_id: Revision id where authorship of token in gold standard is tested.
        """
        # TODO test
        pickle_folder = temp_folder
        temp_folder = '{}/test_json_output'.format(temp_folder)
        with WPHandler(article_name, pickle_folder=pickle_folder, save_tables=('article', 'revision', 'token', )) as wp:
            wp.handle([revision_id], is_api_call=False)
        _test_json(wp, temp_folder, article_name, from_db=True)

    def test_json_output_xml(self, temp_folder, article_name, revision_id):
        """
        Tests json outputs of articles in given revisions in gold standard from xml dump.
        If there are expected differences in jsons, authorship of each token in gold standard should be
        checked manually.
        The xml file dumps taken from here: https://dumps.wikimedia.org/enwiki/20161101/
        :param revision_id: Revision id where authorship of token in gold standard is tested.
        """
        pickle_folder = temp_folder
        temp_folder = '{}/test_json_output_xml'.format(temp_folder)
        # read from xml dumps (7z)
        xml_file_path = 'test_jsons/{}'.format(article_zips[article_name])
        if not os.path.exists(xml_file_path):
            # server
            xml_file_path = '/home/nuser/pdisk/xmls_7z/batch_all/{}'.format(article_zips[article_name])
        dump = Dump.from_file(reader(xml_file_path))
        article_name = article_name.replace(' ', '_')
        title_matched = False
        for page in dump:
            if page.title.replace(' ', '_') == article_name:
                title_matched = True
                with WPHandler(article_name, page.id, pickle_folder=pickle_folder, is_xml=True) as wp:
                    wp.handle_from_xml(page)
                    wp.revision_ids = [revision_id]
                break

        assert title_matched, '{}--{}'.format(article_name, page.title)

        _test_json(wp, temp_folder, article_name, test_io=False)

    def test_json_output_xml_db(self, temp_folder, article_name, revision_id):
        """
        Tests json outputs of articles in given revisions in gold standard from xml dump.
        If there are expected differences in jsons, authorship of each token in gold standard should be
        checked manually.
        The xml file dumps taken from here: https://dumps.wikimedia.org/enwiki/20161101/
        :param revision_id: Revision id where authorship of token in gold standard is tested.
        """
        # TODO test
        pickle_folder = temp_folder
        temp_folder = '{}/test_json_output_xml'.format(temp_folder)
        # read from xml dumps (7z)
        xml_file_path = 'test_jsons/{}'.format(article_zips[article_name])
        if not os.path.exists(xml_file_path):
            # server
            xml_file_path = '/home/nuser/pdisk/xmls_7z/batch_all/{}'.format(article_zips[article_name])
        dump = Dump.from_file(reader(xml_file_path))
        article_name = article_name.replace(' ', '_')
        title_matched = False
        for page in dump:
            if page.title.replace(' ', '_') == article_name:
                title_matched = True
                with WPHandler(article_name, page.id, pickle_folder=pickle_folder,
                               is_xml=True, save_tables=('article', 'revision', 'token', )) as wp:
                    wp.handle_from_xml(page)
                    wp.revision_ids = [revision_id]
                break

        assert title_matched, '{}--{}'.format(article_name, page.title)

        _test_json(wp, temp_folder, article_name, test_io=False, from_db=True)

    def test_continue_logic(self, temp_folder, article_name, revision_id_start, revision_id_end):
        """
        :param revision_id_start: Correct revision id of first token of article in gold standard.
        :param revision_id_end: Revision id where authorship of token in gold standard is tested.
        """
        temp_folder = '{}/test_continue_logic'.format(temp_folder)
        test_json_folder = 'test_jsons'

        # first create article and revisions until revision_id_start
        with WPHandler(article_name) as wp:
            wp.handle([revision_id_start], is_api_call=False)

        assert wp.article_obj is not None

        # continue creating revisions of this article until revision_id_end
        with WPHandler(article_name) as wp:
            wp.handle([revision_id_end], is_api_call=False)

        v = WikiwhoApiView()
        v.article = wp.article_obj

        # compare jsons without token ids
        revision_json_without_tokenid = v.get_revision_json(wp.revision_ids, {'str', 'rev_id', 'editor'})
        json_file_path_without_tokenid = '{}/{}_db_ri_ai.json'.format(temp_folder, article_name)
        with io.open(json_file_path_without_tokenid, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json_without_tokenid, indent=4, separators=(',', ': '),
                               sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_db_ri_ai.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path_without_tokenid, test_json_file_path)
        assert is_content_same, "{}: 'json without token ids' doesn't match".format(article_name)

        # compare jsons with token ids
        revision_json = v.get_revision_json(wp.revision_ids, {'str', 'token_id'})
        # TODO check if all token ids are unique
        # for _, rev in revision_json['revisions'][0].items():
        #     token_ids = [t['token_id'] for t in rev['tokens']]
        #     assert len(token_ids) == len(set(token_ids)), "{}: there are duplicated token ids".format(article_name)
        #     break
        json_file_path = '{}/{}_db_ti.json'.format(temp_folder, article_name)
        with io.open(json_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(revision_json, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False))
        test_json_file_path = '{}/{}_db_ti.json'.format(test_json_folder, article_name)
        is_content_same = filecmp.cmp(json_file_path, test_json_file_path)
        assert is_content_same, "{}: json doesn't match".format(article_name)

        # compare jsons with in/outbounds
        revision_json_with_io = v.get_revision_json(wp.revision_ids, {'str', 'inbound', 'outbound'})
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

        with WPHandler(article_name, pickle_folder=tests, save_into_pickle=True, save_into_db=False) as wp:
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

    def test_authorship(self, temp_folder, article_name, revision_id, token, context, correct_rev_id):
        sub_token_list = split_into_tokens(context)
        n = len(sub_token_list)

        pickle_folder = temp_folder
        with WPHandler(article_name, pickle_folder=pickle_folder) as wp:
            wp.handle([revision_id], is_api_call=False)

        token_list, origin_rev_ids = wp.wikiwho.get_revision_text(revision_id)
        found = 0
        # print(wp.wikiwho.spam)
        print(token, context)
        print(sub_token_list)
        for i in range(len(token_list) - n + 1):
            if sub_token_list == token_list[i:i + n]:
                token_i = i + sub_token_list.index(token)
                ww_rev_id = origin_rev_ids[token_i]
                found = 1
                assert ww_rev_id == correct_rev_id, "1){}: {}: rev id was {}, should be {}".format(article_name,
                                                                                                   token,
                                                                                                   ww_rev_id,
                                                                                                   correct_rev_id)
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
