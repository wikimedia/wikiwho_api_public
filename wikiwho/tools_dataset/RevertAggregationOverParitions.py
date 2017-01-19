'''
Created on 08.01.2017

@author: maribelacosta
'''

import glob
import sys

def reduceArticle(articlefiles, outfile):
    
    print("Reducing article revert.")
    
    # article,source,target,reverted_add_actions,reverted_del_actions,total_actions,source_editor,target_editor
    
    out = open(outfile, 'w')
    out.write("selfrevert,reverted_actions,ratio\n")
    # Read each partition.    
    for f in articlefiles:
        print("Parsing ", str(f))
        with open(f) as infile:
            infile.readline() # Skip head
            for line in infile:
                line = line.rstrip()
                line = line.split(",")
                
                selfrevert = 0
                if (line[6] == line[7]):
                    selfrevert = 1
                
                reverted_actions = int(line[3]) + int(line[4])
                ratio = reverted_actions/float(line[5])
                
                newline = str(selfrevert) + "," + str(reverted_actions) + "," + str(ratio)
                out.write(newline + "\n")
        out.flush()
    
    out.close()
    



if __name__ == '__main__':
    
    root = sys.argv[1]
    
    articlefiles = glob.glob(root + "reverts-part*.csv")
    outarticle = root + "reverts-dataR-all.csv"
    
    reduceArticle(articlefiles, outarticle)
    
