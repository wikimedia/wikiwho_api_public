'''
Created on 08.01.2017

@author: maribelacosta
'''

import glob
import sys

def reduceArticle(articlefiles, outfile):
    
    print("Reducing article revert.")
    
    # article,source,target,reverted_add_actions,reverted_del_actions,total_actions,source_editor,target_editor
    distinct_sources_non_self_full_revert = []
    distinct_sources_non_self_partial_revert = []
    distinct_sources_self_full_revert  = []
    distinct_sources_self_partial_revert = []
    
    distinct_targets_non_self_full_revert = []
    distinct_targets_non_self_partial_revert = []
    distinct_targets_self_full_revert = []
    distinct_targets_self_partial_revert = []

    
    out = open(outfile, 'w')
    out.write("sources-non-self-full-revert,sources-non-self-partial-revert,sources-self-full-revert,sources-self-partial-revert," +
              "targets-non-self-full-revert,targets-non-self-partial-revert,targets-self-full-revert,targets-self-partial-revert" + "\n")
    # Read each partition.    
    for f in articlefiles:
        print("Parsing ", str(f))
        sources_non_self_full_revert = []
        sources_non_self_partial_revert = []
        sources_self_full_revert  = []
        sources_self_partial_revert = []
    
        targets_non_self_full_revert = []
        targets_non_self_partial_revert = []
        targets_self_full_revert = []
        targets_self_partial_revert = []
        
        with open(f) as infile:
            infile.readline() # Skip head
            for line in infile:
                line = line.rstrip()
                line = line.split(",")
                
                # reverted_add_actions + reverted_del_actions by source
                reverted_actions = int(line[3]) + int(line[4])
                
                # total_actions by target
                total_actions = int(line[5]) 
                
                # Self revert
                if (line[6] == line[7]):
                    if reverted_actions == total_actions:
                        sources_self_full_revert.append(int(line[1]))
                        targets_self_full_revert.append(int(line[2]))
                    else:
                        sources_self_partial_revert.append(int(line[1]))
                        targets_self_partial_revert.append(int(line[2]))
                
                # Non-self revert
                else:
                    if reverted_actions == total_actions:
                        sources_non_self_full_revert.append(int(line[1]))
                        targets_non_self_full_revert.append(int(line[2]))
                    else:
                        sources_non_self_partial_revert.append(int(line[1]))
                        targets_non_self_partial_revert.append(int(line[2]))
                        
                    
        distinct_sources_non_self_full_revert.extend(list(set(sources_non_self_full_revert)))
        distinct_sources_non_self_partial_revert.extend(list(set(sources_non_self_partial_revert)))
        distinct_sources_self_full_revert.extend(list(set(sources_self_full_revert)))
        distinct_sources_self_partial_revert.extend(list(set(sources_self_partial_revert)))
    
        distinct_targets_non_self_full_revert.extend(list(set(targets_non_self_full_revert)))
        distinct_targets_non_self_partial_revert.extend(list(set(targets_non_self_partial_revert)))
        distinct_targets_self_full_revert.extend(list(set(targets_self_full_revert)))
        distinct_targets_self_partial_revert.extend(list(set(targets_self_partial_revert)))     
                
                
    a1 = len(set(distinct_sources_non_self_full_revert))
    b1 = len(set(distinct_sources_non_self_partial_revert))  
    c1 = len(set(distinct_sources_self_full_revert))  
    d1 = len(set(distinct_sources_self_partial_revert)) 
    
    a2 = len(set(distinct_targets_non_self_full_revert)) 
    b2 = len(set(distinct_targets_non_self_partial_revert)) 
    c2 = len(set(distinct_targets_self_full_revert))
    d2 = len(set(distinct_targets_self_partial_revert))
       
    out.write(str(a1) + 
              "," + str(b1) + 
              "," + str(c1) + 
              "," + str(d1) + 
              "," + str(a2) +
              "," + str(b2) + 
              "," + str(c2) + 
              "," + str(d2) +
              "\n")
    
    out.flush()
    out.close()
    



if __name__ == '__main__':
    
    root = sys.argv[1]
    
    articlefiles = glob.glob(root + "reverts-part*.csv")
    outarticle = root + "reverts-summary-all.csv"
    
    reduceArticle(articlefiles, outarticle)
    