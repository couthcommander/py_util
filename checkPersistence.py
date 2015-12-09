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

class dsihFile(file):
    def __init__(self, name, percent):
        file.__init__(self, name)
        header = self.readline().rstrip().split(',')
        cols = ['scrssn', 'svc_dteoffset', 'DSIHpre'+str(percent), 'DSIHpost'+str(percent)]
        if False in [i in header for i in cols]:
            print "DSIH file [%s] is not valid" % (name)
            sys.exit()
        self.colOrder = [header.index(i) for i in cols]

    def read(self):
        line = self.readline().rstrip().split(',')
        if len(line) > 1:
            return [int(line[i]) for i in self.colOrder]
        else:
            return []

# measure compliance
def calcDropout(start, dates, gap):
    alldates = dates.keys()
    if start not in alldates:
        return '.'
    alldates.sort()
    lastdate = start
    for i in range(alldates.index(start)+1, len(dates)):
        if int(dates[alldates[i]][0]) + gap >= 0:
            lastdate = alldates[i]
        else:
            break
    #the post pill quantity for current prescription
    pills = dates[lastdate][1]
    # dropout date is last prescription date PLUS the DSIHpost on that day
    # dropout = lastdate + pills
    return [lastdate, pills]

def readMain(line):
    return [int(line[0]), int(line[2])]

def missingRow(line):
    return line + delim_val + missing_val + delim_val + missing_val + "\n"

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile", help='delimited file, should contain PTID|DATE|OFFSET|DRUGNAME|ETC')
    parser.add_argument("DSIHfile", help='DSIH file, should contain PTID|DATE|OFFSET|PRE|POST')
    parser.add_argument("outputfile", help='output file, checking adherence')
    parser.add_argument("drugname", help='drug to find')
    parser.add_argument("-d", "--dsih", help='stockpiling percentage, 0-101%%', default=101, type=int)
    parser.add_argument("-g", "--gap", help='gap size, defaults to 14', default=14, type=int)
    parser.add_argument("--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--count", help='turn counter on', action='store_false')
    args = parser.parse_args()
    missing_val = ''
    delim_val = args.delimiter
    drug = args.drugname
    adherence_gap = args.gap
    dsih_percent = args.dsih
    if dsih_percent < 0 or dsih_percent > 101:
        print "DSIH% must be between 0 and 101"
        sys.exit()
    mainfile = open(args.datafile)
    dsihfile = dsihFile(args.DSIHfile, dsih_percent)
    outfile = open(args.outputfile, 'w')
    if args.count:
        cnt = Counter()
    else:
        cnt = Nothing()

    header = mainfile.readline().rstrip()
    # date of last refill
    fieldname1 = "%s_stop_%s_%s_Offset" % (drug, adherence_gap, dsih_percent)
    # daysupply of last refill
    fieldname2 = "%s_stop_%s_%s_Supply" % (drug, adherence_gap, dsih_percent)
    outfile.write(header + delim_val + fieldname1 + delim_val + fieldname2 + "\n")
    linemain = mainfile.readline().rstrip().split(delim_val, 4)
    linedsih = dsihfile.read()
    (mid, mdate) = readMain(linemain)
    (did, ddate, pre, post) = linedsih
    dates = {}
    while(len(linemain) == 5 and len(linedsih) == 4):
        if mid < did:
            outfile.write(missingRow(delim_val.join(linemain)))
            linemain = mainfile.readline().rstrip().split(delim_val, 4)
            if(len(linemain) == 5):
                (mid, mdate) = readMain(linemain)
            cnt.add()
        elif mid > did:
            while(mid > did):
                linedsih = dsihfile.read()
                if(len(linedsih) != 4):
                    break
            (did, ddate, pre, post) = linedsih
        else:
            matched_id = did
            while(mid == did and len(linedsih) == 4):
                dates[ddate]=[pre, post]
                linedsih = dsihfile.read()
                if(len(linedsih) == 4):
                    (did, ddate, pre, post) = linedsih
            #mid < did unless end of DSIH file was reached -- mid == matched_id AT LEAST the first time
            while(mid == matched_id):
                if len(dates) > 0 and mdate in dates.keys():
                    (dropdate, dropsupply) = calcDropout(mdate, dates, adherence_gap)
                    res = "%s%s%s" % (dropdate, delim_val, dropsupply)
                    outfile.write(delim_val.join(linemain) + delim_val + res + "\n")
                else:
                    outfile.write(missingRow(delim_val.join(linemain)))
                linemain = mainfile.readline().rstrip().split(delim_val, 4)
                if(len(linemain) == 5):
                    (mid, mdate) = readMain(linemain)
                else:
                    break
                cnt.add()
            dates.clear()
    #need to print blank lines for anything left in main file
    while len(linemain) == 5:
        outfile.write(missingRow(delim_val.join(linemain)))
        linemain = mainfile.readline().rstrip().split(delim_val, 4)
        cnt.add()
    mainfile.close()
    dsihfile.close()
    outfile.close()
