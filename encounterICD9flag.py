#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import argparse
#lower this number if you want to test the output
maxinput=pow(10,15)

def splitCohort(string, d, mergeby=None, lastdict={}):
    if mergeby is None:
        junk = string.rstrip().split(d, 4)
        cohortid = int(junk[0])
        cohortdate = junk[1]
        cohortdateint = int(junk[2])
        cohortlastenc = int(junk[3])
        if(len(junk) == 5):
            cohortstuff = junk[4]
        else:
            cohortstuff = ''
    else:
        junk = string.rstrip().split(d, mergeby+1)
        cohortid = int(junk[0])
        cohortdate = junk[1]
        cohortdateint = int(junk[2])
        # look up last encounter date
        cohortlastenc = int(lastdict[junk[mergeby]])
        cohortstuff = d.join(junk[3:])
    return [cohortid, cohortdate, cohortdateint, cohortlastenc, cohortstuff]

def splitOutcome(string, d):
    junk = string.rstrip().split(d)
    #junk should only have three elements
    outcomeid = int(junk[0])
    outcomedate = junk[1]
    outcomedatei = int(junk[2].rstrip())
    return [outcomeid, outcomedate, outcomedatei]

def writeOut1(fh, out, dat, delim):
    for t, v, d, i in zip(dat[0], dat[1], dat[2], dat[3]):
        fh.write(delim.join(out+[str(t), str(v), str(d)])+"\n")

def writeOut2(fh, out, dat, delim):
    for t, v, d, i in zip(dat[0], dat[1], dat[2], dat[3]):
        fh.write(delim.join(out+[str(t), str(v), str(i), str(d)])+"\n")

def buildLastEnc(lastenc, lastfield, mergefield, header, d, gapsize):
    alllastenc = {}
    lastfile = open(lastenc)
    # read last encounter dates into dictionary
    lasthead = lastfile.readline().rstrip().split(d)
    if lastfield in lasthead:
        lastcol = lasthead.index(lastfield)
    else:
        print "lastfield not found in lastencounterfile"
        sys.exit(1)
    if mergefield in lasthead:
        mergecol = lasthead.index(mergefield)
    else:
        print "mergefield not found in lastencounterfile"
        sys.exit(2)
    if mergefield in header:
        inmergecol = header.index(mergefield)
    else:
        print "mergefield not found in cohortfile"
        sys.exit(3)
    lastline = lastfile.readline().rstrip()
    while len(lastline) > 1:
        row = lastline.split(d)
        alllastenc[row[mergecol]] = row[lastcol]+gapsize
        lastline = lastfile.readline().rstrip()
    lastfile.close()
    return [alllastenc, inmergecol]

