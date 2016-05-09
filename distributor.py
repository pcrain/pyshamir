#!/usr/bin/python
#Mockup of distributor for secure computation
from pyshamir import *

#Distribute shares of a number to a list of parties
#  name  = a name for the share to be distributed
#  value = the value to be distributed
#  pids = list of ids of other parties to distribute to / receive from
def distributeNumber(name,value,pids):
  t=int((len(pids)-1)/2)
  print(col.WHT+"Generating polynomials for "+name+col.BLN)
  pp = polygen(value,t)
  print(col.WHT+"Distributing polynomial for "+name+col.BLN)
  for x in range(0,len(pids)):
    p = Party(pids[x],x)
    easyWrite(CLOUD+str(p.id)+"/"+str(p.id)+"-"+name+"-share",str(evalpolyat(pp,p.id) % PRIME))

#Await parties in pids to compute their shares of the v vector, combine them, and distribute the result
#  s1   = name of first share the v-shares are based off of
#  s2   = name of second share the v-shares are based off of
#  pids = list of ids of other parties to distribute to / receive from
def awaitAndComputeV(s1,s2,pids):
  print(col.WHT+"Awaiting shares of ("+s1+"*"+s2+")'s v from all parties"+col.BLN)
  v = [Party(pids[x],x).loadVShare(s1,s2) for x in range(0,len(pids))]     #Aggregate the v matrix (must be done in order)
  print(col.WHT+"Distributing v"+col.BLN)
  for x in range(0,len(pids)):
    p = Party(pids[x],x)
    easyWrite(CLOUD+str(p.id)+"/"+str(p.id)+"-"+s1+"-"+s2+"-v",str(v))

#Compute the original value of a number from shares of its polynomial
#  s   = name of the share to compute
#  pids = list of ids of other parties with shares to compute from
def awaitAndComputeShares(s,pids):
  print(col.WHT+"Awaiting shares of "+s+" from all parties"+col.BLN)
  ss = [Party(pids[x],x).loadSecretShare(s) for x in range(0,len(pids))]     #Aggregate the shares of the new product
  return int(nint(lagrange(ss)(0)))%PRIME

def computeFromShares(s,pids,printit=False):
  ss = [Party(pids[x],x).loadSecretShare(s) for x in range(0,len(pids))]     #Aggregate the shares of the new product
  x = int(nint(lagrange(ss)(0)))%PRIME
  [easyWrite(CLOUD+str(pa)+"/"+str(pa)+"-"+s+"-computed",str(x)) for pa in pids]
  if printit:
    print(col.YLW+s+" = "+str(x)+col.BLN)

#Wait for parties to sum their shares and compute their shares of s3=(s1+s2),
#then aggregate and print the result
#  s3   = name of share to compute and print
#  pids = list of ids of other parties with shares to compute from
def addProtocol(s3,pids):
  s = awaitAndComputeShares(s3,pids)
  print(col.MGN + str([p for p in pids])   + col.GRN + "\n  " + str(s) + col.BLN)

#Wait for parties to compute their v-shares for (s1*s2), distribute v,
#wait for the parties to compute and compute their shares of s3=(s1*s2),
#then aggregate and print the result
#  s1   = name of first share the v-shares are based off of
#  s2   = name of second share the v-shares are based off of
#  s3   = name of share to compute and print
#  pids = list of ids of other parties with shares to compute from
def mulProtocol(s1,s2,s3,pids):
  awaitAndComputeV(s1,s2,pids)
  m = awaitAndComputeShares(s3,pids)
  print(col.MGN + str([p for p in pids])   + col.GRN + "\n  " + str(m) + col.BLN)

def main():
  if not os.path.exists(CLOUD): os.makedirs(CLOUD)
  cleanup()                        #Clear old files

  pids = jload("parties.json")
  for i in pids:
    fpath = CLOUD+str(i)
    if not os.path.exists(fpath): os.makedirs(fpath)

  secrets=jload("secrets.json")
  for s in secrets.keys():
    distributeNumber(s,secrets[s],pids)

  computations=jload("comps.json")
  for c in computations:
    if len(c) == 1:
      computeFromShares(c[0],pids)
      continue
    if type(c[2]) != int:
      if c[1] == "+" or c[1] == "-":
        addProtocol(c[3],pids)
      elif c[1] == "*" or c[1] == "/":
        mulProtocol(c[0],c[2],c[3],pids)

if __name__ == "__main__":
  main()
