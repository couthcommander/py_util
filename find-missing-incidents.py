import sys
#lower this number if you want to test the output
maxinput=pow(10,10)

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%1000:
            print "\r" + str(self.count),
        if self.count > maxinput:
            sys.exit()

def check(inc, enc):
    return not inc in enc

def splitData(string):
    junk=string.split(',',3)
    myid=int(junk[0])
    mydate=int(junk[2])
    return [myid, mydate]

if __name__=='__main__':
    ifile='T:/T2DM/Data/Clean/SpecificDates/Medications/pharm_rxTypeAntiDm.csv'
    efile='T:/T2DM/Data/Clean/SpecificDates/Encounterdates/masterencdatest2dm.csv'
    ofile='missing-inc.csv'
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    infile.readline()
    enfile.readline()
    cnt = Counter()
    lineincident=infile.readline()
    (inid, indate)=splitData(lineincident)
    lineencounter=enfile.readline()
    (curid, curdate)=splitData(lineencounter)
    nextid=''
    nextdate=''
    data=[curdate]
    while(len(lineincident) > 1 and len(lineencounter) > 1):
        if(inid==curid):
            if(nextid==''):
                #read in until the id changes
                while(inid==curid):
                    lineencounter=enfile.readline()
                    if(len(lineencounter) > 1):
                        (curid, curdate)=splitData(lineencounter)
                        data.append(curdate)
                    else:
                        break
                #at this point, this last value in data has a different ID
                #save the new values
                #while restoring the old ones
                if(len(lineencounter) > 1):
                    nextdate=data.pop()
                nextid=curid
                curid=inid
            #do calculations
            ans = check(indate, data)
            #output the results to the new file
            if ans:
                outfile.write(lineincident.rstrip()+'\n')
            cnt.add()
            #read in another line from infile
            lineincident=infile.readline()
            if(len(lineincident) > 1):
                (inid, indate)=splitData(lineincident)
            else:
                break
        elif(inid < curid):
            #no match found, output the results
            outfile.write(lineincident.rstrip()+'\n')
            cnt.add()
            #read another line from infile
            lineincident=infile.readline()
            if(len(lineincident) > 1):
                (inid, indate)=splitData(lineincident)
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
                lineencounter=enfile.readline()
                if(len(lineencounter) > 1):
                    (curid, curdate)=splitData(lineencounter)
                    data.append(curdate)
                else:
                    break
    #special case!
    #if the encounter file ran out of data before the incident file, must compare inid to curid
    #if they're the same and we have data, we should compare those dates as well
    #NOTE: this would never occur if a fake id was appended to the encounter file that was larger than the greatest id in the incident file
    while(len(lineincident) > 1):
        if(inid==curid and len(data) > 0):
            if ans:
                outfile.write(lineincident.rstrip()+'\n')
        lineincident=infile.readline()
        if(len(lineincident) > 1):
            (inid, indate)=splitData(lineincident)
    infile.close()
    enfile.close()
    outfile.close()
