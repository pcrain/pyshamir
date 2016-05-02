#!/usr/bin/python
from pyshamir import *

IDS = [1,2,3,4,5]

def protocol():
  #Clear old files
  cleanup()
  #Constant
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

  #Main Generate
  print(col.WHT+"Generating random numbers p,q"+col.BLN)
  p,q = [random.randrange(SMAX) for i in range(0,2)] #Generate two numbers to multiply
  print(col.YLW + "Computing " + str(p) + "*" + str(q) + col.BLN)
  print(col.WHT+"Generating polynomials p,q"+col.BLN)
  pp = polygen(p,t)
  qq = polygen(q,t)
  print(col.WHT+"Distributing polynomials p,q"+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+"p-share",str(evalpolyat(pp,pa.id) % PRIME)) for pa in ps]
  [easyWrite("_cloud/"+str(pa.id)+"q-share",str(evalpolyat(qq,pa.id) % PRIME)) for pa in ps]

  print(col.WHT+"Awaiting shares of v from all parties"+col.BLN)
  v = [pa.loadVShare("p","q"      ) for pa in ps]     #Aggregate the v matrix (must be done in order)
  print(col.WHT+"Distributing v"+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+"pq-v",str(v)) for pa in ps]

  #Main Finish
  print(col.WHT+"Awaiting shares of s from all parties"+col.BLN)
  s = [pa.loadSShare("p","q"      ) for pa in ps]     #Aggregate the shares of the new product
  print(col.YLW+"DONE"+col.BLN)
  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(p*q) + col.BLN)
  print(col.MGN + str(IDS) + col.GRN + "\n  " + str(int(nint(lagrange(s)(0)))%PRIME) + col.BLN)

if __name__ == "__main__":
  protocol()
