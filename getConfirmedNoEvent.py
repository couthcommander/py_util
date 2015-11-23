#!/usr/bin/python
import sys, getopt
#lower this number if you want to test the output
maxinput=pow(10,25)
# missing value character
missing_val=''
# text file delimeter (must be consistent across all input files)
delim_val=","

# python getConfirmed.py efile.csv cfile.csv ofile.csv

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%1000:
            print '\r%d' % self.count,
            sys.stdout.flush()
        if self.count > maxinput:
            sys.exit()

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

def usage():
    print "usage: " + sys.argv[0] + " [--minlag=92] [--maxlag=36500] [-h] efile cfile outputfile"

if __name__=='__main__':
    minlag=92
    maxlag=36500
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["minlag=", "maxlag=", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("--minlag"):
            minlag=int(arg)
            if minlag < 0:
                print "Minimum Lag must be greater than zero"
                usage()
                sys.exit()
        elif opt in ("--maxlag"):
            maxlag=int(arg)
            if maxlag < 0:
                print "Maximum Lag must be greater than zero"
                usage()
                sys.exit()
            if maxlag < minlag:
                (minlag, maxlag) = maxlag, minlag
                print "Max and Min lag were swapped"
    if len(args) != 3:
        usage()
        sys.exit(1)
    (efile, cfile, ofile)=args
    mainfile=open(efile)
    conffile=open(cfile)
    outfile=open(ofile,'w')
    header=mainfile.readline().rstrip()
    linemain=mainfile.readline().rstrip().split(delim_val, 3)
    junk=conffile.readline().rstrip()
    lineconf=conffile.readline().rstrip().split(delim_val, 3)
    outfile.write(header+delim_val+"confirmedOn"+delim_val+"confirmDist"+"\n")
    count=Counter()
    dates=[]
    (pid, date, dateoffset, stuff)=linemain
    (ptvid, confdate, confdateoffset, morestuff)=lineconf
    while(len(linemain) == 4 and len(lineconf) == 4):
        if(int(pid) < int(ptvid)):
            #can't confirm event, carry on
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
        outfile.write(delim_val.join(linemain + [missing_val]*2)+"\n")
        linemain=mainfile.readline().rstrip().split(delim_val, 3)
        count.add()
    mainfile.close()
    conffile.close()
    outfile.close()
