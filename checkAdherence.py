#!/usr/bin/python
import sys
import argparse
#lower this number if you want to test the output
maxinput=pow(10, 10)

# check the number of days missed during each period

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

def writeOut1(fh, out, dat, delim):
    for t, v, i in zip(dat[0], dat[1], dat[2]):
        fh.write(delim.join(out+[str(t), str(v)])+"\n")

def writeOut2(fh, out, dat, delim):
    for t, v, i in zip(dat[0], dat[1], dat[2]):
        fh.write(delim.join(out+[str(t), str(v), str(i)])+"\n")

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

class Counter():
    def __init__(self):
        self.count = 0

    def add(self):
        self.count += 1
        if not self.count % 10000:
            print "\r" + str(self.count),
        if self.count > maxinput:
            sys.exit()

class Nothing():
    def __init__(self):
        pass

    def add(self):
        pass

def mysort(a,b):
    return cmp(a[0],b[0])

def calcDSIH(dat, stockpile, vfun, fh, delim, skip=False):
    if len(dat) <= 1:
        return(None, [])
    curid = dat[0]
    dat = [vfun(dat)]
    line = fh.readline().rstrip().split(delim)
    while len(line) > 1 and line[0] == curid:
        dat.append(vfun(line))
        line = fh.readline().rstrip().split(delim)
    if skip:
        return(None, line)
    dat.sort(mysort)
    res = [[dat[i][0],0,0] for i in range(len(dat))]
    res[0][2] = dat[0][1]
    dupday = []
    for i in range(1, len(dat)):
        res[i][2] = dat[i][1]
        dayspassed = dat[i][0] - dat[i-1][0]
        # previous DS - days passed
        if dayspassed > 0:
            pre = res[i-1][2] - dayspassed
            if pre > 0:
                res[i][2] += int(round(pre * stockpile/100.0))
            res[i][1] = pre
        elif dayspassed == 0:
             post = max(res[i-1][2], res[i][2])
             res[i-1][2] = post
             res[i][2] = post
             dupday.append(i)
    # remove duplicates
    if len(dupday):
        dupday.reverse()
        for i in dupday:
            del res[i]
    return(res, line)

def calcdata(initdate, enddate, dat, intervalperiod, gap):
    # don't want enddate to equal initdate
    if initdate == enddate:
        enddate = initdate + 1
    endperiod = int((enddate-initdate-1)/intervalperiod)
    if len(dat):
        begperiod = int((dat[0][0]-initdate-1)/intervalperiod)
    else:
        begperiod = endperiod + 1
    times = range(-360/intervalperiod, endperiod+1)
    values = [intervalperiod for i in times]
    inter = ['.' for i in times]
    p1 = ['.' for i in times]
    p2 = ['.' for i in times]
    for ix, t in enumerate(times):
        p1[ix] = t * intervalperiod + 1
        p2[ix] = (t + 1) * intervalperiod
        inter[ix] = "%s..%s" % (p1[ix]+initdate, p2[ix]+initdate)
    if len(dat):
        mydates = []
        for outix in range(len(dat)):
            (cmpdate, pre, post) = dat[outix]
            mydates.extend([i for i in range(cmpdate, cmpdate+post)])
        mydates = set(mydates)
        for ix, t in enumerate(times):
            values[ix] = intervalperiod - sum([int(i+initdate in mydates) for i in range(p1[ix], p2[ix]+1)])
    return [times, values, inter]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    intervalperiod = 30
    # daysupply is column 5
    dcol = 4
    parser.add_argument("cohortfile", help='cohort file with format ID,DATE,OFFSET,ETC')
    parser.add_argument("outcomefile", help='encounter file with format ID,DATE,OFFSET,RX,DAYSUPPLY,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("flagname", help='name of created indicator flag')
    parser.add_argument("-g", "--gap", help='gap size, defaults to 0', default=0, type=int)
    parser.add_argument("-l", "--lastencounterfile", help="last encounter file, to be merged with cohort file")
    parser.add_argument("-f", "--lastfield", help="field with last encounter date offset", default='LastEncdate_i180')
    parser.add_argument("-m", "--mergefield", help="field to merge with cohort file", default='key1')
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--dsih", help='stockpiling percentage, 0-100%%', default=100, type=int)
    parser.add_argument("--missingds", help='value for missing day supply, defaults to 90', default=90, type=int)
    parser.add_argument("--interval", help='include period interval in output', action='store_true')
    parser.add_argument("--count", help='turn counter on', action='store_true')
    args = parser.parse_args()
    delim_val = args.delimiter
    infile = open(args.cohortfile)
    rxfile = open(args.outcomefile)
    outfile = open(args.outputfile, 'w')
    drug = args.flagname
    adherence_gap = args.gap
    dsih_percent = args.dsih
    missing_val = ''
    ### validate arguments
    if dsih_percent < 0 or dsih_percent > 100:
        print "DSIH% must be between 0 and 100"
        sys.exit()
    header = rxfile.readline().rstrip().split(delim_val)
    if args.lastencounterfile is not None:
        (alllastenc, inmergecol) = buildLastEnc(args.lastencounterfile, args.lastfield, args.mergefield, header, delim_val)
    else:
        alllastenc = {}
        inmergecol = None

    ### header for outfile
    header = [infile.readline().rstrip(), 'time', drug+'_DaysMissed']
    if args.interval:
        writeOut = writeOut2
        header.append(drug+'_period')
    else:
        writeOut = writeOut1
    outfile.write(delim_val.join(header) + "\n")
    if args.count:
        cnt = Counter()
    else:
        cnt = Nothing()
    def vals(x):
        if x[dcol] == '':
            x[dcol] = args.missingds
        return [int(x[i]) for i in [2,dcol]]

    linecohort = infile.readline()
    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim_val, inmergecol, alllastenc)
    rx = rxfile.readline().rstrip().split(delim_val)
    while len(linecohort) > 1:
        if rx[0] == '' or cohortid < int(rx[0]):
            res = calcdata(cdateint, clastenc, [], intervalperiod, adherence_gap)
            writeOut(outfile, [linecohort.rstrip()], res, delim_val)
            linecohort = infile.readline()
            if(len(linecohort) > 1):
                (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim_val, inmergecol, alllastenc)
            else:
                break
            cnt.add()
        elif cohortid > int(rx[0]):
            (dsih, rx) = calcDSIH(rx, dsih_percent, vals, rxfile, delim_val, skip=True)
        else:
            matched_id = int(rx[0])
            (dsih, rx) = calcDSIH(rx, dsih_percent, vals, rxfile, delim_val)
            while cohortid == matched_id:
                res = calcdata(cdateint, clastenc, dsih, intervalperiod, adherence_gap)
                writeOut(outfile, [linecohort.rstrip()], res, delim_val)
                linecohort = infile.readline()
                if(len(linecohort) > 1):
                    (cohortid, cdate, cdateint, clastenc, cohortstuff) = splitCohort(linecohort, delim_val, inmergecol, alllastenc)
                else:
                    break
                cnt.add()
    infile.close()
    rxfile.close()
    outfile.close()
