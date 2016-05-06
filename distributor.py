#!/usr/bin/python
from pyshamir import *

def distributeNumber(name,value,pids):
  t=int((len(pids)-1)/2)
  print(col.WHT+"Generating polynomials for "+name+col.BLN)
  pp = polygen(value,t)
  print(col.WHT+"Distributing polynomial for "+name+col.BLN)
  for x in range(0,len(pids)):
    p = Party(pids[x],x)
    easyWrite(CLOUD+str(p.id)+"/"+str(p.id)+name+"-share",str(evalpolyat(pp,p.id) % PRIME))

def awaitAndComputeV(s1,s2,pids):
  print(col.WHT+"Awaiting shares of ("+s1+"*"+s2+")'s v from all parties"+col.BLN)
  v = [Party(pids[x],x).loadVShare(s1,s2) for x in range(0,len(pids))]     #Aggregate the v matrix (must be done in order)
  print(col.WHT+"Distributing v"+col.BLN)
  for x in range(0,len(pids)):
    p = Party(pids[x],x)
    easyWrite(CLOUD+str(p.id)+"/"+str(p.id)+s1+s2+"-v",str(v))

def awaitAndComputeShares(s,pids):
  print(col.WHT+"Awaiting shares of "+s+" from all parties"+col.BLN)
  ss = [Party(pids[x],x).loadSecretShare(s) for x in range(0,len(pids))]     #Aggregate the shares of the new product
  return int(nint(lagrange(ss)(0)))%PRIME

def sumProtocol(s3,nparties,ps):
  s = awaitAndComputeShares(s3,ps)
  print(col.MGN + str([p for p in ps])   + col.GRN + "\n  " + str(s) + col.BLN)

def productProtocol(s1,s2,s3,nparties,ps):
  awaitAndComputeV(s1,s2,ps)
  m = awaitAndComputeShares(s3,ps)
  print(col.MGN + str([p for p in ps])   + col.GRN + "\n  " + str(m) + col.BLN)

def main():
  if len(sys.argv) < 2:            sys.exit(-1)
  if not os.path.exists(CLOUD): os.makedirs(CLOUD)
  nparties = int(sys.argv[1])
  cleanup()                        #Clear old files

  pids = [i*i for i in range(1,nparties+1)]
  for i in pids:
    fpath = CLOUD+str(i)
    if not os.path.exists(fpath): os.makedirs(fpath)

  p = 42; q = 64
  distributeNumber("p",p,pids)
  distributeNumber("q",q,pids)

  sumProtocol("s",nparties,pids)
  print(col.MGN + "Real Sum: " + col.GRN + "\n  " + str(p+q) + col.BLN)
  productProtocol("p","q","m",nparties,pids)
  print(col.MGN + "Real Product: " + col.GRN + "\n  " + str(p*q) + col.BLN)
  sumProtocol("s2",nparties,pids)
  print(col.MGN + "Real Sum: " + col.GRN + "\n  " + str(p+q+p+q) + col.BLN)

if __name__ == "__main__":
  main()
