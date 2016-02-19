#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import argparse
#lower this number if you want to test the output
maxinput=pow(10,15)

def splitCohort(string, d, mergeby=None, lastdict={}):
    if mergeby is None:
        junk = string.split(d, 4)
        cohortid = int(junk[0])
        cohortdate = junk[1]
        cohortdateint = int(junk[2])
        cohortlastenc = int(junk[3].rstrip())
        if(len(junk) == 5):
            cohortstuff = junk[4].rstrip()
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
    junk = string.split(d)
    outcomeid = int(junk[0])
    outcomedate = junk[1]
    outcomedatei = int(junk[2])
    labvalue = float(junk[3].rstrip())
    return [outcomeid, outcomedate, outcomedatei, labvalue]

def writeOut1(fh, out, dat, delim):
    for t, v, I, V, d, i in zip(dat[0], dat[1], dat[2], dat[3], dat[4], dat[5]):
        fh.write(delim.join(out+[str(t), str(v), str(I), str(V), str(d)])+"\n")

def writeOut2(fh, out, dat, delim):
    for t, v, I, V, d, i in zip(dat[0], dat[1], dat[2], dat[3], dat[4], dat[5]):
        fh.write(delim.join(out+[str(t), str(v), str(I), str(V), str(i), str(d)])+"\n")

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
#outcomes are a list of dates and lab values
#intervalperiod defaults to 30 days
#maxback sets age of values respective to initdate
#lastback sets age of values respective to period
#goback allows you to calculate values earlier than one year prior to cohort date
def calcdata(initdate, enddate, outcomes, intervalperiod, maxback, lastback, lastforward, goback=False):
    # don't want enddate to equal initdate
    if initdate == enddate:
        enddate = initdate + 1
    endperiod = int((enddate-initdate-1)/intervalperiod)
    if len(outcomes):
        tmpoutcomes = []
        # remove any dates further than maxback
        threshDate = initdate - maxback
        for i in outcomes:
            if i[0] >= threshDate:
                tmpoutcomes.append(i)
        outcomes = tmpoutcomes
    if len(outcomes):
        begperiod = int((outcomes[0][0]-initdate-1)/intervalperiod)
    else:
        begperiod = endperiod + 1
    startingperiod = -360/intervalperiod
    if goback and begperiod < startingperiod:
        times = range(begperiod, endperiod+1)
    else:
        times = range(startingperiod, endperiod+1)
    # default all values to missing
    values = ['.' for i in times]
    ind = ['.' for i in times]
    values0 = ['.' for i in times]
    matches = ['.' for i in times]
    inter = ['.' for i in times]
    if len(outcomes):
        togglePost = False
        for key, period in enumerate(times):
            a = period * intervalperiod + 1 + initdate
            b = (period + 1) * intervalperiod + initdate
            inter[key] = "%s..%s" % (a, b)
            index = 0
            first = None
            validoutcomes = []
            # remove any dates in outcomes more than 360 days old
            for i in outcomes:
                if i[0] >= (a-lastback):
                    validoutcomes.append(i)
            if(len(validoutcomes) == 0):
                continue
            # I think we want to save the lab value closest to point A
            while len(validoutcomes) > index and validoutcomes[index][0] <= b:
                if first is None and validoutcomes[index][0] >= a:
                    first = index
                index += 1
            val = None
            # first is the first date in validoutcomes past A and before B - or it will be None
            # index is the first date in validoutcomes past B
            # thus, index-1 is the last date before B
            # for periods with no value take most recent
            # if first is None and index > 0 and a - validoutcomes[index-1][0] <= maxback:
            if first is None and index > 0:
                # val will be missing when index is zero -- means first date is past b
                # val will be missing if previous was more than MAXBACK days ago
                val = index-1
                # val is not observed within (a,b) interval
                obs = 0
            elif first is not None:
                val = first
                # val is observed within (a,b) interval
                obs = 1
            if val is not None:
                values[key] = validoutcomes[val][1]
                ind[key] = obs
                matches[key] = validoutcomes[val][0]
                if togglePost or (period >= 0 and obs == 1):
                    values0[key] = values[key]
                    togglePost = True
    return [times, values, ind, values0, matches, inter]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    intervalperiod = 30
    parser.add_argument("cohortfile", help='cohort file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("outcomefile", help='encounter file with format ID,DATE,OFFSET,LABVALUES,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("flagnameprefix", help='prefix name of created indicator flag')
    parser.add_argument("--maxback", help="maximum age of values respective to initdate", type=int, default=365)
    parser.add_argument("--lastback", help="maximum age of values respective to period", type=int, default=360)
    parser.add_argument("--lastforward", help="number of days to include within interval", type=int, default=30)
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
    delim = args.delimiter
    flag = args.flagnameprefix
    maxback = args.maxback
    lastback = args.lastback
    lastforward = args.lastforward
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
    header += ['time', flag+'_lab_value', flag+'_lab_obs', flag+'_lab_value_postday0']
    if args.interval:
        writeOut = writeOut2
        header += [flag+'_period']
    else:
        writeOut = writeOut1
    header += [flag+'_event_i']
    outfile.write(delim.join(header) + "\n")

#need to read in data from enfile until new ids are encountered
#put values into dictionary
    linecohort = infile.readline()
    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
    lineoutcome = enfile.readline()
    (outcomeid, odate, odateint, labvalue) = splitOutcome(lineoutcome, delim)
    data = [[odateint, labvalue]]
    count = 0
    while(len(linecohort) > 1 and len(lineoutcome) > 1):
        if(cohortid > outcomeid):
            #keep reading from enfile
            while(cohortid > outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, labvalue) = splitOutcome(lineoutcome, delim)
                    data = [[odateint, labvalue]]
                else:
                    break
        elif(cohortid < outcomeid):
            #keep reading from infile
            while(cohortid < outcomeid):
                res = calcdata(cdateint, clastenc, [], intervalperiod, maxback, lastback, lastforward)
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
                    (outcomeid, odate, odateint, labvalue) = splitOutcome(lineoutcome, delim)
                    data.append([odateint, labvalue])
                else:
                    break
            #at this point the last value in data do not match (unless we reached the last line)
            if len(lineoutcome) > 1:
                newdata = [data.pop()]
            while(cohortid == previd):
                #need to compare cohortdate versus outcome dates
                res = calcdata(cdateint, clastenc, data, intervalperiod, maxback, lastback, lastforward)
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
            if len(newdata) == 1:
                data = [newdata.pop()]
        if count > maxinput:
            sys.exit()
    #need to print blank lines for anything left in infile
    while(len(linecohort) > 1):
        res = calcdata(cdateint, clastenc, [], intervalperiod, maxback, lastback, lastforward)
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
