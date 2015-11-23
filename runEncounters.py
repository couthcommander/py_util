#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

# all files should have same line counts, how should we combine?

def usage():
    print "usage: " + sys.argv[0] + " basefile newfile outfile nvars"

if __name__=='__main__':
    args = sys.argv[1:]
    if len(args) != 4:
        usage()
        sys.exit(1)
    (bfile, nfile, ofile, nvars) = args
    basefile = open(bfile)
    newfile = open(nfile)
    outfile = open(ofile,'w')
    nvars = int(nvars)*-1
    junk = newfile.readline().rstrip()
    line = junk.split(',')
    part = slice(nvars, len(line))
    header = basefile.readline().rstrip()+','+",".join(line[part])
    outfile.write(header+"\n")

    line = basefile.readline().rstrip()
    value = newfile.readline().rstrip()
    while len(line) > 1 and len(value) > 1:
        output = line+','+",".join(value.split(',')[part])
        outfile.write(output+"\n")
        line = basefile.readline().rstrip()
        value = newfile.readline().rstrip()
