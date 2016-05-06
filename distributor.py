#!/usr/bin/python
from pyshamir import *

def distributeNumber(name,value,parties,t):
  #Main Generate
  print(col.WHT+"Generating polynomials for "+name+col.BLN)
  pp = polygen(value,t)
  print(col.WHT+"Distributing polynomial for "+name+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+name+"-share",str(evalpolyat(pp,pa.id) % PRIME)) for pa in parties]

def awaitAndComputeV(s1,s2,parties):
  print(col.WHT+"Awaiting shares of v from all parties"+col.BLN)
  v = [pa.loadVShare(s1,s2) for pa in parties]     #Aggregate the v matrix (must be done in order)
  print(col.WHT+"Distributing v"+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+s1+s2+"-v",str(v)) for pa in parties]

def awaitAndComputeProduct(s,parties):
  print(col.WHT+"Awaiting shares of s from all parties"+col.BLN)
  ss = [pa.loadSecretShare(s) for pa in parties]     #Aggregate the shares of the new product
  # print(col.BLU+str(ss)+col.BLN)
  return int(nint(lagrange(ss)(0)))%PRIME

def protocol(total):
  #Constant
  IDS = [i for i in range(1,total+1)]
  t = int((total-1)/2)
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

  #Distribute phase
  p = random.randrange(SMAX); distributeNumber("p",p,ps,t)
  q = random.randrange(SMAX); distributeNumber("q",q,ps,t)

  #V compute phase
  awaitAndComputeV("p","q",ps)

  #Final compute phase
  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(p*q) + col.BLN)
  print(col.MGN + str(IDS)   + col.GRN + "\n  " + str(awaitAndComputeProduct("s",ps)) + col.BLN)

if __name__ == "__main__":
  if len(sys.argv) < 2:            sys.exit(-1)
  if not os.path.exists("_cloud"): os.makedirs("_cloud")
  cleanup()                        #Clear old files
  protocol(int(sys.argv[1]))
