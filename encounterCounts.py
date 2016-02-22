#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import argparse
#lower this number if you want to test the output
maxinput=pow(10,15)
#python encounterCounts.py ef_incidents.csv ef_druglist.csv ef_output4.csv 1 myname 360

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
    #junk should only have four elements
    outcomeid = int(junk[0])
    outcomedate = junk[1]
    outcomedatei = int(junk[2])
    name = junk[3].rstrip()
    return [outcomeid, outcomedate, outcomedatei, name]

def buildLastEnc(lastenc, lastfield, mergefield, header, d):
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
        alllastenc[row[mergecol]] = row[lastcol]
        lastline = lastfile.readline().rstrip()
    lastfile.close()
    return [alllastenc, inmergecol]

#initdate and enddate are single dates
#outcomes are a list of dates and drug names
#intervalperiod defaults to 30 days
#lastback sets the date range to examine
#method is 1,2,3
def calcdata(initdate, enddate, outcomes, intervalperiod, lastback, method):
    # don't want enddate to equal initdate
    if initdate == enddate:
        enddate = initdate + 1
    endperiod = int((enddate-initdate-1)/intervalperiod)
    #if len(outcomes):
        #tmpoutcomes = []
        ## remove any dates further than lastback
        #threshDate = initdate - maxback
        #for i in outcomes:
            #if i[0] >= threshDate:
                #tmpoutcomes.append(i)
        #outcomes = tmpoutcomes
    if len(outcomes):
        begperiod = int((outcomes[0][0]-initdate-1)/intervalperiod)
    else:
        begperiod = endperiod + 1
    startingperiod = -360/intervalperiod
    times = range(startingperiod, endperiod+1)
    # default all values to missing
    if method == 3:
        miss_val = '.,.'
    else:
        miss_val = '.'
    values = [miss_val for i in times]

    if len(outcomes):
        togglePost = False
        for key, period in enumerate(times):
            index = 0
            first = None
            a = period * intervalperiod + 1 + initdate
            b = a + intervalperiod - 1
            # SAME AS: b = (period + 1) * intervalperiod + initdate
            validoutcomes = []
            uniqoutcomes = []
            # remove any dates in outcomes more than 360 days old
            for i in outcomes:
                if i[0] >= (a-lastback) and i[0] <= b:
                    validoutcomes.append(i)
                    if method in [2,3] and i[1] not in uniqoutcomes:
                        uniqoutcomes.append(i[1])
            x = str(len(validoutcomes))
            if method in [2,3]:
                y = str(len(uniqoutcomes))
            if method == 1:
                values[key] = x
            elif method == 2:
                values[key] = y
            else:
                values[key] = x+','+y
    return [times, values]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    intervalperiod = 30
    parser.add_argument("cohortfile", help='cohort file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("outcomefile", help='encounter file with format ID,DATE,OFFSET,RX,DAYSUPPLY,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("method", help='count method [1=all, 2=unique, 3=both]')
    parser.add_argument("flagname", help='name of created indicator flag')
    parser.add_argument("lookback", help='maximum days to look back in the past', type=int, nargs='?', default=360)
    parser.add_argument("-l", "--lastencounterfile", help="last encounter file, to be merged with cohort file")
    parser.add_argument("-f", "--lastfield", help="field with last encounter date offset", default='LastEncdate_i180')
    parser.add_argument("-e", "--encgap", help="encounter day gap", default=180, type=int)
    parser.add_argument("-m", "--mergefield", help="field to merge with cohort file", default='key1')
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    args = parser.parse_args()
    ifile = args.cohortfile
    efile = args.outcomefile
    ofile = args.outputfile
    method = args.method
    lookback = args.lookback
    delim = args.delimiter

    # method 1: number of outcomes
    # method 2: unique drug names
    # method 3: both
    if method in ['1', 'all']:
        method = 1
    elif method in ['2', 'unique']:
        method = 2
    elif method in ['3', 'both']:
        method = 3
    else:
        sys.exit(1)
    infile = open(ifile)
    enfile = open(efile)
    outfile = open(ofile,'w')
    junk = enfile.readline()
    header = infile.readline().rstrip().split(delim)
    if args.lastencounterfile is not None:
        (alllastenc, inmergecol) = buildLastEnc(args.lastencounterfile, args.lastfield, args.mergefield, header, delim)
        # modify header to include LastEncounterDateOffset
        header = header[0:3] + [args.lastfield] + header[3:]
    else:
        alllastenc = {}
        inmergecol = None
    header += ['time']
    if method in [1, 3]:
        header += ["%s_%s" % (args.flagname, lookback)]
    if method in [2, 3]:
        header += ["Unique%s_%s" % (args.flagname, lookback)]
    outfile.write(delim.join(header) + "\n")

#need to read in data from enfile until new ids are encountered
#put values into dictionary
    linecohort = infile.readline()
    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
    lineoutcome = enfile.readline()
    (outcomeid, odate, odateint, name) = splitOutcome(lineoutcome, delim)
    data = [[odateint, name]]
    count = 0
    while(len(linecohort) > 1 and len(lineoutcome) > 1):
        if(cohortid > outcomeid):
            #keep reading from enfile
            while(cohortid > outcomeid):
                lineoutcome = enfile.readline()
                if(len(lineoutcome) > 1):
                    (outcomeid, odate, odateint, name) = splitOutcome(lineoutcome, delim)
                    data = [[odateint, name]]
                else:
                    break
        elif(cohortid < outcomeid):
            #keep reading from infile
            while(cohortid < outcomeid):
                res = calcdata(cdateint, clastenc+args.encgap, [], intervalperiod, lookback, method)
                #output the current cohort, that has no matches
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                for t, v in zip(res[0], res[1]):
                    outfile.write(delim.join(output+[str(t), str(v)])+"\n")
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
                    (outcomeid, odate, odateint, name) = splitOutcome(lineoutcome, delim)
                    data.append([odateint, name])
                else:
                    break
            #at this point the last value in data do not match (unless we reached the last line)
            if len(lineoutcome) > 1:
                newdata = [data.pop()]
            while(cohortid == previd):
                #need to compare cohortdate versus outcome dates
                res = calcdata(cdateint, clastenc+args.encgap, data, intervalperiod, lookback, method)
                #output the results for the current cohort
                output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
                if(cohortstuff != ''):
                    output.append(cohortstuff)
                for t, v in zip(res[0], res[1]):
                    outfile.write(delim.join(output+[str(t), str(v)])+"\n")
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
        res = calcdata(cdateint, clastenc+args.encgap, [], intervalperiod, lookback, method)
        #output the current cohort, that has no matches
        output = [str(cohortid), cdate, str(cdateint), str(clastenc)]
        if(cohortstuff != ''):
            output.append(cohortstuff)
        for t, v in zip(res[0], res[1]):
            outfile.write(delim.join(output+[str(t), str(v)])+"\n")
        count+=1
        if not count%10000:
            print "\r" + str(count),
        linecohort=infile.readline()
        if(len(linecohort) > 1):
            (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim, inmergecol, alllastenc)
    infile.close()
    enfile.close()
    outfile.close()
