#!/usr/bin/python
# -*- coding: utf-8 -*-

# two input files
# 1) cohort file, with subject and [incident] date
# 2) rx file, subset by drug, with subject and dates
# algorithm
# create periods surrounding incident date
# go back X days and ahead Y days, with period interval Z
# look for presence of rx within periods
# output file
# 1) subject, date, periods, indicators

import datetime, sys, math, getopt
#lower this number if you want to test the output
maxinput=pow(10,15)

def splitCohort(string):
    junk = string.split(',', 3)
    cohortid = int(junk[0])
    cohortdate = junk[1]
    cohortdateint = int(junk[2])
    if(len(junk) == 4):
        cohortstuff = junk[3].rstrip()
    else:
        cohortstuff=''
    return [cohortid, cohortdate, cohortdateint, cohortstuff]

def splitOutcome(string):
    junk = string.split(',', 3)
    outcomeid = int(junk[0])
    outcomedate = junk[1]
    outcomedatei = int(junk[2])
    if(len(junk) == 4):
        encstuff = junk[3].rstrip()
    else:
        encstuff = ''
    return [outcomeid, outcomedate, outcomedatei, encstuff]

#initdate is a single date
#outcomes are a list of dates
#intervalperiod defaults to 30 days
#back is first period to examine, days before incident
#ahead is last period to examine, days after incident
def calcdata(initdate, outcomes, intervalperiod=30, back=180, ahead=0):
    enddate = initdate + ahead
    # should enddate equal initdate?
    endperiod = int((ahead-1)/intervalperiod)
    times = range(-1*back/intervalperiod, endperiod+1)
    consolidate = True
    # return one line instead of one for each period
    if consolidate:
        values = [0]
        if len(outcomes):
            for cmpdate in outcomes:
                period = int((cmpdate-initdate-1)/intervalperiod)
                if period in times:
                    values = [1]
                    break
        times = ["(%s_%s]" % (back*-1, ahead)]
    else:
        # default all values to zero
        values = [0 for i in times]
        if len(outcomes):
            for cmpdate in outcomes:
                # might be worth adding test
                # break if cmpdate > enddate
                period = int((cmpdate-initdate-1)/intervalperiod)
                if period in times:
                    values[times.index(period)] = 1
    return [times, values]

def usage():
    print "usage: " + sys.argv[0] + " cohortfile outcomefile outputfile flag back ahead"

if __name__=='__main__':
    intervalperiod=30
    args = sys.argv[1:]
    if len(args) != 6:
        usage()
        sys.exit(1)
    (ifile, efile, ofile, flag, back, ahead)=args
    infile=open(ifile)
    enfile=open(efile)
    outfile=open(ofile,'w')
    back = int(back)
    ahead = int(ahead)
    junk = enfile.readline()
    header = infile.readline().rstrip()+",time,"+flag
    outfile.write(header+"\n")

#need to read in data from enfile until new ids are encountered
#put values into dictionary
    linecohort = infile.readline()
    (cohortid, cdate, cdateint, cohortstuff) = splitCohort(linecohort)
    lineoutcome = enfile.readline()
    (outcomeid, odate, odateint, ostuff) = splitOutcome(lineoutcome)
    data = [odateint]
    count = 0
    while(len(linecohort) > 1 and len(lineoutcome) > 1):
        if(cohortid > outcomeid):
            #keep reading from enfile
            while(cohortid > outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, ostuff) = splitOutcome(lineoutcome)
                    data = [odateint]
                else:
                    break
        elif(cohortid < outcomeid):
            #keep reading from infile
            while(cohortid < outcomeid):
                res = calcdata(cdateint, [], intervalperiod, back, ahead)
                #output the current cohort, that has no matches
                output = [str(cohortid), cdate, str(cdateint)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                for t, v in zip(res[0], res[1]):
                    outfile.write(",".join(output+[str(t), str(v)])+"\n")
                count+=1
                if not count%1000:
                    print count
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, cohortstuff) = splitCohort(linecohort)
                else:
                    break
        else:
            previd = outcomeid
            #read from enfile until id's don't match
            while(cohortid == outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, ostuff) = splitOutcome(lineoutcome)
                    data.append(odateint)
                else:
                    break
            #at this point the last value in data do not match (unless we reached the last line)
            if(len(lineoutcome) > 1):
                newdata = [data.pop()]
            else:
                newdata = None
            while(cohortid == previd):
                #need to compare cohortdate versus outcome dates
                res = calcdata(cdateint, data, intervalperiod, back, ahead)
                #output the results for the current cohort
                output = [str(cohortid), cdate, str(cdateint)]
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
                    (cohortid, cdate, cdateint, cohortstuff) = splitCohort(linecohort)
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
        res = calcdata(cdateint, [], intervalperiod, back, ahead)
        #output the current cohort, that has no matches
        output = [str(cohortid), cdate, str(cdateint)]
        if(cohortstuff != ''):
            output.append(cohortstuff)
        for t, v in zip(res[0], res[1]):
            outfile.write(",".join(output+[str(t), str(v)])+"\n")
        count+=1
        if not count%1000:
            print count
        linecohort=infile.readline()
        if(len(linecohort) > 1):
            (cohortid, cdate, cdateint, cohortstuff) = splitCohort(linecohort)
