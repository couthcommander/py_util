import sys, argparse
#lower this number if you want to test the output
maxinput=pow(10,15)

# merge all files, assumes same number of rows

# python mergeByLast.py output.csv file1.csv file2.csv ... -N 2
# possible extensions that would be slower
# update a particular column
# merge from a particular column (non-last)

class Counter():
    def __init__(self):
        self.count=0

    def add(self):
        self.count+=1
        if not self.count%10000:
            print "\r" + str(self.count),
        if self.count > maxinput:
            sys.exit()

def splitData(string, nvars):
    line = string.rstrip().split(',')
    part = slice(nvars, len(line))
    return ','.join(line[part])

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("outputfile")
    parser.add_argument("infiles", nargs="+")
    parser.add_argument("-N", "--cols", help="number of columns to merge (from the end)", type=int, default=1)
    args = parser.parse_args()
    if len(args.infiles) < 2:
        print "***\nAt least two files to merge should be specified\n***\n"
        parser.print_help()
        sys.exit(1)
    nvars = args.cols * -1
    ofile = args.outputfile
    file1 = args.infiles[0]
    fileN = args.infiles[1:]
    outfile = open(ofile,'w')
    infile = open(file1)
    ifiles = [open(i) for i in fileN]
    cnt = Counter()
    buffsize = 1000
    while True:
        if not cnt.count % buffsize:
            if cnt.count > 0:
                outfile.write("\n".join(linebuff)+"\n")
            linebuff = ["" for i in range(buffsize)]
        line = infile.readline().rstrip()
        if(len(line) == 0):
            linebuff = linebuff[:(cnt.count % buffsize)]
            if len(linebuff):
                outfile.write("\n".join(linebuff)+"\n")
            break
        for i in ifiles:
            line = "%s,%s" % (line, splitData(i.readline(), nvars))
        linebuff[cnt.count % buffsize] = line
        cnt.add()
    [i.close() for i in ifiles]
    infile.close()
    outfile.close()
