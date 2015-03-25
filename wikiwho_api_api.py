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

    try:
        art = fs.getvalue('name') #for running through browser
    except:
        Wikiwho.printFail(message="Name missing!")

    try:
        revisions = [int(x) for x in fs.getvalue('revid').split('|')] #for running through browser
    except:
        Wikiwho.printFail(message="Revision ids missing!")

    if len(revisions) > 2:
        Wikiwho.printFail(message="Too many revision ids provided!")

    try:
        format = fs.getvalue('format')
    except:
        format = "json"

    try:
        par = set(fs.getvalue('params').split('|'))
    except:
        par = set(['revid', 'author'])

    if par.issubset(set(['revid', 'author'])) == False:
        Wikiwho.printFail(message="Wrong parameter in list!")
    
    #art = 'graz'
    #reviid = 45618658
    #format = "json"

    logging.debug("--------")
    logging.debug(art)
    logging.debug(revisions)

    art = art.replace(" ", "_")


    if format != "json":
        Wikiwho.printFail(message="Currently, only json works as format!")

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
    while max(revisions) >= rvcontinue:
        logging.debug('doing partial download')
        logging.debug(rvcontinue)
        if rvcontinue != 0:
            params['rvcontinue'] = rvcontinue

        try:
            result = requests.get(url=url, headers=headers, params=params).json()
        except:
            Wikiwho.printFail(message="HTTP Response error! Try again later!")

        if 'error' in result: Wikiwho.printFail(message="Wikipedia API returned the following error:" + result['error'])
        #if 'warnings' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following warning:" + result['warnings'])
        if 'query' in result:
            if "-1" in result['query']['pages']:
                    Wikiwho.printFail(message="The article you are trying to request does not exist!")
            try:
                wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
            except:
                pickle(art, wikiwho)
                Wikiwho.printFail(message="Some problems with the returned XML by Wikipedia!")
        if 'continue' not in result: 
            #hackish
            wikiwho.rvcontinue = wikiwho.revision_curr.wikipedia_id + 1 
            break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue
        #print rvcontinue

    logging.debug('final rvcontinue ' + str(wikiwho.rvcontinue))


    #print len(wikiwho.revisions)

    for r in revisions:
        if r not in wikiwho.revisions:
            wikiwho.printFail(message="Revision ID does not exist for this article!")

    wikiwho.printRevision(revisions, par)

#
    logging.debug(wikiwho.rvcontinue)
    #logging.debug(wikiwho.lastrev_date)
#
    if wikiwho.rvcontinue != start:
        pickle(art, wikiwho)
