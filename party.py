#!/usr/bin/python
from pyshamir import *

def rGenProtocol(me,s1,s2,t,parties):
  sid = str(me.id)
  print(col.WHT+"Computing random polynomial r[" + sid + "]"+col.BLN)
  me.genRandomP   (s1,s2,t    ) #Generate a random polynomial r for each party
  print(col.WHT+"Writing shares of r[" + sid + "] to file"+col.BLN)
  me.writeRanShares(s1,s2,parties   )    #Distribute the jth share of p_i's r to party j
  print(col.WHT+"Loading other parties' shares of r[j]"+col.BLN)
  me.loadRanShares(s1,s2,parties   )    #Distribute the jth share of p_i's r to party j

def vGenProtocol(me,s1,s2,parties):
  sid = str(me.id)
  print(col.WHT+"Computing share " + sid + " of v"+col.BLN)
  me.computeVShare("p","q"      )    #Compute shares of the v matrix
  print(col.WHT+"Writing shares of v[" + sid + "] to file"+col.BLN)
  easyWrite("_cloud/"+sid+"pq-vshares",str(me.vshares["p*q"]))
  print(col.WHT+"Awaiting v from distributor"+col.BLN)
  return me.loadV("p","q")

def sGenProtocol(pa,s1,s2,v,t,IDS):
  sid = str(pa.id)
  print(col.WHT+"Computing A matrix"+col.BLN)
  A = genMatrixA(t,IDS)
  print(col.WHT+"Computing share " + sid + " of s"+col.BLN)
  pa.computeSShare("p","q",v,A[pa.relid,:]) #Compute the shares of the new product
  return

  print(col.WHT+"Computing A matrix"+col.BLN)
  A = genMatrixA(t,IDS)
  print(col.WHT+"Computing share " + str(me.id) + " of s"+col.BLN)
  me.computeSShare(s1,s2,v,A[me.relid,:]) #Compute the shares of the new product

def protocol(id,total):
  IDS = [i for i in range(1,total+1)]
  t = int((total-1)/2)
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids
  print(id)
  sid = str(id)
  pa = Party(IDS[id],id)  #Generate new parties with the specified ids

  print(col.WHT+"Loading share " + sid + " of p"+col.BLN)
  pa.loadSecretShare("p")
  print(col.WHT+"Loading share " + sid + " of q"+col.BLN)
  pa.loadSecretShare("q")

  rGenProtocol(pa,"p","q",t,ps)       #Load shares
  v = vGenProtocol(pa,"p","q",ps)     #Generate v matrix
  sGenProtocol(pa,"p","q",v,t,IDS)    #Generate new shares
  pa.writeComputedShare("p","q","s")  #Write new shares to file

if __name__ == "__main__":
  if len(sys.argv) < 3: sys.exit(-1)
  protocol(int(sys.argv[1]),int(sys.argv[2]))
