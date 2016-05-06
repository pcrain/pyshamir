#!/usr/bin/python
from pyshamir import *

#Generate a random polynomial, distribute shares to other parties, and
#load shares distributed by other parties
#  me   = party doing the generation / distribution / receiving
#  s1   = name of first share the polynomial is based off
#  s2   = name of second share the polynomial is based off
#  t    = degree of random polynomial to generate
#  pids = list of ids of other parties to distribute to / receive from
def rGenProtocol(me,s1,s2,t,pids):
  print(col.WHT+"Computing random polynomial r[" + str(me.id) + "]"+col.BLN)
  me.genRandomP   (s1,s2,t    ) #Generate a random polynomial r for each party
  print(col.WHT+"Writing shares of r[" + str(me.id) + "] to file"+col.BLN)
  me.writeRanShares(s1,s2,pids   )    #Distribute the jth share of p_i's r to party j
  print(col.WHT+"Loading other parties' shares of r[j]"+col.BLN)
  me.loadRanShares(s1,s2,pids   )    #Distribute the jth share of p_i's r to party j

#Sum previously generated random shares with (s1*s2), distribute the result, and
#combine to form the vector v
#  me   = party doing the generation / distribution / receiving
#  s1   = name of first share the vector is based off
#  s2   = name of second share the vector is based off
#returns: the vector v as described here - http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html
def vGenProtocol(me,s1,s2):
  print(col.WHT+"Computing share " + str(me.id) + " of v"+col.BLN)
  me.computeVShare(s1,s2)    #Compute shares of the v matrix
  print(col.WHT+"Writing shares of v[" + str(me.id) + "] to file"+col.BLN)
  easyWrite(CLOUD+str(me.id)+"/"+str(me.id)+"-"+s1+"-"+s2+"-vshare",str(me.vshares[s1+"*"+s2]))
  print(col.WHT+"Awaiting v from distributor"+col.BLN)
  return me.loadV(s1,s2)

#Compute the reduced-degree share of (s1*s2)
#  me   = party doing the computation
#  s1   = name of first share the share is based off
#  s2   = name of second share the share is based off
#  v    = vector computed by vGenProtocol()
#  t    = degree of polynomial
#  pids = list of ids of other share-holding parties
def sGenProtocol(me,s1,s2,v,t,pids):
  print(col.WHT+"Computing A matrix"+col.BLN)
  A = genMatrixA(t,pids)
  print(col.WHT+"Computing share " + str(me.id) + " of "+s1+"*"+s2+col.BLN)
  me.computeSShare(s1,s2,v,A[me.relid,:]) #Compute the shares of the new product

#Compute a share of (s1*s2) with the same degree as s1 and s2
#  me   = party doing the computation
#  s1   = name of first share to multiplu
#  s2   = name of second share to multiplu
#  ids  = list of ids of other share-holding parties
def reductionProtocol(me,s1,s2,pids):
  t = int((len(pids)-1)/2)
  rGenProtocol(me,s1,s2,t,pids)       #Load shares
  v = vGenProtocol(me,s1,s2)          #Generate v matrix
  sGenProtocol(me,s1,s2,v,t,pids)     #Generate new shares

#Load shares s1 and s2, compute s3=s1+s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to add
#  s2   = name of second share to add
#  s3   = name of third share to write to disk
#  np   = number of parties involved
def sumProtocol(s1,s2,s3,np):
  pids = [i*i for i in range(1,np+1)]
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSummedShare(s1,s2,s3)       #Write share for s=p+q

#Load shares s1 and s2, compute s3=s1*s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to multiplu
#  s2   = name of second share to multiplu
#  s3   = name of third share to write to disk
#  np   = number of parties involved
def mulProtocol(s1,s2,s3,np):
  pids = [i*i for i in range(1,np+1)]
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  reductionProtocol(me,s1,s2,pids)    #Generate share for m=p*q
  me.writeMultipliedShare(s1,s2,s3)   #Write new shares to file

def main():
  global _myID, np
  if len(sys.argv) < 3: sys.exit(-1)
  _myID = int(sys.argv[1])
  np = int(sys.argv[2])
  print(str(_myID))

  sumProtocol("p","q","s",np)
  mulProtocol("p","q","m",np)
  sumProtocol("s","s","s2",np)

if __name__ == "__main__":
  main()
