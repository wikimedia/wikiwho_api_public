"""
Created on 29.12.2016

@author: maribelacosta
"""
from dateutil import parser
import sys
import csv


# def computeConflict(article_id, revision_file, token_file, f1, f2):
def computeConflict(article_id, revision_file, token_file):
    # Main structures.
    art = {}  # Key: article id. Values: list of revisions and conflict scores.

    art.update({int(article_id): {"rev_order": [], "revs": {}, "cbSimple": 0, "cb": 0, "cbTime": 0}})

    print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: article_id,revision_id,editor,timestamp,oadds
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            if line[0] == article_id:
                line[0] = int(line[0])
                art[line[0]]["revs"].update({int(line[1]): {"editor": line[2], "timestamp": parser.parse(line[3]),
                                                            "oadds": [], "token-ins": [], "token-outs": []}})

    print("Load token meta-data.")
    with open(token_file) as csvfile:
        # article_id,revision_id,token_id,str,origin,inbound,outbound
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for aux in infile:
            if aux[0] != article_id:
                continue
            
            aux[0] = int(aux[0])  # article id
            aux[5] = eval(aux[5].replace("{", "[").replace("}", "]"))  # ins
            aux[6] = eval(aux[6].replace("{", "[").replace("}", "]"))  # outs
            # in/out length check
            if len(aux[5]) > len(aux[6]):
                print("Warning: Inbound longer than Outbound in article" + str(aux[0]))
            
            # Cleaning inbound
            ins = aux[5]
            inbound = []
            for rev in ins:
                if rev in art[aux[0]]["revs"]:
                    inbound.append(rev)
                else:
                    print("Warning: Inbound contains spam in article" + str(aux[0]))
            
            # Cleaning outbound.
            outs = aux[6]
            outbound = []
            for rev in outs:
                if rev in art[aux[0]]["revs"]:
                    outbound.append(rev)
                else:
                    print("Warning: Outbound contains spam in article" + str(aux[0]))
            
            if inbound and outbound:
                m = min(len(inbound), len(outbound))
                if len(outbound) > len(inbound):
                    for i in range(0, m):
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"] - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        if aux1 < 0 or aux2 < 0:
                            # Error with timestamps
                            # break
                            print("Error: Inconsistent Inbound and Outbound in article" + str(aux[0])) 
                else:
                    # print m, inbound, outbound
                    b = False
                    for i in range(0, m-1):
                        aux1 = (art[aux[0]]["revs"][inbound[i]]["timestamp"] - art[aux[0]]["revs"][outbound[i]]["timestamp"]).total_seconds()
                        aux2 = (art[aux[0]]["revs"][outbound[i+1]]["timestamp"] - art[aux[0]]["revs"][inbound[i]]["timestamp"]).total_seconds()
                        if aux1 < 0 or aux2 < 0:
                            # Error here
                            print("Error: Inconsistent Inbound and Outbound  in article" + str(aux[0]))
                            b = True
                            break
                        
                    if not b and len(inbound)>m-1 and len(outbound)>m-1:
                        # print("here>>>", str(len(inbound)), str(len(outbound)), str(inbound), str(outbound))
                        aux1 = (art[aux[0]]["revs"][inbound[m-1]]["timestamp"] - art[aux[0]]["revs"][outbound[m-1]]["timestamp"]).total_seconds()   
                        if aux1 < 0:
                            # Error here
                            print("Error: Inconsistent Inbound and Outbound in article" + str(aux[0])) 
    return art


def main():
    csv.field_size_limit(sys.maxsize)
    article_id = sys.argv[1]  # No requirements on article_file.
    revision_file = sys.argv[2]    # Requirement on article_file: revisions ordered by timestamp.
    token_file = sys.argv[3]    # No requirements on token_file.

    print("Debugging Inbound and Outbound ...")
    data = computeConflict(article_id, revision_file, token_file)
    print("Done!")


if __name__ == '__main__':
    main()
