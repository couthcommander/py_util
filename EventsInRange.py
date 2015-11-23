import sys

# expect input files to be ordered by patient, then date

# python EventsInRange.py input.csv output.csv 1 180 181 360

def inBetween(x, left, right):
    for i in range(len(x)):
        if x[i] >= left and x[i] <= right:
            return 1
    return 0

def daysOn(dateint, daysupply, a, b, c, d):
    n = len(dateint)
    inInt = [[0,0] for i in range(n)]
    # calculate set of days
    days = set()
    for i in range(n):
        #days = days + range(dateint[i], daysupply[i]+dateint[i])
        # using every 90th day saves time
        days.add(dateint[i])
        if daysupply[i] > 0:
            for j in range(daysupply[i]/90):
                days.add((j+1)*90+dateint[i]-1)
            days.add(dateint[i]+daysupply[i]-1)
    days = sorted(days)
    # any days in between [a,b] or [c,d]
    for i in range(n):
        inInt[i][0] = inBetween(days, dateint[i]+b, dateint[i]+a)
        inInt[i][1] = inBetween(days, dateint[i]+d, dateint[i]+c)
    return inInt

def splitData(string):
    junk=string.split(',',5)
    myid=int(junk[0])
    if junk[1] == "":
        print "error with string %s" % (string)
        return [-999,-999,-999]
    mydate=int(junk[2])
    ds = junk[4].rstrip()
    if ds == '':
        ds = '90'
    ds = int(ds)
    return [myid, mydate, ds]

if __name__=='__main__':
    if len(sys.argv) != 4 and len(sys.argv) != 8:
        print "usage: " + sys.argv[0] + " inputfile outputfile colname [a b c d]"
        sys.exit(1)
    ifile=sys.argv[1]
    ofile=sys.argv[2]
    cname = sys.argv[3]
    if len(sys.argv) != 8:
        (a, b, c, d) = [-1, -365, -366, -730]
    else:
        (a, b, c, d) = map(lambda x: abs(int(x))*-1, sys.argv[4:8])
    infile=open(ifile)
    outfile=open(ofile,'w')
    newcol = ',%s%sto%s,%s%sto%s\n' % (cname, a, b, cname, c, d)
    outfile.write(infile.readline().rstrip()+newcol)
    count=0
    while True:
        lineincident=infile.readline()
        (curid, curdate, curds) = splitData(lineincident)
        if curid != -999 or curdate != -999:
            break
    inid = curid
    dates = [curdate]
    dsups = [curds]
    lines = [lineincident]
    while True:
        lineincident = infile.readline()
        if(len(lineincident) > 1):
            (curid, curdate, curds) = splitData(lineincident)
            if curid != -999 or curdate != -999:
                if curid == inid:
                    dates.append(curdate)
                    dsups.append(curds)
                    lines.append(lineincident)
                else:
                    res = daysOn(dates, dsups, a, b, c, d)
                    for i in range(len(res)):
                        outfile.write(lines[i].rstrip()+','+str(res[i][0])+','+str(res[i][1])+'\n')
                    inid = curid
                    dates = [curdate]
                    dsups = [curds]
                    lines = [lineincident]
        else:
            break
    # run for last set of data
    res = daysOn(dates, dsups, a, b, c, d)
    for i in range(len(res)):
        outfile.write(lines[i].rstrip()+','+str(res[i][0])+','+str(res[i][1])+'\n')
    infile.close()
    outfile.close()
