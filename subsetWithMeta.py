import sys
import argparse
import re
import os.path

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

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile", help='delimited file with data to subset')
    parser.add_argument("metafile", help='delimited file with format NAME,FLAG1,FLAG2')
    parser.add_argument("matchcolumn", help='subset datafile by matching on this column')
    parser.add_argument("types", metavar='metatype', nargs='+', help='determine names to lookup by identifying types in metafile')
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("--nocount", help='turn counter off', action='store_true')
    args = parser.parse_args()
    delim_val = args.delimiter
    prfile = open(args.datafile)
    mtfile = open(args.metafile)
    types = args.types

    req_col = [args.matchcolumn]
    header = prfile.readline().rstrip().split(delim_val)
    if sum([i in header for i in req_col]) != len(req_col):
        print "some required columns are missing %s" % (req_col)
        sys.exit(1)
    col_loc = [header.index(i) for i in req_col]

    mheader = mtfile.readline().rstrip().split(delim_val)
    type_col = [None for i in types]
    for ix, val in enumerate(types):
        # match name by looking at end of string
        pat = re.compile("%s$" % (val), re.I)
        matches = [pat.search(i) is not None for i in mheader]
        if True not in matches:
            print "requested NAME not found: %s" % (val)
            sys.exit(2)
        type_col[ix] = matches.index(True)
    name_list = [[] for i in types]
    unique_names = set()
    for line in mtfile:
        linem = line.rstrip().split(delim_val)
        # name should be in first column
        name = linem[0].replace('"', '')
        for ix, val in enumerate(type_col):
            if linem[val] == '1':
                name_list[ix].append(name)
                unique_names.add(name)
    mtfile.close()

    # create array of file handles
    ofiles = []
    for ix, val in enumerate(type_col):
        (b, e) = os.path.splitext(os.path.basename(args.datafile))
        fname = "%s_%s.csv" % (b, mheader[val].replace('"', ''))
        ofiles.append(open(fname, 'w'))
        ofiles[ix].write(delim_val.join(header) + "\n")

    if args.nocount:
        cnt = Nothing()
    else:
        cnt = Counter()

    for line in prfile:
        dat = line.rstrip().split(delim_val)
        drugname = dat[col_loc[0]]
        if drugname in unique_names:
            for ix, names in enumerate(name_list):
                if drugname in names:
                    ofiles[ix].write(line)
        cnt.add()

    # close all files
    prfile.close()
    for fh in ofiles:
        fh.close()
