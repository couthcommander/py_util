#!/usr/bin/python
import sys
import argparse
#lower this number if you want to test the output
maxinput=pow(10, 10)

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

# measure compliance
def calcDropout(start, dat, ix, gap):
    # dat[ix][0] == start
    lastdate = ix
    for i in range(ix+1, len(dat)):
        if dat[i][1] + gap >= 0:
            lastdate = i
        else:
            break
    return dat[lastdate]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help='delimited file, should contain PTID|DATE|OFFSET|DRUGNAME|ETC')
    parser.add_argument("rxfile", help='delimited file, should contain PTID|DATE|OFFSET|DAYSUPPLY')
    parser.add_argument("outputfile", help='output file, checking adherence')
    parser.add_argument("dscolumn", help='column name with day supply')
    parser.add_argument("flagname", help='drugname for created column')
    parser.add_argument("-d", "--dsih", help='stockpiling percentage, 0-100%%', default=100, type=int)
    parser.add_argument("-g", "--gap", help='gap size, defaults to 14', default=14, type=int)
    parser.add_argument("-m", "--missingds", help='value for missing day supply, defaults to 90', default=90, type=int)
    parser.add_argument("--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--count", help='turn counter on', action='store_true')
    args = parser.parse_args()
    delim_val = args.delimiter
    infile = open(args.infile)
    rxfile = open(args.rxfile)
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
    if args.dscolumn not in header:
        print "daysupply column [%s] not found" % (args.dscolumn)
        sys.exit(-1)
    dcol = header.index(args.dscolumn)
    ### header for outfile
    header = infile.readline().rstrip()
    # date of last refill
    fieldname1 = "%s_stop_%s_%s_Offset" % (drug, adherence_gap, dsih_percent)
    # daysupply of last refill
    fieldname2 = "%s_stop_%s_%s_Supply" % (drug, adherence_gap, dsih_percent)
    outfile.write(header + delim_val + fieldname1 + delim_val + fieldname2 + "\n")
    if args.count:
        cnt = Counter()
    else:
        cnt = Nothing()
    def vals(x):
        if x[dcol] == '':
            x[dcol] = args.missingds
        return [int(x[i]) for i in [2,dcol]]
    def missingRow(line):
        return line + delim_val + missing_val + delim_val + missing_val + "\n"

    linemain = infile.readline().rstrip().split(delim_val, 4)
    rx = rxfile.readline().rstrip().split(delim_val)
    while len(linemain) == 5:
        if rx[0] == '' or int(linemain[0]) < int(rx[0]):
            outfile.write(missingRow(delim_val.join(linemain)))
            linemain = infile.readline().rstrip().split(delim_val, 4)
            cnt.add()
        elif int(linemain[0]) > int(rx[0]):
            (res, rx) = calcDSIH(rx, dsih_percent, vals, rxfile, delim_val, skip=True)
        else:
            matched_id = int(rx[0])
            (res, rx) = calcDSIH(rx, dsih_percent, vals, rxfile, delim_val)
            if res is not None:
                dates = [res[i][0] for i in range(len(res))]
            while int(linemain[0]) == matched_id:
                # ensure date is in both files
                mdate = int(linemain[2])
                if res is not None and mdate in dates:
                    (dropdate, droppre, dropsupply) = calcDropout(mdate, res, dates.index(mdate), adherence_gap)
                    out = "%s%s%s" % (dropdate, delim_val, dropsupply)
                    outfile.write(delim_val.join(linemain) + delim_val + out + "\n")
                else:
                    outfile.write(missingRow(delim_val.join(linemain)))
                linemain = infile.readline().rstrip().split(delim_val, 4)
                if len(linemain) != 5:
                    break
                cnt.add()
    infile.close()
    rxfile.close()
    outfile.close()
