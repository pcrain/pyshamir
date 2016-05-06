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
  me.computeVShare(s1,s2)    #Compute shares of the v matrix
  print(col.WHT+"Writing shares of v[" + sid + "] to file"+col.BLN)
  easyWrite("_cloud/"+sid+s1+s2+"-vshares",str(me.vshares[s1+"*"+s2]))
  print(col.WHT+"Awaiting v from distributor"+col.BLN)
  return me.loadV(s1,s2)

def sGenProtocol(me,s1,s2,v,t,IDS):
  sid = str(me.id)
  print(col.WHT+"Computing A matrix"+col.BLN)
  A = genMatrixA(t,IDS)
  print(col.WHT+"Computing share " + sid + " of "+s1+"*"+s2+col.BLN)
  me.computeSShare(s1,s2,v,A[me.relid,:]) #Compute the shares of the new product
  return

def reductionProtocol(me,s1,s2,t,ps,IDS):
  rGenProtocol(me,s1,s2,t,ps)       #Load shares
  v = vGenProtocol(me,s1,s2,ps)     #Generate v matrix
  sGenProtocol(me,s1,s2,v,t,IDS)    #Generate new shares

# def protocol(id,nparties):
#   print(str(id))

#   #Init parties
#   IDS = [i for i in range(1,nparties+1)]
#   t = int((nparties-1)/2)
#   ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

#   me = ps[id]                          #Generate a new Party with input id
#   me.loadSecretShare("p")              #Load share for p
#   me.loadSecretShare("q")              #Load share for q
#   me.writeSummedShare("p","q","s")     #Write share for s=p+q
#   reductionProtocol(me,"p","q",t,ps,IDS) #Generate share for m=p*q
#   me.writeMultipliedShare("p","q","m") #Write new shares to file

def sumProtocol(s1,s2,s3,id,nparties):
  print(str(id))
  #Init parties
  IDS = [i for i in range(1,nparties+1)]
  t = int((nparties-1)/2)
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

  me = ps[id]                          #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSummedShare(s1,s2,s3)     #Write share for s=p+q

def productProtocol(s1,s2,s3,id,nparties):
  print(str(id))
  #Init parties
  IDS = [i for i in range(1,nparties+1)]
  t = int((nparties-1)/2)
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids

  me = ps[id]                          #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  reductionProtocol(me,s1,s2,t,ps,IDS) #Generate share for m=p*q
  me.writeMultipliedShare(s1,s2,s3) #Write new shares to file

if __name__ == "__main__":
  if len(sys.argv) < 3: sys.exit(-1)
  sumProtocol("p","q","s",int(sys.argv[1]),int(sys.argv[2]))
  productProtocol("p","q","m",int(sys.argv[1]),int(sys.argv[2]))
