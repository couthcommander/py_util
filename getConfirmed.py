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
            print self.count
        if self.count > maxinput:
            sys.exit()

#confirm events within lag time frame
#list of event types: GFR, ESRD, Death, Transplant
#GFR is confirmed with GFR/ESRD/Transplant
#ESRD is confirmed with ESRD/Transplant
def confirmEvent(etype, init, elist, dlist, minlag, maxlag):
    #assuming dlist is sorted
    if(init > dlist[len(dlist)-1]) or (etype != 'GFR' and etype !='ESRD'):
        return False
    firstdate = init + minlag
    lastdate = init + maxlag
    for i in range(0, len(dlist)):
        if (firstdate <= dlist[i] <= lastdate) and (elist[i] == 'ESRD' or elist[i] == 'Transplant' or (etype == elist[i] == 'GFR')):
            return dlist[i]
    return False

##############################
# efile - list of events
# cfile - list of events, used for confirmation
# outputfile - confirmed events from efile
####### expects format [ptvid][date][dateoffset][eventType][etc]
####### also expects data to be sorted by ptvid and date
####### output of this script will be used with getFirstRx script
##############################

def usage():
    print "usage: " + sys.argv[0] + " [--minlag=92] [--maxlag=365] [-h] efile cfile outputfile"

if __name__=='__main__':
    minlag=92
    maxlag=365
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
    linemain=mainfile.readline().rstrip().split(delim_val, 4)
    junk=conffile.readline().rstrip()
    lineconf=conffile.readline().rstrip().split(delim_val, 4)
    outfile.write(header+delim_val+"confirmedOn"+"\n")
    count=Counter()
    dates=[]
    events=[]
    (pid, date, dateoffset, etype, stuff)=linemain
    (ptvid, confdate, confdateoffset, conftype, morestuff)=lineconf
    while(len(linemain) == 5 and len(lineconf) == 5):
        if(int(pid) < int(ptvid)):
            #can't confirm event, carry on
            linemain=mainfile.readline().rstrip().split(delim_val, 4)
            if(len(linemain) == 5):
                (pid, date, dateoffset, etype, stuff)=linemain
            count.add()
        elif(int(pid) > int(ptvid)):
            while(int(pid) > int(ptvid)):
                lineconf=conffile.readline().rstrip().split(delim_val, 4)
                if(len(lineconf) == 5):
                    (ptvid, confdate, confdateoffset, conftype, morestuff)=lineconf
                else:
                    break
        else:
            currentid=ptvid
            while(pid == ptvid):
                dates.append(int(confdateoffset))
                events.append(conftype)
                lineconf=conffile.readline().rstrip().split(delim_val, 4)
                if(len(lineconf) == 5):
                    (ptvid, confdate, confdateoffset, conftype, morestuff)=lineconf
                else:
                    break
            while(pid == currentid):
                #if event is confirmed, print to outfile
                confDate = confirmEvent(etype, int(dateoffset), events, dates, minlag, maxlag)
                if confDate is not False:
                    outfile.write(delim_val.join(linemain + [str(confDate)])+"\n")
                linemain=mainfile.readline().rstrip().split(delim_val, 4)
                if(len(linemain) == 5):
                    (pid, date, dateoffset, etype, stuff)=linemain
                else:
                    break
                count.add()
            dates=[]
            events=[]
    #there may be remaining lines in main file, but they can't be confirmed
    #while(len(linemain) == 5):
        #linemain=mainfile.readline().rstrip().split(delim_val, 4)
        #count.add()
    mainfile.close()
    conffile.close()
    outfile.close()
