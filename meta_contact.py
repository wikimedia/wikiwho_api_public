import sys
from os import listdir
from os.path import isfile, join
from ContactAPI_may16 import run

if __name__ == '__main__':
    
    mypath = sys.argv[1]
    range1 = int(sys.argv[2])
    range2 = int(sys.argv[3])
    l = listdir(mypath)
    print l
    for f in l:
        full_path = join(mypath, f)
        if isfile(full_path):
            pos1 = f.find("-")
            pos2 = f.find(".")
            if (pos1>-1 and pos2 >-1):
                i = int(f[pos1+1:pos2])
                #print "f", f, "i", i
                if (i >= range1 and i <= range2):
                    print "Run file", f
                    run(full_path, mypath + "/log/" + f +"_output")   
                