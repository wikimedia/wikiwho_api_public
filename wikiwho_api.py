#!/usr/bin/python2.7

from __future__ import division

__author__ = 'psinger'

# enable debugging
import cgitb
cgitb.enable(format="html")
import io

import logging
logging.basicConfig(filename='log.log',level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

#import msgpack

import cgi

fs=cgi.FieldStorage()

print "Content-Type: application/json"
print

from Wikiwho import Wikiwho
import urllib, urllib2
import cPickle
import sys
import gzip
import requests

from cStringIO import StringIO

import json
import simplejson
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

    logging.debug("--------")
    logging.debug(art)
    logging.debug(reviid)

    art = art.replace(" ", "_")


    if format != "json":
        Wikiwho.printFail(reviid, message="Currently, only json works as format!")

    #art = "test4"


    try:
        f = open("pickle/" + art + ".p",'rb')
        wikiwho = cPickle.load(f)
    except:
        wikiwho = Wikiwho(art)


    assert (wikiwho.article == art)

    lastrev = wikiwho.lastrev
    #print wikiwho.lastrev

    try:
        response = urllib2.urlopen('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&revids='+str(reviid) + '&rvprop=timestamp&format=json')
        data = json.load(response)
        #url ='https://en.wikipedia.org/w/api.php'
	#params = {"action":"query", "prop":"revisions", "revids":str(reviid), "rvprop":"timestamp", "format":"json"}
	#resp = requests.get(url=url, params=params)

	#data = resp.json()
	if "badrevids" in data['query']:
            Wikiwho.printFail(reviid, message="The revision id requested does not exist!")
        #print data
        #sys.exit()
        for page in data['query']['pages'].values():
            #   print page
            rev_timestamp = page['revisions'][0]['timestamp']
            rev_title = page['title']
    except Exception, e:
        print e
        Wikiwho.printFail(reviid, message="HTTP Response error! Try again later!")

    #if rev_title != art:
    #	Wikiwho.printFail(reviid, message="Revision ID does not exist for this article!")

    logging.debug("STARTING NOW")

    rev_timestamp = dateutil.parser.parse(rev_timestamp[:-1])
    logging.debug("revision timestamp")
    logging.debug(rev_timestamp)
    timestamp = wikiwho.lastrev_date

    #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "application/xml"}

    i = 0
    while True:
	i += 1
        if rev_timestamp > timestamp:
            logging.debug("NEED TO DO SOMETHING")
            #logging.debug(type(rev_timestamp))
            #logging.debug(type(timestamp))
            logging.debug("wikiwho timestamp first")
            logging.debug(timestamp)
            if timestamp.year == 1900:
                logging.debug('doing full history download')
                url ='http://en.wikipedia.org/w/index.php'
                enc = {'title':'Special:Export', 'pages':art, 'action':'submit'}
            else:
                logging.debug('doing partial download')
                url ='http://en.wikipedia.org/w/index.php'
                enc = {'title':'Special:Export','pages':art,'offset':timestamp,'action':'submit'}
            # print timestamp
            # #	enc = {'pages':art,'limit':'47','action':'submit'}
            try:
                #data = urllib.urlencode(enc)
                #req = urllib2.Request(url=url,data=data)
                #response = urllib2.urlopen(req)
                r = requests.post(url, params=enc, stream=True)
            except: 
		#print str(e)
                Wikiwho.printFail(reviid, message="HTTP Response error! Try again later!")
        # response = open("Finger_Lakes3_until4.xml")
        # reviid = 27
            #sys.exit()
	    #try:
            #if timestamp <= wikiwho.lastrev_date:
            #    Wikiwho.printFail(reviid, message="Something went awfully wrong with the timestamps!")
            text = r.content
            
            text_file = open("test.xml", "w+")
            text_file.write(text)
            text_file.close()
            
            try:
                wikiwho.analyseArticle(StringIO(text))
            except:
                logging.debug("ouch, Wikipedia returns bullshit!")
                logging.debug("pickling")
                f = io.open("pickle/" + art + ".p",'wb')
                cPickle.dump(wikiwho, f, protocol =-1)
                Wikiwho.printFail(reviid, message="Some problems with the returned XML by Wikipedia! Parsing error! Please try again!")
            #wikiwho.analyseArticle(StringIO(response.read()))
            #except:
	#	Wikiwho.printFail(reviid, message="Some problems with the returned XML by Wikipedia! Parsing error!")


            timestamp = wikiwho.lastrev_date
            logging.debug("wikiwho timestamp after")
            logging.debug(timestamp)
        else:
            logging.debug("NO NEED TO DO ANYTHING")
            break

    logging.debug(wikiwho.lastrev)
    logging.debug(wikiwho.lastrev_date)

    if reviid in wikiwho.revisions:
        wikiwho.printRevision(reviid)
    else:
        wikiwho.printFail(reviid, message="Revision ID does not exist for this article!")

    #logging.debug(wikiwho.lastrev)
    #logging.debug(wikiwho.lastrev_date)

    if lastrev != wikiwho.lastrev:
        # f = io.open("pickle/" + art + ".msg",'wb')
        # msgpack.dump(wikiwho.spam, f)
        logging.debug("pickling")
        f = io.open("pickle/" + art + ".p",'wb')
        cPickle.dump(wikiwho, f, protocol =-1)

    logging.debug("time at the end :")
    time2 = time()
    logging.debug(time2 - time1)
    logging.debug("ENDING NOW")
    #print(time2 - time1)
