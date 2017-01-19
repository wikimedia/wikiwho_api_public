'''
Created on 08.01.2017

@author: maribelacosta
'''

import glob
import sys

def reduceArticle(articlefiles, outfile):
    
    print("Reducing article SHA revert.")
    
    # article,source,target,reverted_add_actions,reverted_del_actions,total_actions,source_editor,target_editor
    distinct_sources = []
    
    
    out = open(outfile, 'w')
    out.write("distinct_sources" + "\n")
    # Read each partition.    
    for f in articlefiles:
        print("Parsing ", str(f))
          
        with open(f) as infile:
            infile.readline() # Skip head
            for line in infile:
                line = line.split(",", 2)
                
                distinct_sources.append(int(line[1]))
                        
                    
    x = len(set(distinct_sources))
       
    out.write(str(x) + "\n")
    
    out.flush()
    out.close()
    



if __name__ == '__main__':
    
    root = sys.argv[1]
    
    articlefiles = glob.glob(root + "revisions-20161226-part*.csv")
    outarticle = root + "reverts-sha-summary-all.csv"
    
    reduceArticle(articlefiles, outarticle)
    