#initdate and enddate are single dates
#cmpdates are a list of dates when a ICD9 code was present
#intervalperiod defaults to 30 days
#maxback allows you to take values up to that amount
#goback allows you to calculate values earlier than one year prior to cohort date
def calcdata(initdate, enddate, cmpdates, intervalperiod, maxback, goback=False):
    # don't want enddate to equal initdate
    if initdate == enddate:
        enddate = initdate + 1
    endperiod = int((enddate-initdate-1)/intervalperiod)
    if len(cmpdates):
        begperiod = int((cmpdates[0]-initdate-1)/intervalperiod)
        firstevent = cmpdates[0]
        # don't view dates prior to 1 year
        stop = 360
        if maxback < stop:
            stop = maxback
        index = 0
        while len(cmpdates) > index and begperiod < -1*stop/intervalperiod:
            begperiod = int((cmpdates[index]-initdate-1)/intervalperiod)
            firstevent = cmpdates[index]
            index += 1
        # if you made it to the end without finding a period after 1-year prior
        if index == len(cmpdates) and begperiod < -1*stop/intervalperiod:
            begperiod = endperiod + 1
    else:
        begperiod = endperiod + 1
    # this step shouldn't happen anymore
    if begperiod < -360/intervalperiod:
        if goback:
            times = range(begperiod, endperiod+1)
        else:
            times = range(-360/intervalperiod, endperiod+1)
        values = [1 for i in times]
        matches = [firstevent for i in times]
    elif begperiod > endperiod:
        times = range(-360/intervalperiod, endperiod+1)
        values = [0 for i in times]
        matches = ['.' for i in times]
    else:
        timesA = range(-360/intervalperiod, begperiod)
        valuesA = [0 for i in timesA]
        matchesA = ['.' for i in timesA]
        timesB = range(begperiod, endperiod+1)
        valuesB = [1 for i in timesB]
        matchesB = [firstevent for i in timesB]
        times = timesA + timesB
        values = valuesA + valuesB
        matches = matchesA + matchesB
    inter = ['.' for i in times]
    for ix, t in enumerate(times):
        a = t * intervalperiod + 1
        b = (t + 1) * intervalperiod
        inter[ix] = "%s..%s" % (a+initdate,b+initdate)
    return [times, values, matches, inter]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    intervalperiod = 30
    parser.add_argument("cohortfile", help='cohort file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("outcomefile", help='encounter file with format ID,DATE,OFFSET,RX,DAYSUPPLY,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("flagname", help='name of created indicator flag')
    parser.add_argument("maxback", help='maximum days to look back in the past', type=int, nargs='?', default=365)
    parser.add_argument("-l", "--lastencounterfile", help="last encounter file, to be merged with cohort file")
    parser.add_argument("-f", "--lastfield", help="field with last encounter date offset", default='LastEncdate_i180')
    parser.add_argument("-e", "--encgap", help="encounter day gap", default=180, type=int)
    parser.add_argument("-m", "--mergefield", help="field to merge with cohort file", default='key1')
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--interval", help='include period interval in output', action='store_true')
    args = parser.parse_args()
    ifile = args.cohortfile
    efile = args.outcomefile
    ofile = args.outputfile
    maxback = args.maxback
    delim = args.delimiter
    infile = open(ifile)
    enfile = open(efile)
    outfile = open(ofile,'w')
    junk = enfile.readline()
    header = infile.readline().rstrip().split(delim)
    if args.lastencounterfile is not None:
        (alllastenc, inmergecol) = buildLastEnc(args.lastencounterfile, args.lastfield, args.mergefield, header, delim, args.encgap)
        # modify header to include LastEncounterDateOffset
        header = header[0:3] + [args.lastfield] + header[3:]
    else:
        alllastenc = {}
        inmergecol = None
    header = header + ['time', args.flagname]
    if args.interval:
        writeOut = writeOut2
        header += [args.flagname+'_period']
    else:
        writeOut = writeOut1
    header += [args.flagname+'_event_i']
    outfile.write(delim.join(header) + "\n")

#need to read in data from enfile until new ids are encountered
#put values into dictionary
    linecohort = infile.readline()
    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
    lineoutcome = enfile.readline()
    (outcomeid, odate, odateint) = splitOutcome(lineoutcome, delim)
    data = [odateint]
    count = 0
    while(len(linecohort) > 1 and len(lineoutcome) > 1):
        if(cohortid > outcomeid):
            #keep reading from enfile
            while(cohortid > outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint) = splitOutcome(lineoutcome, delim)
                    data = [odateint]
                else:
                    break
        elif(cohortid < outcomeid):
            #keep reading from infile
            while(cohortid < outcomeid):
                res = calcdata(cdateint, clastenc, [], intervalperiod, maxback)
                #output the current cohort, that has no matches
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                writeOut(outfile, output, res, delim)
                count+=1
                if not count%10000:
                    print "\r" + str(count),
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
                else:
                    break
        else:
            previd = outcomeid
            #read from enfile until id's don't match
            while(cohortid == outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint) = splitOutcome(lineoutcome, delim)
                    data.append(odateint)
                else:
                    break
            #at this point the last value in data do not match (unless we reached the last line)
            if(len(lineoutcome) > 1):
                newdata = data.pop()
            else:
                newdata = None
            while(cohortid == previd):
                #need to compare cohortdate versus outcome dates
                res = calcdata(cdateint, clastenc, data, intervalperiod, maxback)
                #output the results for the current cohort
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                writeOut(outfile, output, res, delim)
                count+=1
                if not count%10000:
                    print "\r" + str(count),
                #read in the next line from infile
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
                else:
                    break
            #restore data from newdata (cohortid should be > previd, but possibly == outcomeid)
            if(newdata is not None):
                data = [newdata]
        if count > maxinput:
            sys.exit()
    #need to print blank lines for anything left in infile
    while(len(linecohort) > 1):
        res = calcdata(cdateint, clastenc, [], intervalperiod, maxback)
        #output the current cohort, that has no matches
        output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
        if(cohortstuff != ''):
            output.append(cohortstuff)
        writeOut(outfile, output, res, delim)
        count+=1
        if not count%10000:
            print "\r" + str(count),
        linecohort=infile.readline()
        if(len(linecohort) > 1):
            (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
    infile.close()
    enfile.close()
    outfile.close()
