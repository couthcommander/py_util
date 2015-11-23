import sys
#lower this number if you want to test the output
maxinput=pow(10,10)

# expect input files to be ordered by patient, then date

# python LastEncounter.py fake_incidents.csv fake_encounters.csv more_output.csv

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%1000:
            print "\r" + str(self.count),
        if self.count > maxinput:
            sys.exit()

def lastenc(incdate, encdate):
    n = len(encdate)
    edate = []
    edatei = []
    gap = []
    for string in encdate:
        junk = string.split(',',4)
        tmp = int(junk[2])
        if tmp >= incdate:
            edate.append(junk[1])
            edatei.append(tmp)
            gap.append(int(junk[3].rstrip()))
    # check if last encounter dates is before incident date
    if len(edate) == 0:
        return ['.','.','.','.']
    ans = [None,None,None,None]
    for i in range(n):
        if ans[0] is None and gap[i] > 180:
            ans[0] = edate[i]
            ans[1] = edatei[i]
        if ans[2] is None and gap[i] > 360:
            ans[2] = edate[i]
            ans[3] = edatei[i]
        if ans[0] is not None and ans[2] is not None:
            break
    return ans

def splitData(string):
    junk=string.split(',',3)
    myid=int(junk[0])
    if junk[1] == "":
        print "error with string %s" % (string)
        return [-999,-999]
    mydate=int(junk[2])
    return [myid, junk[1], mydate]

if __name__=='__main__':
    if len(sys.argv) != 4:
        print "usage: " + sys.argv[0] + " incidentfile encounterfile outputfile"
        sys.exit(1)
    ifile=sys.argv[1]
    efile=sys.argv[2]
    ofile=sys.argv[3]
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    newcol = ',LastEncdate_180,LastEncdate_i180,LastEncdate_360,LastEncdate_i360\n'
    outfile.write(infile.readline().rstrip()+newcol)
    enfile.readline() # ignore first line
    nextid=''
    nextdate=''
    cnt = Counter()
    while True:
        lineincident=infile.readline()
        (inid, inmeh, indate)=splitData(lineincident)
        if inid != -999 or indate != -999:
            break
    while True:
        lineencounter=enfile.readline()
        (curid, curmeh, curdate)=splitData(lineencounter)
        if curid != -999 or curdate != -999:
            break
    data=[lineencounter]
    while(len(lineincident) > 1 and len(lineencounter) > 1):
        if(inid==curid):
            if(nextid==''):
                #read in until the id changes
                while(inid==curid):
                    while True:
                        lineencounter=enfile.readline()
                        if(len(lineencounter) > 1):
                            (curid, curmeh, curdate)=splitData(lineencounter)
                            if curid != -999 or curdate != -999:
                                data.append(lineencounter)
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
            ans = lastenc(indate, data)
            #output the results to the new file
            outfile.write(lineincident.rstrip()+',%s,%s,%s,%s\n' % (ans[0], ans[1], ans[2], ans[3]))
            cnt.add()
            #read in another line from infile
            while True:
                lineincident=infile.readline()
                if(len(lineincident) > 1):
                    (inid, inmeh, indate)=splitData(lineincident)
                    if inid != -999 or indate != -999:
                        break
                else:
                    break
        elif(inid < curid):
            #no match found, output the results
            outfile.write(lineincident.rstrip()+',.,.,.,.\n')
            cnt.add()
            #read another line from infile
            while True:
                lineincident=infile.readline()
                if(len(lineincident) > 1):
                    (inid, inmeh, indate)=splitData(lineincident)
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
                        (curid, curmeh, curdate)=splitData(lineencounter)
                        if curid != -999 or curdate != -999:
                            data.append(lineencounter)
                            break
                    else:
                        break
    #special case!
    #if the encounter file ran out of data before the incident file, must compare inid to curid
    #if they're the same and we have data, we should compare those dates as well
    #NOTE: this would never occur if a fake id was appended to the encounter file that was larger than the greatest id in the incident file
    while(len(lineincident) > 1):
        ans = ['.','.','.','.']
        if(inid==curid and len(data) > 0):
            ans = lastenc(indate, data)
        outfile.write(lineincident.rstrip()+',%s,%s,%s,%s\n' % (ans[0], ans[1], ans[2], ans[3]))
        while True:
            lineincident=infile.readline()
            if(len(lineincident) > 1):
                (inid, inmeh, indate)=splitData(lineincident)
                if inid != -999 or indate != -999:
                    break
            else:
                break
    infile.close()
    enfile.close()
    outfile.close()
