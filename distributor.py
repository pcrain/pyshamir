#!/usr/bin/python
from pyshamir import *

def distributeNumber(name,value,parties):
  t=int((len(ps)-1)/2)
  #Main Generate
  print(col.WHT+"Generating polynomials for "+name+col.BLN)
  pp = polygen(value,t)
  print(col.WHT+"Distributing polynomial for "+name+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+name+"-share",str(evalpolyat(pp,pa.id) % PRIME)) for pa in parties]

def awaitAndComputeV(s1,s2,parties):
  print(col.WHT+"Awaiting shares of ("+s1+"*"+s2+")'s v from all parties"+col.BLN)
  v = [pa.loadVShare(s1,s2) for pa in parties]     #Aggregate the v matrix (must be done in order)
  print(col.WHT+"Distributing v"+col.BLN)
  [easyWrite("_cloud/"+str(pa.id)+s1+s2+"-v",str(v)) for pa in parties]

def awaitAndComputeShares(s,parties):
  print(col.WHT+"Awaiting shares of "+s+" from all parties"+col.BLN)
  ss = [pa.loadSecretShare(s) for pa in parties]     #Aggregate the shares of the new product
  # print(col.BLU+str(ss)+col.BLN)
  return int(nint(lagrange(ss)(0)))%PRIME

def sumProtocol(s3,nparties,ps):
  #Compute sum
  s = awaitAndComputeShares(s3,ps)
  #Print results
  print(col.MGN + str([p.id for p in ps])   + col.GRN + "\n  " + str(s) + col.BLN)


def productProtocol(s1,s2,s3,nparties,ps):
  #Compute product
  awaitAndComputeV(s1,s2,ps)
  m = awaitAndComputeShares(s3,ps)
  #Print results
  print(col.MGN + str([p.id for p in ps])   + col.GRN + "\n  " + str(m) + col.BLN)

if __name__ == "__main__":
  if len(sys.argv) < 2:            sys.exit(-1)
  if not os.path.exists("_cloud"): os.makedirs("_cloud")
  nparties = int(sys.argv[1])
  cleanup()                        #Clear old files

  #Init parties
  IDS = [i for i in range(1,nparties+1)]
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

  p = 42; q = 64
  distributeNumber("p",p,ps)
  distributeNumber("q",q,ps)

  sumProtocol("s",nparties,ps)
  print(col.MGN + "Real Sum: " + col.GRN + "\n  " + str(p+q) + col.BLN)

  productProtocol("p","q","m",nparties,ps)
  print(col.MGN + "Real Product: " + col.GRN + "\n  " + str(p*q) + col.BLN)

  # sumProtocol("p",42,"q",64,"s",int(sys.argv[1]))
