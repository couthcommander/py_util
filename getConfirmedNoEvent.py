#!/usr/bin/python
import sys
import argparse
# missing value character
missing_val=''

class Counter():
    def __init__(self):
        self.count = 0

    def add(self):
        self.count += 1
        if not self.count % 10000:
            print "\r" + str(self.count),

class Nothing():
    def __init__(self):
        pass

    def add(self):
        pass

#confirm events within lag time frame
def confirmEvent(init, dlist, minlag, maxlag):
    #assuming dlist is sorted
    if init > dlist[len(dlist)-1]:
        return [missing_val]*2
    firstdate = init + minlag
    lastdate = init + maxlag
    for i in range(0, len(dlist)):
        if firstdate <= dlist[i] <= lastdate:
            return [str(dlist[i]), str(dlist[i]-init)]
    return [missing_val]*2

##############################
# efile - list of events
# cfile - list of events, used for confirmation
# outputfile - confirmed events from efile
####### expects format [ptvid][date][dateoffset][eventType][etc]
####### also expects data to be sorted by ptvid and date
####### output of this script will be used with getFirstRx script
##############################

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    intervalperiod = 30
    parser.add_argument("efile", help='event file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("cfile", help='confirmation file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("--minlag", help="start of confirmation window", default=92, type=int)
    parser.add_argument("--maxlag", help="end of confirmation window", default=36500, type=int)
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--drop", help='drop records without confirmation', action='store_true')
    parser.add_argument("--nocount", help='turn counter off', action='store_true')
    args = parser.parse_args()
    efile = args.efile
    cfile = args.cfile
    ofile = args.outputfile
    minlag = args.minlag
    maxlag = args.maxlag
    delim_val = args.delimiter
    if minlag < 0:
        print "Minimum Lag must be greater than zero"
        sys.exit()
    if maxlag < 0:
        print "Maximum Lag must be greater than zero"
        sys.exit()
    if maxlag < minlag:
        (minlag, maxlag) = maxlag, minlag
        print "Max and Min lag were swapped"
    if args.drop:
        prm = False
    else:
        prm = True
    if args.nocount:
        count = Nothing()
    else:
        count = Counter()

    mainfile=open(efile)
    conffile=open(cfile)
    outfile=open(ofile,'w')
    header=mainfile.readline().rstrip()
    linemain=mainfile.readline().rstrip().split(delim_val, 3)
    junk=conffile.readline().rstrip()
    lineconf=conffile.readline().rstrip().split(delim_val, 3)
    outfile.write(header+delim_val+"confirmedOn"+delim_val+"confirmDist"+"\n")
    dates=[]
    (pid, date, dateoffset, stuff)=linemain
    (ptvid, confdate, confdateoffset, morestuff)=lineconf
    while(len(linemain) == 4 and len(lineconf) == 4):
        if(int(pid) < int(ptvid)):
            #can't confirm event, carry on
            if prm:
                outfile.write(delim_val.join(linemain + [missing_val]*2)+"\n")
            linemain=mainfile.readline().rstrip().split(delim_val, 3)
            if(len(linemain) == 4):
                (pid, date, dateoffset, stuff)=linemain
            count.add()
        elif(int(pid) > int(ptvid)):
            while(int(pid) > int(ptvid)):
                lineconf=conffile.readline().rstrip().split(delim_val, 3)
                if(len(lineconf) == 4):
                    (ptvid, confdate, confdateoffset, morestuff)=lineconf
                else:
                    break
        else:
            currentid=ptvid
            while(pid == ptvid):
                dates.append(int(confdateoffset))
                lineconf=conffile.readline().rstrip().split(delim_val, 3)
                if(len(lineconf) == 4):
                    (ptvid, confdate, confdateoffset, morestuff)=lineconf
                else:
                    break
            while(pid == currentid):
                #if event is confirmed, print to outfile
                confDate = confirmEvent(int(dateoffset), dates, minlag, maxlag)
                if prm or confDate[0] != missing_val:
                    outfile.write(delim_val.join(linemain + confDate)+"\n")
                linemain=mainfile.readline().rstrip().split(delim_val, 3)
                if(len(linemain) == 4):
                    (pid, date, dateoffset, stuff)=linemain
                else:
                    break
                count.add()
            dates=[]
    #there may be remaining lines in main file, but they can't be confirmed
    while(len(linemain) == 4):
        if prm:
            outfile.write(delim_val.join(linemain + [missing_val]*2)+"\n")
        linemain=mainfile.readline().rstrip().split(delim_val, 3)
        count.add()
    mainfile.close()
    conffile.close()
    outfile.close()
