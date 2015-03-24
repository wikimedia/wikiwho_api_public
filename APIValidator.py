'''
Created on 22.10.2014

@author: maribelacosta
'''
import sys
from sys import argv,exit
import getopt
import WikiwhoAPIOutput
import random
import httplib, urllib
from difflib import Differ
from time import sleep
import ast  
import json

def main(my_argv):
    inputfile = ''
    n = None
    r = None

    if (len(my_argv) <= 3):
        try:
            opts, _ = getopt.getopt(my_argv,"i:",["ifile="])
        except getopt.GetoptError:
            print 'Usage: wikistats.py -i <inputfile> [-n <sample>] [-r <revision>]'
            exit(2)
    else:
        try:
            opts, _ = getopt.getopt(my_argv,"i:n:r:",["ifile=","sample=","revision="])
        except getopt.GetoptError:
            print 'Usage: wikistats.py -i <inputfile> [-n <sample>] [-r <revision>]'
            exit(2)
    
    for opt, arg in opts:
        if opt in ('-h', "--help"):
            print "wikistats"
            print
            print 'Usage: wikistats.py -i <inputfile> [-rev <revision_id>]'
            print "-i --ifile File to analyze"
            print "-n --sample Number of revisions to compare (by default 10)"
            print "-r --revision Specific revision id to diff"
            print "-h --help This help."
            exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-n", "--sample"):
            n = int(arg)
        elif opt in ("-r", "--revision"):
            r = int(arg)
         
    return (inputfile,n, r)

if __name__ == '__main__':
    
    #n = 10
    error = "A problem occurred in a Python script."
    
    (file_name, n, r) = main(argv[1:])
    
    if (n == None):
        n = 10
    
    pos1= file_name.rfind("/")
    pos2 = file_name.find(".xml")
    article_name = file_name[pos1+1:pos2]
    
    # Compute authorship information.
    revisions  = WikiwhoAPIOutput.analyseArticle(file_name)
    
    if (r != None):
        # Run specific revision. 
        rev_ids = [r]
    else:
        # Select randomly k revisions. 
        k = min(n, len(revisions.keys()))
        rev_ids = random.sample(revisions.keys(), k)
        rev_ids.sort()

    # Call the API for each revision in rev_ids.
    server = "wikiwho.aifb.kit.edu:80"
    service = "cgi-bin/wikiwho_api_api.py"
    headers = {"User-Agent": "APIValidator/0.1", "Accept": "*/*", "Host": server}
        
    api_res = {}
    for rev_id in rev_ids:
        #print rev_id
        # Open connection to server.
        conn = httplib.HTTPConnection(server)
        # Set parameters for API.
        params = urllib.urlencode({'revid': rev_id, 'name': article_name, 'format': 'json'})
        # Execute GET request to the API.
        conn.request("GET", "/" + service + "?" + params, None, headers)
        # Get the response
        response = conn.getresponse()
        response = response.read()#str(response.read())
	#print response
	#print rev_id
	try:
	    response = json.loads(response, encoding="UTF-8")
        except:
	    print response
	    sys.exit()	    

	#print "response", response
        
        if (error in response):
            res = [error]
        else:
            #response = response.replace('null', '"null"')
            #print response, type(response)
            #response = eval(response)#ast.literal_eval(response)
            response = response["tokens"]
            res = []
            for elem in response:
                new_elem = dict([(k.encode("utf-8"), v.encode("utf-8")) for k, v in elem.items()])
                #print elem["token"], type(elem["token"]), str(elem["token"])
                #elem["token"] = elem["token"].encode("utf-8")
                #elem["u'author_name"] = elem["token"].encode("utf-8")
                #print elem
                res.append(str(new_elem))
        #print res
        # Add response in structure to save all the responses from API.
        api_res.update({rev_id : res}) 
        # Close connection.
        conn.close()
        # Sleep x seconds before contacting the API.
        sleep(3) 
        
    #sys.exit()
    # Compare results of the API with the output of WikiWho.
    d = Differ()
    
    for rev_id in rev_ids:
        
        found_diff = False
        
        if (error in api_res[rev_id]):
            print "Revision ", rev_id, "presented error in API."
            found_diff = True
            continue
        
        original = WikiwhoAPIOutput.printRevisionJSON(revisions[rev_id])
        #print original
        diff = list(d.compare(original, api_res[rev_id]))
        for elem in diff:
            # if (word_diff[0] == ' '):
            if (elem[0] == '+') or (elem[0] == '-'):
                print rev_id, elem 
                found_diff = True
                
        if not(found_diff):
            print "No differences were found in revision", rev_id
    
    #print api_res
    
