import datetime, sys
#lower this number if you want to test the output
maxinput=100000000000

# expect input files to be ordered by patient, then date
# version 11a
# [a,b] and [c,d] can overlap
# version 11
# argument for column name
# take four additional inputs to define [a, b] and [c, d]
# --regardless of sign, values are made negative
# throw out invalid dates

# python Dm365Maker11.py fake_incidents.csv fake_encounters.csv more_output.csv Encounter

def splitData(string):
    junk=string.split(',',3)
    myid=int(junk[0])
    if junk[1] == "":
        print "error with string %s" % (string)
        return [-999,-999]
    mydate=int(junk[2])
    return [myid, mydate]

if __name__=='__main__':
    if len(sys.argv) != 5 and len(sys.argv) != 9:
        print "usage: " + sys.argv[0] + " incidentfile encounterfile outputfile colname [a b c d]"
        sys.exit(1)
    ifile=sys.argv[1]
    efile=sys.argv[2]
    ofile=sys.argv[3]
    cname = sys.argv[4]
    if len(sys.argv) != 9:
        (a, b, c, d) = [-1, -365, -366, -730]
    else:
        (a, b, c, d) = map(lambda x: abs(int(x))*-1, sys.argv[5:9])
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    newcol = ',%s%sto%s,%s%sto%s\n' % (cname, a, b, cname, c, d)
    outfile.write(infile.readline().rstrip()+newcol)
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
        enc365=0
        enc730=0
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
            for encdate in data:
                if((encdate - indate) >= 0 or (enc365 and enc730)):
                    continue
                if(not enc365 and (encdate - indate) >= b and (encdate - indate) <= a):
                    enc365=1
                if(not enc730 and (encdate - indate) >= d and (encdate - indate) <= c):
                    enc730=1
            #output the results to the new file
            outfile.write(lineincident.rstrip()+','+str(enc365)+','+str(enc730)+'\n')
            count+=1
            if not count%1000:
                print count
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
            outfile.write(lineincident.rstrip()+','+str(enc365)+','+str(enc730)+'\n')
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
        enc365=0
        enc730=0
        if(inid==curid and len(data) > 0):
            for encdate in data:
                if((encdate - indate) >= 0 or (enc365 and enc730)):
                    continue
                if(not enc365 and (encdate - indate) >= b and (encdate - indate) <= a):
                    enc365=1
                elif(not enc730 and (encdate - indate) >= d and (encdate - indate) <= c):
                    enc730=1
        outfile.write(lineincident.rstrip()+','+str(enc365)+','+str(enc730)+'\n')
        while True:
            lineincident=infile.readline()
            if(len(lineincident) > 1):
                (inid, indate)=splitData(lineincident)
                if inid != -999 or indate != -999:
                    break
            else:
                break

