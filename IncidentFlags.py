import sys
#lower this number if you want to test the output
maxinput=pow(10, 10)

# python IncidentFlags.py input.csv output.csv

def splitData(string):
    return string.rstrip().split(',')

if __name__=='__main__':
    nArgs = len(sys.argv)
    if nArgs != 3:
        print "usage: " + sys.argv[0] + " infile outputfile"
        sys.exit(1)
    ifile=sys.argv[1]
    ofile=sys.argv[2]
    infile=open(ifile)
    outfile=open(ofile,'w')

    header = splitData(infile.readline())
    header = header + ['Incident180Active180','Incident180Active360','Incident360Active360']
    # look up column number
    dmCols = ['DmRxFill-1to-180','DmRxFill-1to-360']
    aeCols = ['AnyEncounter-1to-180','AnyEncounter-1to-360','AnyEncounter-181to-360','AnyEncounter-361to-720']
    if sum([i in header for i in dmCols+aeCols]) != (len(dmCols)+len(aeCols)):
        print "some required columns are missing %s" % (dmCols+aeCols)
        sys.exit(2)
    dmLoc = [header.index(i) for i in dmCols]
    aeLoc = [header.index(i) for i in aeCols]
    outfile.write(','.join(header)+"\n")
    lineincident=infile.readline()
    count = 0
    while len(lineincident) > 1:
        dat = splitData(lineincident)
        dmVals = [int(dat[i]) for i in dmLoc]
        aeVals = [int(dat[i]) for i in aeLoc]
        i180a180 = not dmVals[0] and aeVals[0] and aeVals[2]
        i180a360 = not dmVals[0] and aeVals[1] and aeVals[3]
        i360a360 = not dmVals[1] and aeVals[1] and aeVals[3]
        ans = [str(int(i)) for i in [i180a180, i180a360, i360a360]]
        outfile.write(','.join(dat+ans)+'\n')
        lineincident=infile.readline()
        count+=1
        if not count%10000:
            print "\r" + str(count),
        #this is for debugging purposes
        if count > maxinput:
            sys.exit()
    infile.close()
    outfile.close()
