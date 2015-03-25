#!/usr/bin/python2.7

from __future__ import division

__author__ = 'psinger'

# enable debugging
import cgitb
cgitb.enable(format="html")
import io

import logging
logging.basicConfig(filename='log_api_api.log',level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

#import msgpack

import cgi

fs=cgi.FieldStorage()

print "Content-Type: application/json"
print

from Wikiwho_simple import Wikiwho
import urllib, urllib2
import cPickle
import sys
import requests

from cStringIO import StringIO

import json
from time import time

import dateutil.parser


# art = "Hermann_Beitzke"
# reviid = 620303077


def pickle(art, obj):
    logging.debug("pickling")
    f = io.open("pickle_api/" + art + ".p",'wb')
    cPickle.dump(obj, f, protocol =-1)

if __name__ == '__main__':

    time1 = time()

    # art = "Memex"
    # reviid = 601975046
    # format = "json"

    art = fs.getvalue('name') #for running through browser
    reviid=int(fs.getvalue('revid')) #for running through browser
    format = fs.getvalue('format')

    #art = 'graz'
    #reviid = 45618658
    #format = "json"

    logging.debug("--------")
    logging.debug(art)
    logging.debug(reviid)

    art = art.replace(" ", "_")


    if format != "json":
        Wikiwho.printFail(reviid, message="Currently, only json works as format!")

    #art = "test4"

    logging.debug("trying to load pickle")
    try:
        f = open("pickle_api/" + art + ".p",'rb')
        wikiwho = cPickle.load(f)
    except:
        wikiwho = Wikiwho(art)

    assert (wikiwho.article == art)

    #lastrev = wikiwho.lastrev
    #print wikiwho.lastrev

    url ='https://en.wikipedia.org/w/api.php'

    headers = {
        'User-Agent': 'Wikiwho API',
        'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'
    }


    logging.debug("STARTING NOW")

    params = {'titles':art, 'action':'query', 'prop':'revisions', 'rvprop':'content|ids|timestamp|sha1|comment|flags|user|userid', 'rvlimit':'max', 'format':'json', 'continue':'', 'rvdir':'newer'}
    rvcontinue = wikiwho.rvcontinue
    start = rvcontinue
    #print rvcontinue
    #rvcontinue = '643899697'

    #THINK ABOUT NO RVCONTINUE

    i = 0
    while reviid >= rvcontinue:
        logging.debug('doing partial download')
        logging.debug(rvcontinue)
        if rvcontinue != 0:
            params['rvcontinue'] = rvcontinue

        try:
            result = requests.get(url=url, headers=headers, params=params).json()
        except:
            Wikiwho.printFail(reviid, message="HTTP Response error! Try again later!")

        if 'error' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following error:" + result['error'])
        if 'warnings' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following warning:" + result['warning'])
        if 'query' in result:
            if "-1" in result['query']['pages']:
                    Wikiwho.printFail(reviid, message="The article you are trying to request does not exist!")
            try:
            	wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
            except:
		#print e
		#print result
		pickle(art, wikiwho)
                Wikiwho.printFail(reviid, message="Some problems with the returned XML by Wikipedia!")
        if 'continue' not in result: break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue
        #print rvcontinue



    #print len(wikiwho.revisions)

    if reviid in wikiwho.revisions:
        wikiwho.printRevision(reviid)
    else:
        wikiwho.printFail(reviid, message="Revision ID does not exist for this article!")
#
    logging.debug(wikiwho.rvcontinue)
    #logging.debug(wikiwho.lastrev_date)
#
    if rvcontinue != start:
        pickle(art, wikiwho)
	# f = io.open("pickle/" + art + ".msg",'wb')
        # msgpack.dump(wikiwho.spam, f)
        #logging.debug("pickling")
        #f = io.open("pickle_api/" + art + ".p",'wb')
        #cPickle.dump(wikiwho, f, protocol =-1)
#
#     logging.debug("time at the end :")
#     time2 = time()
#     logging.debug(time2 - time1)
#     logging.debug("ENDING NOW")
#     #print(time2 - time1)
