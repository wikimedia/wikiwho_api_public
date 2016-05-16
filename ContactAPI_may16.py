'''
Created on 13.05.2015

@author: maribelacosta
'''
import httplib, urllib
import signal
import sys
import csv
import json


def run(input_file, output_file):
    
    input_file = open(input_file, "r")
    output_file = open(output_file, "a")
    
    input_articles = csv.reader(input_file, delimiter=";")
    
    for line in input_articles:
        article_name = line[0] 
        page_id = line[1]
        
        try:
            with Timeout(120):
                res = contactWikiWhoAPI(article_name)
                output_file.write(article_name + "\t" + str(res) + "\n")
                output_file.flush()
                
        except Timeout.Timeout:
            print "WikiWho API timeout"
            output_file.write(article_name + "\t" + "TIMEOUT" +  "\n")
            output_file.flush()

        ''#print
        
        
        #contactWikiWhoAPI(rev_id, article_name)
    input_file.close()
    output_file.close()
    

def contactWikiWhoAPI(article_name):
    
    # Set up request for WikiWho API.
    server = "193.175.238.123:80"
    service = "wikiwho/wikiwho_api_api.py"
    headers = {"User-Agent": "WikiWhoClient/0.1", "Accept": "*/*", "Host": server}
    
    
    # Open connection to server.
    conn = httplib.HTTPConnection(server)
    
    # Set parameters for API.
    params = urllib.urlencode({'revid': '', 'name': article_name, 'format': 'json'})
    
    # Execute GET request to the API.
    conn.request("GET", "/" + service + "?" + params, None, headers)
    
    # Get the response
    response = conn.getresponse()
    response = response.read()#str(response.read())
    
    return "WikiWho API response", response[:300]
  
    
class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass
 
    def __init__(self, sec):
        self.sec = sec
 
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)
 
    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm
 
    def raise_timeout(self, *args):
        raise Timeout.Timeout()

if __name__ == '__main__':
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    run(input_file, output_file)
        
        
        