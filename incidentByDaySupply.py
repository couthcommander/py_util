#!/usr/bin/python
import sys, getopt
#lower this number if you want to test the output
maxinput = pow(10, 20)
# missing value character
missing_val='-9'
# text file delimeter (must be consistent across all input files)
delim_val=","

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%10000:
            print "\r" + str(self.count),
        if self.count > maxinput:
            sys.exit()

##############################
# infile - prescription data
# datefile - list of key-value pairs for dates
##############################

def usage():
    print "usage: " + sys.argv[0] + " [-h] infile datefile outfile"

if __name__=='__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) != 3:
        usage()
        sys.exit(1)
    (inf, dat, out) = args

    infile = open(inf)
    req_col = ['scrssn','svc_dte','svc_dteoffset','drugdesc','day_supply']
    header = infile.readline().rstrip().split(delim_val)
    if sum([i in header for i in req_col]) != len(req_col):
        print "some required columns are missing %s" % (req_col)
        sys.exit(2)
    col_loc = [header.index(i) for i in req_col]
    header = [header[i] for i in col_loc]

    dates = open(dat)
    dateinfo = {}
    for line in dates:
        (date,ix) = line.rstrip().split(delim_val)
        dateinfo[int(ix)] = date
    dates.close()

    outfile = open(out, 'w')
    outfile.write(delim_val.join(header) + "\n")

    cnt = Counter()
    for line in infile:
        dat = line.rstrip().split(delim_val)
        out = [dat[i] for i in col_loc]
        outfile.write(delim_val.join(out) + "\n")
        # what is missing day_supply?
        if out[4] == '':
          out[4] = '0'
        do = int(out[2])
        ds = int(out[4])
        if ds > 0:
          dix = do+ds
          outfile.write(delim_val.join([out[0],dateinfo[dix],str(dix),out[3],missing_val]) + "\n")
        if ds > 180:
          dix = do+180
          outfile.write(delim_val.join([out[0],dateinfo[dix],str(dix),out[3],missing_val]) + "\n")
        if ds > 360:
          dix = do+360
          outfile.write(delim_val.join([out[0],dateinfo[dix],str(dix),out[3],missing_val]) + "\n")
        if ds > 540:
          dix = do+540
          outfile.write(delim_val.join([out[0],dateinfo[dix],str(dix),out[3],missing_val]) + "\n")
        if ds > 720:
          dix = do+720
          outfile.write(delim_val.join([out[0],dateinfo[dix],str(dix),out[3],missing_val]) + "\n")
        cnt.add()

    # close all files
    infile.close()
    outfile.close()
