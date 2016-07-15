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
