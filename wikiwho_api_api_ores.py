#!/usr/bin/python2.7

from __future__ import division

__author__ = 'psinger,ffloeck'

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

import Wikiwho_simple_ores 
import urllib, urllib2
import cPickle
import sys
import requests
import httplib

from cStringIO import StringIO

import json
from time import time

import dateutil.parser
from datetime import datetime, timedelta




def pickle(art, obj, path):
    logging.debug("pickling")
    f = io.open(path + art + ".p",'wb')
    cPickle.dump(obj, f, protocol =-1)
    
    
def getLatestRevId(article_name):
    
    # Set up request for Wikipedia API.
    server = "en.wikipedia.org"
    service = "w/api.php"
    headers = {"User-Agent": "WikiWhoClient/0.1", "Accept": "*/*", "Host": server}
    
    # Open connection to server.
    conn = httplib.HTTPSConnection(server)
    
    # Set parameters for API.
    params = urllib.urlencode({'action': "query", 'prop': 'revisions', 'titles': article_name, 'format': 'json'})
    
    # Execute GET request to the API.
    conn.request("GET", "/" + service + "?" + params, None, headers)
    
    # Get the response
    response = conn.getresponse()
    response = response.read()
    
    # Parse the response to JSON and get the last revid.
    response = json.loads(response)
    pageid = response["query"]["pages"].keys()[0]
    revid = response["query"]["pages"][pageid]["revisions"][0]["revid"]
    
    conn.close()
    return [revid] 

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
        revisions = getLatestRevId(art)
        #Wikiwho.printFail(message="Revision ids missing!")

    if len(revisions) > 2:
        Wikiwho.printFail(message="Too many revision ids provided!")

    if len(revisions) == 2:
        if revisions[1] <= revisions[0]:
            Wikiwho.printFail(message="Second revision id has to be larger than first revision id!")

    try:
        format = fs.getvalue('format')
    except:
        format = "json"

    try:
        par = set(fs.getvalue('params').split('|'))
    except:
        par = set()

    if par.issubset(set(['revid', 'author', 'tokenid'])) == False:
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
        #see if exists in primary disk, load, extend
        f = open("pickle_api/" + art + ".p",'rb')
        wikiwho = cPickle.load(f)
        path = "pickle_api/"
    except:
        try:
            # see if exists in secondary  disk, load, extend
            f = open("../disk2/pickle_api_2/" + art + ".p",'rb')
            wikiwho = cPickle.load(f)
            path = "../disk2/pickle_api_2/"
        except:
            #create new pickle in secondary disk
            wikiwho = Wikiwho(art)
            path = "../disk2/pickle_api_2/"


    assert (wikiwho.article == art)

    #lastrev = wikiwho.lastrev
    #print wikiwho.lastrev

    url ='https://en.wikipedia.org/w/api.php'

    headers = {
        'User-Agent': 'Wikiwho API',
        'From': 'philipp.singer@gesis.org and fabian.floeck@gesis.org'
    }


    session = requests.session()

    user    = 'Fabian%20Fl%C3%B6ck'
    passw   = 'rumkugeln'

    params  = '?action=login&lgname=%s&lgpassword=%s&format=json'% (user,passw)

    # Login request
    r1 = session.post(url+params)
    token = r1.json()['login']['token']
    params2 = params+'&lgtoken=%s'% token

    # Confirm token; should give "Success"
    r2 = session.post(url+params2)

    logging.debug("STARTING NOW")

    params = {'titles':art, 'action':'query', 'prop':'revisions', 'rvprop':'content|ids|timestamp|sha1|comment|flags|user|userid', 'rvlimit':'max', 'format':'json', 'continue':'', 'rvdir':'newer'}
    rvcontinue = wikiwho.rvcontinue
    start = rvcontinue
    #print rvcontinue
    #rvcontinue = '643899697'

    #THINK ABOUT NO RVCONTINUE

    i = 0
    while revisions[-1] >= int(rvcontinue.split('|')[-1]):
        logging.debug('doing partial download')
        logging.debug(rvcontinue)
        if rvcontinue != '0':
            params['rvcontinue'] = rvcontinue

        try:
            result = session.get(url=url, headers=headers, params=params).json()
        except:
            Wikiwho.printFail(message="HTTP Response error! Try again later!")

        if 'error' in result: Wikiwho.printFail(message="Wikipedia API returned the following error:" + str(result['error']))
        #if 'warnings' in result: Wikiwho.printFail(reviid, message="Wikipedia API returned the following warning:" + result['warnings'])
        if 'query' in result:
            if "-1" in result['query']['pages']:
                    Wikiwho.printFail(message="The article you are trying to request does not exist!")
            try:
            
            
                wikiwho.analyseArticle(result['query']['pages'].itervalues().next()['revisions'])
            except:
                pickle(art, wikiwho, path)
                Wikiwho.printFail(message="Some problems with the JSON returned by Wikipedia!")
        if 'continue' not in result: 
            #hackish
            timestamp = datetime.strptime(wikiwho.revision_curr.time, '%Y-%m-%dT%H:%M:%SZ') + timedelta(seconds=1)
            
            wikiwho.rvcontinue = timestamp.strftime('%Y%m%d%H%M%S') + "|" + str(wikiwho.revision_curr.wikipedia_id + 1)
            #print wikiwho.rvcontinue 
            break
        rvcontinue = result['continue']['rvcontinue']
        wikiwho.rvcontinue = rvcontinue
        #print rvcontinue

    logging.debug('final rvcontinue ' + str(wikiwho.rvcontinue))


    #print len(wikiwho.revisions)

    for r in revisions:
        if r not in wikiwho.revisions:
            wikiwho.printFail(message="Revision ID does not exist or is spam or deleted!")

    wikiwho.printRevision(revisions, par)

#
    logging.debug(wikiwho.rvcontinue)
    #logging.debug(wikiwho.lastrev_date)
#
    if wikiwho.rvcontinue != start:
        pickle(art, wikiwho, path)
