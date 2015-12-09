#!/usr/bin/python
import argparse, sys

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

#################################################
# version 4
# assume ordered by ptvid
# don't read entire file at once
# refactored, now using argparse
# data subset by drug
# no dosechange variable
#
# version 2
# started to use new output format of getdose7
# output two new vars, pre101 and post101
#
# version 1
# calculate DSIH post/pre-fills (for alpha 0 to 100)
# missedI is no longer calculated
#################################################

def mysort(a,b):
    return cmp(int(a[2]),int(b[2]))

def calcData(dat, dscol, delim):
    # sort by fill date
    dat.sort(mysort)
    prevpost = [0 for i in range(101)]
    prevday = 0
    n = len(prevpost)
    output = ''
    for obs in dat:
        date = int(obs[2])
        daysupply = int(obs[dscol])
        pre = [0 for i in range(n)]
        post = [0 for i in range(n)]
        dayspassed = date - prevday
        for i in range(n):
            # want negative values returned
            if prevday and dayspassed > 0:
                pre[i] = prevpost[i] - dayspassed
            post[i] = daysupply
            if pre[i] > 0:
                post[i] += int(round(pre[i]*i/100.0))
        prevpost = post
        prevday = date
        vals = ["%s%s%s" % (i,delim,j) for i,j in zip(pre, post)]
        output += delim.join(obs + vals) + "\n"
    return output

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile", help='delimited file, should contain PTID|DATE|OFFSET|DAYSUPPLY')
    parser.add_argument("outputfile", help='created file with DSIH with stockpiling 0-100%%')
    parser.add_argument("dscolumn", help='column name with day supply')
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--count", help='turn counter on', action='store_false')
    args = parser.parse_args()
    delim_val = args.delimiter
    myfile = open(args.inputfile)
    outfile = open(args.outputfile, 'w')
    if args.count:
        cnt = Counter()
    else:
        cnt = Nothing()

    colhead = delim_val.join(["DSIHpre%s%sDSIHpost%s" % (i, delim_val, i) for i in range(101)])
    header = myfile.readline().rstrip().split(delim_val)
    if args.dscolumn not in header:
        print "daysupply column [%s] not found" % (args.dscolumn)
        sys.exit(-1)
    dcol = header.index(args.dscolumn)
    outfile.write(delim_val.join(header)+delim_val+colhead+'\n')
    prevpat = False
    data = []
    line = myfile.readline().rstrip().split(delim_val)
    while len(line) > 1:
        pat = int(line[0])
        if pat != prevpat:
            if len(data):
                res = calcData(data, dcol, delim_val)
                outfile.write(res)
            data = [line]
            prevpat = pat
        else:
            data.append(line)
        line = myfile.readline().rstrip().split(delim_val)
        cnt.add()
    if len(data):
        res = calcData(data, dcol, delim_val)
        outfile.write(res)
    outfile.close()
    myfile.close()
