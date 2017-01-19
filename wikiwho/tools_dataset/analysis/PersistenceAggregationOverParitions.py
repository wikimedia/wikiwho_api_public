'''
Created on 08.01.2017

@author: maribelacosta
'''

import glob
from collections import defaultdict

def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1
        
# Token file format
# "year,month,user_type,not_persisted_48h,oadds
def reduceFile(tokenfiles, outfile):
    
    print("Reducing token conflict.")
    
    #periods = []
    
    notpersisted_ip = defaultdict(int)
    notpersisted_bot = defaultdict(int)
    notpersisted_reg = defaultdict(int)
    
    oadds_ip = defaultdict(int)
    oadds_bot = defaultdict(int)
    oadds_reg = defaultdict(int)

    # Read each partition.    
    for f in tokenfiles:
        print("Parsing ", str(f))
        with open(f) as infile:
            infile.readline()
            for line in infile:
                line = line.rstrip()
                aux = line.split(",")
                
                aux[0] = int(aux[0])
                aux[1] = int(aux[1])
                #aux[1] = int(aux[1])
                
                #periods.append[(aux[0], aux[1])]
                if (aux[2] == "ip"):
                    notpersisted_ip[(aux[0], aux[1])] += int(aux[3])
                    oadds_ip[(aux[0], aux[1])] += int(aux[4])
                elif (aux[2] == "bot"):
                    notpersisted_bot[(aux[0], aux[1])] += int(aux[3])
                    oadds_bot[(aux[0], aux[1])] += int(aux[4])
                else:
                    notpersisted_reg[(aux[0], aux[1])] += int(aux[3])
                    oadds_reg[(aux[0], aux[1])] += int(aux[4])
                
            
    # Print aggregate.
    print("Preparing  output.")
    out = open(outfile, 'w')
    out.write("year,month,user_type,not_survived_48h,oadds\n")
    for t in month_year_iter(1, 2001, 12, 2016):
        (year, month) = t
        
        # Print data of IP
        out.write(str(year) + ','  + str(month) + ',ip,' + str(notpersisted_ip[t]) + ',' +  str(oadds_ip[t])  + '\n')
        
        # Print data of bot
        out.write(str(year) + ','  + str(month) + ',bot,' + str(notpersisted_bot[t]) + ',' +  str(oadds_bot[t])  + '\n')
        
        # Print data of regular user 
        out.write(str(year) + ','  + str(month) + ',reg,' + str(notpersisted_reg[t]) + ',' +  str(oadds_reg[t])  + '\n')
    out.flush()
    out.close()

if __name__ == '__main__':
    
    root = "/home/nuser/dumps/wikiwho_dataset/output_authorship/"
    
    infiles = glob.glob(root + "authorship-part*.csv")
    
    outfile = root + "authorship-persistence-all.csv"
    
    reduceFile(infiles, outfile)
    