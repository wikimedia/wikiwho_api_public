'''
Created on 29.12.2016

@author: maribelacosta
'''

from dateutil import parser
import sys
import csv
def computeConflict(article_id, revision_file, token_file, f1, f2):
    
    # Main structures.
    art = {}  # Key: article id. Values: list of revisions and conflict scores.
    
    # Auxiliary structures.
    tokens = []
    
    art.update({int(article_id) : {"rev_order": [], "revs": {}, "cbSimple": 0, "cb": 0, "cbTime": 0}})


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
            
            if len(aux[5]) > len(aux[6]):
                print ("Warning: Inbound longer than Outbound in article" + str(aux[0]))
            
            # Cleaning inbound
            f5 = aux[5]
            inbound = []
            for rev in f5:
                if rev in art[aux[0]]["revs"]:
                    inbound.append(rev)
                else:
                    print ("Warning: Inbound contains spam in article" + str(aux[0]))
            
            # Cleaning outbound.
            f6 = aux[6]
            outbound = []
            for rev in f6:
                if rev in art[aux[0]]["revs"]:
                    outbound.append(rev)
                else:
                    print ("Warning: Outbound contains spam in article" + str(aux[0]))
            
            # Compute conflict: CB Simple.
            #x = max(len(inbound) + len(outbound) - 1, 0)
            
            cbsimple = 0
                
            #if x > 0:
            if len(inbound) > 0 and len(outbound) > 0:
                
                m = min(len(inbound), len(outbound))

                
                if len(outbound) > len(inbound):
                    
                    for i in range(0, m):
                        
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"] - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        
                        cbsimple = cbsimple + 2
                        
                        if aux1 < 0 or aux2 < 0:
                            # Error with timestamps
                            #break
                            print("Error: Inconsistent Inbound and Outbound in article" + str(aux[0])) 
                        
                else:
                    
                    #print m, inbound, outbound
                    
                    b = False
                    for i in range(0, m-1):
                        
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"]  - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        
                        if aux1 < 0 or aux2 < 0:
                            # Error here
                            print("Error: Inconsistent Inbound and Outbound  in article" + str(aux[0]))
                            b = True
                            break
                        
                    
                    if not(b) and len(inbound)>m-1 and len(outbound)>m-1:
                        #print("here>>>", str(len(inbound)), str(len(outbound)), str(inbound), str(outbound)) 
                        aux1 = (art[aux[0]]["revs"][inbound[m-1]]["timestamp"] - art[aux[0]]["revs"][outbound[m-1]]["timestamp"]).total_seconds()   
                        
                        if aux1 < 0:
                            
                            # Error here 
                            print("Error: Inconsistent Inbound and Outbound in article" + str(aux[0])) 
                            
                                
    
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
    
    print("Debugging Inbound and Outbound ...")
    data = computeConflict(article_id, revision_file, token_file, f1, f2)
    #reverts = 
    print("Done!")    
    #for a in reverts.keys():
    #    for r in reverts[a]:
    #        print(a, r)
    
    
    
