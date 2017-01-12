'''
Created on 09.01.2017

@author: maribelacosta
'''

from collections import defaultdict
from dateutil import parser
import sys
import csv


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1
        # yield '{}-{}'.format(m+1, y)


def computePersistence(article_file, revision_file, token_file, bot_file, f1):
    base = 48 * 3600  # hours

    # Main structures.
    art = {}  
    botList = {}
    # periods = []
    #notsurvived_agg = defaultdict(int)
    #oadds = defaultdict(int)
    
    # Number of tokens added by type of users. 
    oadds_ip = defaultdict(int)
    oadds_reg = defaultdict(int)
    oadds_bot = defaultdict(int)
    
    # Number of tokens that did not survived (a given time frame) by type of user.
    notsurvived_ip = defaultdict(int)
    notsurvived_reg = defaultdict(int)
    notsurvived_bot = defaultdict(int)
        
    print("Load article id.") 
    with open(article_file) as infile:
        next(infile, None)  # skip the header
        for line in infile:
            art.update({int(line): {"revs": {}}})

    print("Load revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: article_id,revision_id,editor,timestamp,oadds
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            aux = line
            aux[0] = int(aux[0])  # article id
            art[aux[0]]["revs"].update({int(aux[1]): {"editor": aux[2], "timestamp": parser.parse(aux[3]),
                                                      "oadds": [], "token-ins": [], "token-outs": []}})

    print("Load bot list.")
    with open(bot_file) as infile:
        next(infile, None)
        for line in infile:
            aux = line.split(",", 1)
            botList.update({aux[0]: aux[1]})  # {bot_id: bot_name}
    
    print("Load token meta-data.")
    with open(token_file) as csvfile:
        # Example of line CSV: article_id, label_revision_id (origin), token_id, value, inbound, outbound
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            # Get line.
            aux = line
            aux[0] = int(aux[0])  # article_id
            aux[1] = int(aux[1])  # label_revision_id (origin)
            aux[4] = eval(aux[4].replace("{", "[").replace("}", "]"))  # inbound
            aux[5] = eval(aux[5].replace("{", "[").replace("}", "]"))  # outbound
            
            # Getting type of editor of the origin revision.
            isIP = False
            isBot = False
            #isReg = False
            editor = art[aux[0]]["revs"][aux[1]]["editor"]
            if editor[:2] == "0|":
                isIP = True
                print("Editor is IP", editor)
            elif editor in botList.keys():
                isBot = True
                print("Editor is bot", editor, botList[editor])
            else:
                print("Editor is regular user")
            #    isReg = True
                
            # Cleaning outbound.
            f6 = aux[5]
            outbound = []
            for rev in f6:
                if rev in art[aux[0]]["revs"]:
                    outbound.append(rev)
            
            t1 = art[aux[0]]["revs"][aux[1]]["timestamp"]  # Timestamp of origin
            
            period = (t1.year, t1.month) #str(t1.year) +"-"+ str(t1.month)
            # periods.append(period)
            
            if isIP:
                oadds_ip[period] += 1
            elif isBot:
                oadds_bot[period] += 1
            else:
                oadds_reg[period] += 1
             
            if len(outbound) > 0:
                firstout = outbound[0]
                t2 = art[aux[0]]["revs"][firstout]["timestamp"]  # Timestamp of first out
                secs = (t2 - t1).total_seconds()
                
                if (secs < base):
                    #print aux["f3"], aux["f2"], t1, firstout, t2
                    if isIP:
                        notsurvived_ip[period] += 1
                    elif isBot:
                        notsurvived_bot[period] += 1
                    else:
                        notsurvived_reg[period] += 1
                    
                #else:
                #    survived_agg[period] += 1 
                    
            #else:
            #    survived_agg[period] += 1
                
    print("Printing persistence.")
    out2 = open(f1, 'w')
    out2.write("year,month,user_type,not_survived_48h,oadds\n")
    # for t in set(periods):
    for t in month_year_iter(1, 2001, 12, 2016):
        (year, month) = t
        # Print data of IP
        out2.write(str(year) + "," + str(month) + ",ip," + str(notsurvived_ip[t]) + "," + str(oadds_ip[t]) + "\n")
        # Print data of bots
        out2.write(str(year) + "," + str(month) + ",bot," + str(notsurvived_bot[t]) + "," + str(oadds_bot[t]) + "\n")
        # Print data of regular users
        out2.write(str(year) + "," + str(month) + ",regular," + str(notsurvived_reg[t]) + "," + str(oadds_reg[t]) + "\n")
    out2.close()
    
if __name__ == '__main__':
    
    article_file = sys.argv[1]  # No requirements on article_file.
    revision_file = sys.argv[2]    # Requirement on article_file: revisions ordered by timestamp.
    token_file = sys.argv[3]    # No requirements on token_file. 
    bot_file = sys.argv[4]
    f1 = sys.argv[5] #"persisentecesample-part01-token-out1000.txt"
    
    #article_file = "toy-articles.txt"  # No requirements on article_file.
    #revision_file = "toy-revisions.json"    # Requirement on article_file: revisions ordered by timestamp.
    #token_file = "toy-tokens.json"    # No requirements on token_file. 
    #bot_file = ""
    #f1 = "persistence-toy.txt"
    
    print("Computing Authorship and Persistence ...")
    computePersistence(article_file, revision_file, token_file, bot_file, f1)
    
    print("Done!")    
