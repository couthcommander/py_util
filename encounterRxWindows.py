#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime, sys, math, getopt
#lower this number if you want to test the output
maxinput=pow(10,15)

#
# added arguments for window size [-5, 1], which equates to [-150, 30) days
# python encounterRxWindows.py -b -5 -f 1 ef_incidents.csv ef_daysupply.csv ef_window.csv stuff
#

def splitCohort(string):
    junk = string.split(',', 4)
    cohortid = int(junk[0])
    cohortdate = junk[1]
    cohortdateint = int(junk[2])
    cohortlastenc = int(junk[3].rstrip())
    if(len(junk) == 5):
        cohortstuff = junk[4].rstrip()
    else:
        cohortstuff=''
    return [cohortid, cohortdate, cohortdateint, cohortlastenc, cohortstuff]

def splitOutcome(string):
    junk = string.split(',')
    #junk should only have four elements
    outcomeid = int(junk[0])
    outcomedate = junk[1]
    outcomedatei = int(junk[2])
    daysupply = int(float(junk[3].rstrip()))
    return [outcomeid, outcomedate, outcomedatei, daysupply]

#initdate and enddate are single dates
#outcomes are a list of dates and valid daysupplies
#intervalperiod defaults to 30 days
#goback allows you to calculate values earlier than one year prior to cohort date
def calcdata(initdate, enddate, outcomes, intervalperiod, goback=False, windowback=-5, windowforward=1):
    # don't want enddate to equal initdate
    if initdate == enddate:
        enddate = initdate + 1
    #initdate = 0
    #enddate = 29, endperiod -> 0
    #enddate = 30, endperiod -> 1
    endperiod = int((enddate-initdate)/intervalperiod)
    if len(outcomes):
        begperiod = int((outcomes[0][0]-initdate)/intervalperiod)
    else:
        begperiod = endperiod + 1
    # create period indicators
    if goback and begperiod < -360/intervalperiod:
        times = range(begperiod, endperiod+1)
    else:
        times = range(-360/intervalperiod, endperiod+1)
    # default all values to zero
    values = [0 for i in times]
    if len(outcomes):
        mydays = set([])
        # set of all days with prescription
        for cmpdate, daysupply in outcomes:
            mydays.update(range(cmpdate-initdate, cmpdate+daysupply-initdate))
        # [a,b] window, count days with prescription
        # period = -12 looks at [-510, -331]
        for i in times:
            a = (i+windowback)*intervalperiod
            b = a+(windowforward-windowback)*intervalperiod
            cnt = len(mydays.intersection(range(a,b)))
            values[times.index(i)] = cnt
    return [times, values]

def usage():
    print "usage: " + sys.argv[0] + " [-b -5] [-f 1] [-h] cohortfile outcomefile outputfile flagname"

if __name__=='__main__':
    intervalperiod=30
    windowback = -5
    windowforward = 1
    try:
        opts, args = getopt.getopt(sys.argv[1:], "b:f:h", ["windowback=", "windowforward=", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-b", "--windowback"):
            windowback = int(arg)
        elif opt in ("-f", "--windowforward"):
            windowforward = int(arg)
    if len(args) != 4:
        usage()
        sys.exit(1)
    (ifile, efile, ofile, flag)=args
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    junk = enfile.readline()
    header = infile.readline().rstrip()+",time,"+flag
    outfile.write(header+"\n")

#need to read in data from enfile until new ids are encountered
#put values into dictionary
    linecohort = infile.readline()
    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort)
    lineoutcome = enfile.readline()
    (outcomeid, odate, odateint, daysupply) = splitOutcome(lineoutcome)
    data = []
    if daysupply > 0:
        data.append([odateint, daysupply])
    count = 0
    while(len(linecohort) > 1 and len(lineoutcome) > 1):
        if(cohortid > outcomeid):
            #keep reading from enfile
            while(cohortid > outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, daysupply) = splitOutcome(lineoutcome)
                    data = []
                    if daysupply > 0:
                        data.append([odateint, daysupply])
                else:
                    break
        elif(cohortid < outcomeid):
            #keep reading from infile
            while(cohortid < outcomeid):
                res = calcdata(cdateint, clastenc, [], intervalperiod, False, windowback, windowforward)
                #output the current cohort, that has no matches
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                for t, v in zip(res[0], res[1]):
                    outfile.write(",".join(output+[str(t), str(v)])+"\n")
                count+=1
                if not count%1000:
                    print count
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort)
                else:
                    break
        else:
            previd = outcomeid
            #read from enfile until id's don't match
            while(cohortid == outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, daysupply) = splitOutcome(lineoutcome)
                    if daysupply > 0:
                        data.append([odateint, daysupply])
                else:
                    break
            #at this point the last value in data do not match (unless we reached the last line)
            if(len(lineoutcome) > 1 and daysupply > 0):
                newdata = [data.pop()]
            else:
                newdata = None
            while(cohortid == previd):
                #need to compare cohortdate versus outcome dates
                res = calcdata(cdateint, clastenc, data, intervalperiod, False, windowback, windowforward)
                #output the results for the current cohort
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                for t, v in zip(res[0], res[1]):
                    outfile.write(",".join(output+[str(t), str(v)])+"\n")
                count+=1
                if not count%1000:
                    print count
                #read in the next line from infile
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort)
                else:
                    break
            #restore data from newdata (cohortid should be > previd, but possibly == outcomeid)
            if(newdata is not None):
                data = [newdata.pop()]
            else:
                data = []
        if count > maxinput:
            sys.exit()
    #need to print blank lines for anything left in infile
    while(len(linecohort) > 1):
        res = calcdata(cdateint, clastenc, [], intervalperiod, False, windowback, windowforward)
        #output the current cohort, that has no matches
        output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
        if(cohortstuff != ''):
            output.append(cohortstuff)
        for t, v in zip(res[0], res[1]):
            outfile.write(",".join(output+[str(t), str(v)])+"\n")
        count+=1
        if not count%1000:
            print count
        linecohort=infile.readline()
        if(len(linecohort) > 1):
            (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort)
