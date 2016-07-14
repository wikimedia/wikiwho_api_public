# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import range
from openpyxl import load_workbook
import os
import pytest

from handler import WPHandler
from structures.Text import splitIntoWords
# TODO tests for structures: splitIntoWords ...


def pytest_generate_tests(metafunc):
    # print(metafunc)
    if "article_name" in metafunc.fixturenames:
        wb = load_workbook(filename='test_wikiwho_simple.xlsx', data_only=True, read_only=True)
        ws = wb[wb.sheetnames[0]]
        c = 0
        for row in ws.iter_rows():
            if c == 0:
                c += 1
                continue
            funcargs = {
                'article_name': row[0].value,
                'revision_ids': [int(row[2].value)],
                'token': '{}'.format(row[3].value).lower(),
                'context': '{}'.format(row[4].value).lower(),
                'correct_rev_id': int(row[5].value),
            }
            metafunc.addcall(funcargs=funcargs)


class TestWikiwho:
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """

    @classmethod
    def teardown_class(cls):
        """ teardown any state that was previously setup with a call to
        setup_class.
        """

    @pytest.fixture(scope='session')
    def temp_folder(self, tmpdir_factory):
        tmp = 'tmp_test'
        if not os.path.exists(tmp):
            os.mkdir(tmp)
        return tmp
        # in os' tmp dir
        # return tmpdir_factory.getbasetemp()

    def test_authorship(self, temp_folder, article_name, revision_ids, token, context, correct_rev_id):
        sub_text = splitIntoWords(context)
        with WPHandler(article_name, temp_folder) as wp:
            wp.handle(revision_ids, 'json')
        text, authors = wp.wikiwho.get_revision_text(revision_ids[0])
        n = len(sub_text)
        found = 0
        print(token, context)
        print(sub_text)
        for i in range(len(text) - n + 1):
            if sub_text == text[i:i + n]:
                token_i = i + sub_text.index(token)
                ww_rev_id = authors[token_i]
                found = 1
                assert ww_rev_id == correct_rev_id, "{}: {}: rev id was {}, should be {}".format(article_name,
                                                                                                 token,
                                                                                                 ww_rev_id,
                                                                                                 correct_rev_id)
                break
        assert found, "{}: {} -> token not found".format(article_name, token)
