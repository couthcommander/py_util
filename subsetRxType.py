#!/usr/bin/python
import sys, getopt, re
#lower this number if you want to test the output
maxinput = pow(10, 20)
# missing value character
missing_val='.'
# text file delimeter (must be consistent across all input files)
delim_val=","

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%1000000:
            print(str(self.count))
        if self.count > maxinput:
            sys.exit()

##############################
# datafile - prescription data
# rxfile - list of prescriptions with rxtype indicators
# drugname - list of drugdesc to subset
##############################

def usage():
    print("usage: " + sys.argv[0] + " [-h] datafile rxfile drugname [drugname2] [...]")

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
    if len(args) < 3:
        usage()
        sys.exit(1)
    (presc, rxcode) = args[0:2]
    types = args[2:]

    prfile = open(presc)
    req_col = ['scrssn','svc_dte','svc_dteoffset','drugdesc','day_supply']
    header = prfile.readline().rstrip().split(delim_val)
    if sum([i in header for i in req_col]) != len(req_col):
        print("some required columns are missing %s" % (req_col))
        sys.exit(2)
    col_loc = [header.index(i) for i in req_col]
    header = [header[i] for i in col_loc]+['rxType']

    # create list of drug names for each requested rxtype
    rxfile = open(rxcode)
    rxheader = rxfile.readline().rstrip().split(delim_val)
    if 'drugdesc' not in rxheader:
        print("drugdesc not found in rxfile")
        sys.exit(3)
    nameix = rxheader.index('drugdesc')
    type_col = [None for i in types]
    for ix, val in enumerate(types):
        pat = re.compile("^rxtype[_]*%s$" % (val), re.I)
        matches = [pat.search(i) is not None for i in rxheader]
        if True not in matches:
            print("requested rxtype not found: %s" % (val))
            sys.exit(4)
        type_col[ix] = matches.index(True)
    name_list = [[] for i in types]
    unique_names = set()
    for line in rxfile:
        linerx = line.rstrip().split(delim_val)
        name = linerx[nameix]
        for ix, val in enumerate(type_col):
            if linerx[val] == '1':
                name_list[ix].append(name)
                unique_names.add(name)
    rxfile.close()

    # create array of file handles
    ofiles = []
    for ix, val in enumerate(type_col):
        rxname = rxheader[val]
        ofiles.append(open('pharm_'+rxname+'.csv', 'w'))
        ofiles[ix].write(delim_val.join(header) + "\n")

    cnt = Counter()
    for line in prfile:
        dat = line.rstrip().split(delim_val)
        drugname = dat[col_loc[3]]
        if drugname in unique_names:
            for ix, names in enumerate(name_list):
                # is prescription in drug list for rxtype
                if drugname in names:
                    rxname = rxheader[type_col[ix]]
                    out = [dat[i] for i in col_loc]+[rxname]
                    ofiles[ix].write(delim_val.join(out) + "\n")
        cnt.add()

    # close all files
    prfile.close()
    for fh in ofiles:
        fh.close()
