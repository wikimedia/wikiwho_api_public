'''
Created on 29.12.2016

@author: maribelacosta
'''

from collections import Counter,  defaultdict
from dateutil import parser
import math
import sys
import csv
def computeConflict(article_id, revision_file, token_file, f1, f2):
    
    # Log base to compute score. 
    base = 3600
    
    # Main structures.
    art = {}  # Key: article id. Values: list of revisions and conflict scores.
    cbSimple_str = defaultdict(int) # Key: token string. Values: conflict scores.
    cb_str = defaultdict(int) # Key: token string. Values: conflict scores.
    cbTime_str = defaultdict(int) # Key: token string. Values: conflict scores.
    #freq_str = {} # Key: token string. Values: # occurrences in all articles.
    
    # Auxiliary structures.
    tokens = []
    cbSimple_str_aux = []
    cb_str_aux = []
    cbTime_str_aux = []
    
    art.update({int(article_id) : {"rev_order": [], "revs": {}, "cbSimple": 0, "cb": 0, "cbTime": 0}})
    
    #print("Load article id.") 
    #with open(article_file) as infile:
    #    infile.readline() # pop the header
    #    for line in infile:
    #        art.update({int(line) : {"rev_order": [], "revs": {}, "cbSimple": 0, "cb": 0, "cbTime": 0}})

    #print(art) 
    print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: article_id,revision_id,editor,timestamp,oadds
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            aux = line
            #aux = line.split(",")
            #art[int(aux["article_id"])]["rev_order"].append(int(aux["revision_id"])) 
            if (aux[0] == article_id):
                aux[0] = int(aux[0])
                art[aux[0]]["revs"].update({int(aux[1]) : {"editor": aux[2], "timestamp": parser.parse(aux[3]),"oadds": [], "token-ins": [], "token-outs": []}}) 
    

    print("Load token meta-data.")
    #infile = open(token_file, 'r')
    #lines = infile.readlines()
    #if True:
    #counter = 0
    with open(token_file) as csvfile:
        # Example of line: {"f1":287849360,"f2":0,"f3":"for","f4":[],"f5":[288382394]}
        # f1 -> article_id
        # f2 -> revision_id (origin)
        # f3 -> token_id
        # f4 -> value
        # f5 -> inbound
        # f6 -> outbound
        # article_id,revision_id,token_id,str,origin,inbound,outbound 
        # article_id,revision_id,token_id,str,origin,inbound,outbound
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        #infile.readline() # pop the header
        for line in infile:
            aux = line
            
            if aux[0] != article_id:
                continue
            
            aux[0] = int(aux[0])
            aux[5] = eval(aux[5].replace("{", "[").replace("}", "]"))
            aux[6] = eval(aux[6].replace("{", "[").replace("}", "]"))
            #aux = eval(line)
            
            # Add token to the list of tokens.
            tokens.append(aux[3])
            
            # Cleaning inbound
            f5 = aux[5]
            inbound = []
            for rev in f5:
                if rev in art[aux[0]]["revs"]:
                    inbound.append(rev)
            
            # Cleaning outbound.
            f6 = aux[6]
            outbound = []
            for rev in f6:
                if rev in art[aux[0]]["revs"]:
                    outbound.append(rev)
            
            # Compute conflict: CB Simple.
            #x = max(len(inbound) + len(outbound) - 1, 0)
            
            cbsimple = 0
                
            #if x > 0:
            if len(inbound) > 0 and len(outbound) > 0:
                
                m = min(len(inbound), len(outbound))
                cb = 0
                cbTime = 0
                #cbsimple = 0
                
                if len(outbound) > len(inbound):
                    
                    for i in range(0, m):
                        
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"] - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        
                        cbsimple = cbsimple + 2
                        
                        if aux1 < 0 or aux2 < 0:
                            break 
                        
                        if (art[aux[0]]["revs"][inbound[i]]["editor"] != art[aux[0]]["revs"][outbound[i]]["editor"]):
                            cb = cb + 1
                            cbTime = cbTime + 1.0/(math.log(aux1 + 2.0, base))
                        
                        if (art[aux[0]]["revs"][outbound[i+1]]["editor"] != art[aux[0]]["revs"][inbound[i]]["editor"]):
                            cb = cb + 1
                            cbTime = cbTime + 1.0/(math.log(aux2 + 2.0, base))
                        
                else:
                    
                    #print m, inbound, outbound
                    
                    b = False
                    for i in range(0, m-1):
                        
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"]  - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        
                        if aux1 < 0 or aux2 < 0:
                            b = True
                            break
                        
                        cbsimple = cbsimple + 2
                        
                        if (art[aux[0]]["revs"][inbound[i]]["editor"] != art[aux[0]]["revs"][outbound[i]]["editor"]):
                            cb = cb + 1
                            cbTime = cbTime + 1.0/(math.log(aux1 + 2.0, base))
                            
                        
                        if (art[aux[0]]["revs"][outbound[i+1]]["editor"] != art[aux[0]]["revs"][inbound[i]]["editor"]):
                            cb = cb + 1
                            cbTime = cbTime + 1.0/(math.log(aux2 + 2.0, base))
                    
                    if not(b) and len(inbound)>m-1 and len(outbound)>m-1:
                        #print("here>>>", str(len(inbound)), str(len(outbound)), str(inbound), str(outbound)) 
                        aux1 = (art[aux[0]]["revs"][inbound[m-1]]["timestamp"] - art[aux[0]]["revs"][outbound[m-1]]["timestamp"]).total_seconds()   
                        
                        if aux1 >= 0: 
                            cbsimple = cbsimple + 1
                        
                            if (art[aux[0]]["revs"][inbound[m-1]]["editor"] != art[aux[0]]["revs"][outbound[m-1]]["editor"]):
                                cb = cb + 1
                                cbTime = cbTime + 1.0/(math.log(aux1 +2.0, base))
                        
                cb_str_aux.append((aux[3], cb))
                cbTime_str_aux.append((aux[3], cbTime))
                    
                # Update conflict of article: cb.
                art[aux[0]]["cb"] = art[aux[0]]["cb"] + cb 
                
                # Update conflict of article: cbTime.
                art[aux[0]]["cbTime"] = art[aux[0]]["cbTime"] + cbTime
                
            
                # Update conflict of article: cbSimple.
                art[aux[0]]["cbSimple"] = art[aux[0]]["cbSimple"] + cbsimple  
                
                # Update conflict of string overall all articles.
                cbSimple_str_aux.append((aux[3], cbsimple))
                    
                
    #infile.close()
    
    print("Printing article conflict.")    
    out1 = open(f1, 'w')
    out1.write("article_id,cbSimple,cb,cbTime,total_revs\n")
    for article in art.keys():
        out1.write(str(article) + "," + str(art[article]["cbSimple"]) + "," + str(art[article]["cb"]) + "," + str(art[article]["cbTime"]) + "," + str(len(art[article]['revs'])) + "\n") 
    #    for revision in d[article]["rev_order"]:
    #        print(d[article]["revs"][revision])
    out1.close()
                   
    print("Computing token frequency.")
    freq_str = Counter(tokens)
    
    print("Computing token conflict CB Simple.")
    for token, conflict in cbSimple_str_aux:
        cbSimple_str[token] += conflict
        
    print("Computing token conflict CB.")
    for token, conflict in cb_str_aux:
        cb_str[token] += conflict
        
    print("Computing token conflict CB Time.")
    for token, conflict in cbTime_str_aux:
        cbTime_str[token] += conflict
    
    print("Printing token conflict.")
    out2 = open(f2, 'w')
    out2.write("token,cbSimple,cb,cbTime,total_freq\n")
    for t in cbSimple_str.keys(): 
        out2.write(str(t) + "," + str(cbSimple_str[t]) + "," + str(cb_str[t]) + "," +  str(cbTime_str[t]) + "," + str(freq_str[t]) + "\n")
        #print cbSimple_str
        #print freq_str
    out2.close()
    
    return art
if __name__ == '__main__':
    
    csv.field_size_limit(sys.maxsize)   
    article_id = sys.argv[1]  # No requirements on article_file.
    revision_file = sys.argv[2]    # Requirement on article_file: revisions ordered by timestamp.
    token_file = sys.argv[3]    # No requirements on token_file. 
    
    #article_file = "toy-articles.txt"  # No requirements on article_file.
    #revision_file = "toy-revisions.json"    # Requirement on article_file: revisions ordered by timestamp.
    #token_file = "toy-tokens.json"    # No requirements on token_file. 
    f1 = sys.argv[4] #"conflictsample-part01-article-out1000.txt"
    f2 = sys.argv[5] #"conflictsample-part01-token-out1000.txt"
    
    print("Computing Conflict ...")
    data = computeConflict(article_id, revision_file, token_file, f1, f2)
    #reverts = 
    print("Done!")    
    #for a in reverts.keys():
    #    for r in reverts[a]:
    #        print(a, r)
    
    
    
