import sys
#lower this number if you want to test the output
maxinput=100000000000

# expect input files to be ordered by patient, then date
# version 12
# any number of intervals that can overlap
# version 11
# argument for column name
# take four additional inputs to define [a, b] and [c, d]
# --regardless of sign, values are made negative
# throw out invalid dates

# python Dm365Maker12.py fake_incidents.csv fake_encounters.csv more_output.csv Encounter

def inBetween(x, left, right):
    for i in range(len(x)):
        if x[i] >= left and x[i] <= right:
            return '1'
        if x[i] > right:
            return '0'
    return '0'

def checkInterval(indate, data, a, b):
    dates = [i - indate for i in data]
    res = [inBetween(dates, b[i], a[i]) for i in range(len(a))]
    return res

def splitData(string):
    junk=string.split(',',3)
    myid=int(junk[0])
    if junk[1] == "":
        print "error with string %s" % (string)
        return [-999,-999]
    mydate=int(junk[2])
    return [myid, mydate]

if __name__=='__main__':
    nArgs = len(sys.argv)
    if nArgs != 5 and nArgs < 7:
        print "usage: " + sys.argv[0] + " incidentfile encounterfile outputfile colname [a b] [c d]"
        sys.exit(1)
    ifile=sys.argv[1]
    efile=sys.argv[2]
    ofile=sys.argv[3]
    cname = sys.argv[4]
    if nArgs < 6:
        a = [-1]
        b = [-365]
    else:
        y = [abs(int(sys.argv[i]))*-1 for i in range(5, nArgs)]
        if len(y) % 2 != 0:
            print "usage: " + sys.argv[0] + " incidentfile encounterfile outputfile colname [a b] [c d]"
            sys.exit(2)
        a = [y[i] for i in range(0, len(y), 2)]
        b = [y[i] for i in range(1, len(y), 2)]
    newcols = ['%s%sto%s' % (cname, a[i], b[i]) for i in range(len(a))]
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    outfile.write(infile.readline().rstrip()+','+','.join(newcols)+"\n")
    enfile.readline() # ignore first line
    nextid=''
    nextdate=''
    count=0
    #more=True
    #morein=True
    while True:
        lineincident=infile.readline()
        (inid, indate)=splitData(lineincident)
        if inid != -999 or indate != -999:
            break
    while True:
        lineencounter=enfile.readline()
        (curid, curdate)=splitData(lineencounter)
        if curid != -999 or curdate != -999:
            break
    data=[curdate]
    while(len(lineincident) > 1 and len(lineencounter) > 1):
        if(inid==curid):
            if(nextid==''):
                #read in until the id changes
                while(inid==curid):
                    while True:
                        lineencounter=enfile.readline()
                        if(len(lineencounter) > 1):
                            (curid, curdate)=splitData(lineencounter)
                            if curid != -999 or curdate != -999:
                                data.append(curdate)
                                break
                        else:
                            break
                    if(len(lineencounter) <= 1):
                        break
                #at this point, this last value in data has a different ID
                #save the new values
                #while restoring the old ones
                if(len(lineencounter) > 1):
                    nextdate=data.pop()
                nextid=curid
                curid=inid
            #do calculations
            ans = checkInterval(indate, data, a, b)
            #output the results to the new file
            outfile.write(lineincident.rstrip()+','+','.join(ans)+'\n')
            count+=1
            if not count%10000:
                print "\r" + str(count),
            #read in another line from infile
            while True:
                lineincident=infile.readline()
                if(len(lineincident) > 1):
                    (inid, indate)=splitData(lineincident)
                    if inid != -999 or indate != -999:
                        break
                else:
                    break
        elif(inid < curid):
            #no match found, output the results
            ans = ['0' for i in range(len(a))]
            outfile.write(lineincident.rstrip()+','+','.join(ans)+'\n')
            count+=1
            #read another line from infile
            while True:
                lineincident=infile.readline()
                if(len(lineincident) > 1):
                    (inid, indate)=splitData(lineincident)
                    if inid != -999 or indate != -999:
                        break
                else:
                    break
        elif(inid > curid):
            data=[] #reset data array
            if(nextid!=''):
                curid=nextid
                nextid=''
                data.append(nextdate)
            else:
                #read in another line from enfile
                while True:
                    lineencounter=enfile.readline()
                    if(len(lineencounter) > 1):
                        (curid, curdate)=splitData(lineencounter)
                        if curid != -999 or curdate != -999:
                            data.append(curdate)
                            break
                    else:
                        break
        #this is for debugging purposes
        if count > maxinput:
            sys.exit()
    #special case!
    #if the encounter file ran out of data before the incident file, must compare inid to curid
    #if they're the same and we have data, we should compare those dates as well
    #NOTE: this would never occur if a fake id was appended to the encounter file that was larger than the greatest id in the incident file
    while(len(lineincident) > 1):
        ans = ['0' for i in range(len(a))]
        if(inid==curid and len(data) > 0):
            ans = checkInterval(indate, data, a, b)
        outfile.write(lineincident.rstrip()+','+','.join(ans)+'\n')
        while True:
            lineincident=infile.readline()
            if(len(lineincident) > 1):
                (inid, indate)=splitData(lineincident)
                if inid != -999 or indate != -999:
                    break
            else:
                break
