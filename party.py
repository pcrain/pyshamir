#!/usr/bin/python
from pyshamir import *


def protocol(id,total):
  IDS = [i for i in range(1,total+1)]
  sid = str(id)
  t = int((total-1)/2)
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids
  print(id)
  pa = Party(IDS[id],id)  #Generate new parties with the specified ids

  print(col.WHT+"Loading share " + sid + " of p"+col.BLN)
  pa.loadSecretShare("p")
  print(col.WHT+"Loading share " + sid + " of q"+col.BLN)
  pa.loadSecretShare("q")
  print(col.WHT+"Computing random polynomial r[" + sid + "]"+col.BLN)
  pa.genRandomP   ("p","q",t    ) #Generate a random polynomial r for each party
  print(col.WHT+"Writing shares of r[" + sid + "] to file"+col.BLN)
  pa.writeRanShares("p","q",ps   )    #Distribute the jth share of p_i's r to party j
  print(col.WHT+"Loading other parties' shares of r[j]"+col.BLN)
  pa.loadRanShares("p","q",ps   )    #Distribute the jth share of p_i's r to party j

  print(col.WHT+"Computing share " + sid + " of v"+col.BLN)
  pa.computeVShare("p","q"      )    #Compute shares of the v matrix
  print(col.WHT+"Writing shares of v[" + sid + "] to file"+col.BLN)
  easyWrite("_cloud/"+str(pa.id)+"pq-vshares",str(pa.vshares["p*q"]))

  print(col.WHT+"Awaiting v from distributor"+col.BLN)
  v = pa.loadV("p","q")
  print(col.WHT+"Computing A matrix"+col.BLN)
  A = genMatrixA(t,IDS)
  print(col.WHT+"Computing share " + sid + " of s"+col.BLN)
  pa.computeSShare("p","q",v,A[pa.relid,:]) #Compute the shares of the new product
  print(col.WHT+"Writing share s[" + sid + "] to file"+col.BLN)
  easyWrite("_cloud/"+str(pa.id)+"pq-sshare",str(pa.sshares["p*q"]))
  print(col.YLW+"DONE"+col.BLN)

if __name__ == "__main__":
  argv = sys.argv
  argc = len(argv)
  if argc < 3:
    sys.exit(-1)
  protocol(int(argv[1]),int(argv[2]))
