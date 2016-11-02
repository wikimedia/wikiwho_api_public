# -*- coding: utf-8 -*-
"""
Additional configuration for py.test.
"""
import pytest


def pytest_addoption(parser):
    """
    To add lines option to py.test command parser.
    :param parser:
    :return:
    """
    parser.addoption("--lines", action="store", default="all",
                     help="line numbers from input file to test")


@pytest.fixture
def lines(request):
    """
    Value of lines option is returned.
    :param request:
    :return:
    """
    return request.config.getoption("--lines")


# @pytest.fixture(scope='session')
# def django_db_modify_db_settings():
#     """
#     By default, each xdist process gets its own database to run tests on. This is needed to have transactional
#     tests that does not interfere with eachother.
#     If you instead want your tests to use the same database, override the django_db_modify_db_settings to not do
#     anything
#     :return:
#     """
#     pass
