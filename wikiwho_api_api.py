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

    params = {'titles':'Graz', 'action':'query', 'prop':'revisions', 'rvprop':'content|ids|timestamp|sha1|comment|flags|user|userid', 'rvlimit':'max', 'format':'json', 'continue':'', 'rvdir':'newer'}
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

        result = requests.get(url=url, headers=headers, params=params).json()

        if 'error' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following error:" + result['error'])
        if 'warnings' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following warning:" + result['warning'])
        if 'query' in result:
            wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
        if 'continue' not in result: break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue
        #print rvcontinue

# 	i += 1
#         if rev_timestamp > timestamp:
#             logging.debug("NEED TO DO SOMETHING")
#             #logging.debug(type(rev_timestamp))
#             #logging.debug(type(timestamp))
#             logging.debug("wikiwho timestamp first")
#             logging.debug(timestamp)
#             if timestamp.year == 1900:
#
# params = {'titles':'Gamergate_controversy', 'action':'query', 'prop':'revisions', 'rvprop':'content|ids', 'rvlimit':'max', 'format':'json'}
#
#
#
#                 url ='http://en.wikipedia.org/w/index.php'
#                 enc = {'title':'Special:Export', 'pages':art, 'action':'submit'}
#             else:
#                 logging.debug('doing partial download')
#                 url ='http://en.wikipedia.org/w/index.php'
#                 enc = {'title':'Special:Export','pages':art,'offset':timestamp,'action':'submit'}
#             # print timestamp
#             # #	enc = {'pages':art,'limit':'47','action':'submit'}
#             try:
#                 #data = urllib.urlencode(enc)
#                 #req = urllib2.Request(url=url,data=data)
#                 #response = urllib2.urlopen(req)
#                 r = requests.post(url, params=enc, stream=True)
#             except:
# 		#print str(e)
#                 Wikiwho.printFail(reviid, message="HTTP Response error! Try again later!")
#         # response = open("Finger_Lakes3_until4.xml")
#         # reviid = 27
#             #sys.exit()
# 	    #try:
#             #if timestamp <= wikiwho.lastrev_date:
#             #    Wikiwho.printFail(reviid, message="Something went awfully wrong with the timestamps!")
#             text = r.content
#
#             text_file = open("test.xml", "w+")
#             text_file.write(text)
#             text_file.close()
#
#             try:
#                 wikiwho.analyseArticle(StringIO(text))
#             except:
#                 logging.debug("ouch, Wikipedia returns bullshit!")
#                 logging.debug("pickling")
#                 f = io.open("pickle/" + art + ".p",'wb')
#                 cPickle.dump(wikiwho, f, protocol =-1)
#                 Wikiwho.printFail(reviid, message="Some problems with the returned XML by Wikipedia! Parsing error! Please try again!")
#             #wikiwho.analyseArticle(StringIO(response.read()))
#             #except:
# 	#	Wikiwho.printFail(reviid, message="Some problems with the returned XML by Wikipedia! Parsing error!")
#
#
#             timestamp = wikiwho.lastrev_date
#             logging.debug("wikiwho timestamp after")
#             logging.debug(timestamp)
#         else:
#             logging.debug("NO NEED TO DO ANYTHING")
#             break
#
#     logging.debug(wikiwho.lastrev)
#     logging.debug(wikiwho.lastrev_date)
#

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
        # f = io.open("pickle/" + art + ".msg",'wb')
        # msgpack.dump(wikiwho.spam, f)
        logging.debug("pickling")
        f = io.open("pickle_api/" + art + ".p",'wb')
        cPickle.dump(wikiwho, f, protocol =-1)
#
#     logging.debug("time at the end :")
#     time2 = time()
#     logging.debug(time2 - time1)
#     logging.debug("ENDING NOW")
#     #print(time2 - time1)
