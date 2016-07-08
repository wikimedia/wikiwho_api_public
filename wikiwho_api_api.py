#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
from __future__ import division
import cgitb
import logging
import cgi
from utils import print_fail, get_latest_revision_id
from handler import handle

# import io
# from Wikiwho_simple import Wikiwho
# import urllib  # , urllib2
# import cPickle
# import sys
# import requests
# import httplib
# from cStringIO import StringIO
# import json
# from time import time
# import dateutil.parser
# from datetime import datetime, timedelta
# import json
# import sys


__author__ = 'psinger,ffloeck'

# enable debugging
cgitb.enable(format="html")
# logging
logging.basicConfig(filename='log_api_api.log', level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
# CGI
fs = cgi.FieldStorage()

print "Content-Type: application/json"
print


def main():
    article_name = ''
    try:
        article_name = fs.getvalue('name')  # for running through browser
    except:
        # FIXME fs.getvalue doesnt throw exception, so it doesnt enter here
        print_fail(message="Name missing!")
    if not article_name:
        print_fail(message="Name missing!")

    try:
        revision_ids = [int(x) for x in fs.getvalue('revid').split('|')]  # for running through browser
    except:
        revision_ids = get_latest_revision_id(article_name)
        if not revision_ids:
            print_fail(message="The article you are trying to request does not exist!")
    if len(revision_ids) > 2:
        print_fail(message="Too many revision ids provided!")
    if len(revision_ids) == 2 and revision_ids[1] <= revision_ids[0]:
        revision_ids.reverse()
        # print_fail(message="Second revision id has to be larger than first revision id!")

    try:
        format_ = fs.getvalue('format')
    except:
        format_ = "json"
    else:
        if not format_:
            format_ = "json"  # default
        elif format_ != "json":
            print_fail(message="Currently, only json works as format!")

    try:
        parameters = set(fs.getvalue('params').split('|'))
    except:
        parameters = set()
    if parameters.issubset({'revid', 'author', 'tokenid'}) is False:
        print_fail(message="Wrong parameter in list!")

    handle(article_name, revision_ids, format_, parameters)

if __name__ == '__main__':
    main()
