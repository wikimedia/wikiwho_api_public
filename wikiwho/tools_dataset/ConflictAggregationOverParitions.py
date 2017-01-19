'''
Created on 08.01.2017

@author: maribelacosta
'''

import glob
from collections import defaultdict



def reduceArticle(articlefiles, outfile):
    
    print("Reducing article conflict.")
    
    out = open(outfile, 'w')
    out.write("article_id,cbSimple,cb,cbTime,total_revs\n")
    # Read each partition.    
    for f in articlefiles:
        print("Parsing ", str(f))
        with open(f) as infile:
            infile.readline()
            for line in infile:
                line = line.rstrip()
                out.write(line + "\n")
        out.flush()
    
    out.close()
    

# Token file format
# token,cbSimple,cb,cbTime,total_freq
def reduceToken(tokenfiles, outfile):
    
    print("Reducing token conflict.")
    agg_cbsimple = defaultdict(int)
    agg_cb = defaultdict(int)
    agg_cbtime = defaultdict(float)
    agg_freq = defaultdict(int)
    x = []

    # Read each partition.    
    for f in tokenfiles:
        print("Parsing ", str(f))
        with open(f) as infile:
            infile.readline()
            for line in infile:
                line = line.rstrip()
                aux = line.rsplit(",",4)
                #print(aux)
                x.append((aux[0], int(aux[1]), int(aux[2]), float(aux[3]), int(aux[4])))
                
    # Aggregate the values of all partitions.
    print("Aggregating token conflict.")
    for (token, cbSimple, cb, cbTime, total_freq) in x:
        agg_cbsimple[token] = agg_cbsimple[token] + cbSimple
        agg_cb[token] = agg_cb[token] + cb
        agg_cbtime[token] = agg_cbtime[token] + cbTime
        agg_freq[token] = agg_freq[token] + total_freq
        
    
    # Print aggregate.
    print("Preparing token output.")
    out = open(outfile, 'w')
    out.write("token,cbSimple,cb,cbTime,total_freq\n")
    for token in agg_cbsimple.keys():
        out.write(token + ',' + str(agg_cbsimple[token]) + ',' +  str(agg_cb[token]) + ',' +  str(agg_cbtime[token]) + ',' +  str(agg_freq[token]) + '\n')
    out.flush()
    out.close()

if __name__ == '__main__':
    
    root = "/home/nuser/dumps/wikiwho_dataset/output_conflict/"
    
    articlefiles = glob.glob(root + "conflict-part*-article.csv")
    tokenfiles =  glob.glob(root + "conflict-part*-token.csv")
    
    outarticle = root + "conflict-all-article.csv"
    outtoken = root + "conflict-all-token.csv"
    
    reduceToken(tokenfiles, outtoken)
    reduceArticle(articlefiles, outarticle)
    
