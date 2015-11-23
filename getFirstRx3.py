#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, getopt
#lower this number if you want to test the output
maxinput=pow(10,20)
#maxinput=100
# missing value character
missing_val=''
# text file delimeter (must be consistent across all input files)
delim_val=","

class Counter():
  def __init__(self):
    self.count=0

  def add(self):
    self.count+=1
    if not self.count%100000:
      print self.count
    if self.count > maxinput:
      sys.exit()

#find the first value in dlist >= to init
def calcFirstDate(init, dlist):
  dlist.sort()
  if(init > dlist[len(dlist)-1]):
    return missing_val
  itr=0
  while(dlist[itr] < init):
    itr+=1
  return itr

##############################
# datafile - main cohort data
# rxfile - list of prescriptions for [DRUGNAME]
# outputfile - adds new column [DRUGNAME_FIRST] to datafile
####### expects format [ptvid][date][dateoffset][etc]
####### also expects data to be sorted by ptvid and date
# version 3:
# changed calcFirstDate to return the index instead of date
# that way both date and dateoffset are known
# rxfile isn't guaranteed 4 columns, so only ensure 3 [id,date,dateoffset]
##############################

def usage():
  print "usage: " + sys.argv[0] + " [-h] datafile rxfile outputfile drugname"

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
  if len(args) != 4:
    usage()
    sys.exit(1)
  (mfile, dfile, ofile, drug)=args
  mainfile=open(mfile)
  rxfile=open(dfile)
  outfile=open(ofile,'w')
  header=mainfile.readline().rstrip()
  linemain=mainfile.readline().rstrip().split(delim_val, 3)
  junk=rxfile.readline().rstrip()
  linerx=rxfile.readline().rstrip().split(delim_val, 3)
  outfile.write(header+delim_val+drug+'FirstOffset'+delim_val+drug+'First'+"\n")
  count=Counter()
  dates=[]
  realdates=[]
  if len(linemain) != 4 or len(linerx) < 3:
    print "you don't have any data!"
    sys.exit()
  (pid, date, dateoffset, stuff)=linemain
  (ptvid, filldate, filldateoffset)=linerx[0:3]
  while(len(linemain) == 4 and len(linerx) >= 3):
    if(int(pid) < int(ptvid)):
      outfile.write(delim_val.join(linemain)+delim_val+missing_val+delim_val+missing_val+"\n")
      linemain=mainfile.readline().rstrip().split(delim_val, 3)
      if(len(linemain) == 4):
        (pid, date, dateoffset, stuff)=linemain
      count.add()
    elif(int(pid) > int(ptvid)):
      while(int(pid) > int(ptvid)):
        linerx=rxfile.readline().rstrip().split(delim_val, 3)
        if(len(linerx) >= 3):
          (ptvid, filldate, filldateoffset)=linerx[0:3]
        else:
          break
    else:
      currentid=ptvid
      while(int(pid) == int(ptvid)):
        dates.append(int(filldateoffset))
        realdates.append(filldate)
        linerx=rxfile.readline().rstrip().split(delim_val, 3)
        if(len(linerx) >= 3):
          (ptvid, filldate, filldateoffset)=linerx[0:3]
        else:
          break
      while(int(pid) == int(currentid)):
        first_index=calcFirstDate(int(dateoffset), dates)
        if first_index == missing_val:
          firstdate = missing_val
          firstdateoffset = missing_val
        else:
          firstdate = str(realdates[first_index])
          firstdateoffset = str(dates[first_index])
        outfile.write(delim_val.join(linemain)+delim_val+firstdateoffset+delim_val+firstdate+"\n")
        linemain=mainfile.readline().rstrip().split(delim_val, 3)
        if(len(linemain) == 4):
          (pid, date, dateoffset, stuff)=linemain
        else:
          break
        count.add()
      dates=[]
      realdates=[]
  #need to print blank lines for anything left in main file
  while(len(linemain) == 4):
    outfile.write(delim_val.join(linemain)+delim_val+missing_val+delim_val+missing_val+"\n")
    linemain=mainfile.readline().rstrip().split(delim_val, 3)
    count.add()
  mainfile.close()
  rxfile.close()
  outfile.close()
