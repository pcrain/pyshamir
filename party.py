#!/usr/bin/python
#Mockup of party for secure computation
from pyshamir import *

pids = []
secrets = {}

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
def vGenProtocol(me,s1,s2,pids):
  me.computeVShare(s1,s2)    #Compute shares of the v matrix
  # easyWrite(CLOUD+str(me.id)+"/"+str(me.id)+"-"+s1+"-"+s2+"-vshare",str(me.vshares[s1+"*"+s2]))
  me.shareVShare(s1,s2,pids)
  me.computeLinearShares(s1,s2,pids)
  me.reconstructSShare(s1,s2,pids)
  # return me.loadV(s1,s2)

#Sum previously generated random shares with (s1*s2), distribute the result, and
#combine to form the vector v
#  me   = party doing the generation / distribution / receiving
#  s1   = name of first share the vector is based off
#  s2   = name of second share the vector is based off
def vGenProtocolOld(me,s1,s2,pids):
  print(col.WHT+"Computing share " + str(me.id) + " of v"+col.BLN)
  me.computeVShare(s1,s2)    #Compute shares of the v matrix
  print(col.WHT+"Writing shares of v[" + str(me.id) + "] to file"+col.BLN)
  easyWrite(CLOUD+str(me.id)+"/"+str(me.id)+"-"+s1+"-"+s2+"-vshare",str(me.vshares[s1+"*"+s2]))
  print(col.WHT+"Awaiting v from distributor"+col.BLN)
  return me.loadV(s1,s2)

#Compute the reduced-degree share of (s1*s2)
#  me   = party doing the computation
#  s1   = name of first share the new share is based off
#  s2   = name of second share the new share is based off
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
#  s1   = name of first share to multiply
#  s2   = name of second share to multiply
#  ids  = list of ids of other share-holding parties
def reductionProtocol(me,s1,s2,pids):
  t = int((len(pids)-1)/2)
  rGenProtocol(me,s1,s2,t,pids)       #Load shares
  vGenProtocol(me,s1,s2,pids)          #Generate v matrix
  # sGenProtocol(me,s1,s2,v,t,pids)     #Generate new shares

#Load shares s1 and s2, compute s3=s1+s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to add
#  s2   = name of second share to add
#  s3   = name of third share to write to disk
def addProtocol(s1,s2,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSummedShare(s1,s2,s3)       #Write share for s=p+q

#Load shares s, compute s3=s+c, and write share s3 to file
#  me   = party doing the computation
#  s    = name of share to add
#  c    = name of constant to add
#  s3   = name of share to write to disk
def addConstProtocol(s,c,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s)               #Load share for p
  me.writeConstSumShare(s,c,s3)       #Write share for s=p+q

#Load shares s1 and s2, compute s3=s1-s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of share to subtract from
#  s2   = name of share to subtract with
#  s3   = name of third share to write to disk
def subProtocol(s1,s2,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSubbedShare(s1,s2,s3)       #Write share for s=p-q

#Load shares s, compute s3=s-c, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of share to subtract from
#  s2   = name of share to subtract with
#  s3   = name of third share to write to disk
def subConstProtocol(s,c,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s)              #Load share for p
  me.writeConstSubShare(s,c,s3)       #Write share for s=p-q

#Load shares s1 and s2, compute s3=s1*s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to multiply
#  s2   = name of second share to multiply
#  s3   = name of third share to write to disk
def mulProtocol(s1,s2,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  reductionProtocol(me,s1,s2,pids)    #Generate share for m=p*q
  me.writeMultipliedShare(s1,s2,s3)   #Write new shares to file

#Load shares s, compute s3=s*c, and write share s3 to file
#  me   = party doing the computation
#  s    = name of share to multiply
#  c    = name of constant to multiply
#  s3   = name of share to write to disk
def mulConstProtocol(s,c,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s)               #Load share for p
  me.writeConstMultipleShare(s,c,s3)  #Write new shares to file

#Load shares s1 and s2, compute s3=s1/s2, and write share s3 to file (NOT WORKING)
#  me   = party doing the computation
#  s1   = name of divisor share
#  s2   = name of dividend share
#  s3   = name of third share to write to disk
def divProtocol(s1,s2,s3):
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  reductionProtocol(me,s1,s2,pids)    #Generate share for m=p*q
  me.writeMultipliedShare(s1,s2,s3)   #Write new shares to file

def computeFromShares(s,id,pids):
  sshare = mpmathify(easyRead(CLOUD+str(id)+"/"+str(id)+"-"+s+"-share"))
  [easyWrite(CLOUD+str(pa)+"/"+str(pa)+"-"+str(id)+"-"+s+"-revealshare",str(sshare)) for pa in pids]
  ss = []
  for pa in pids:
    share = easyRead(CLOUD+str(id)+"/"+str(id)+"-"+str(pa)+"-"+s+"-revealshare")
    ss.append((pa,mpmathify(share)))
  n = int(nint(lagrange(ss)(0)))%PRIME
  easyWrite(CLOUD+str(id)+"/"+str(id)+"-"+s+"-computed",str(n))

def printComputed(s):
  x = easyRead(CLOUD+str(pids[_myID])+"/"+str(pids[_myID])+"-"+s+"-computed")
  print(col.YLW+s+" = "+x+col.BLN)

#Distribute shares of a number to a list of parties
#  name  = name of the secret to be distributed
#  pids = list of ids of other parties to distribute to / receive from
def distributeNumber(name,pids):
  t=int((len(pids)-1)/2)
  print(col.WHT+"Generating polynomials for "+name+col.BLN)
  pp = polygen(secrets[name],t)
  # print(pp)
  print(col.WHT+"Distributing polynomial for "+name+col.BLN)
  for x in pids:
    base = CLOUD+str(x)
    if not os.path.exists(base): os.makedirs(base)
    path = base+"/"+str(x)+"-"+name+"-share"
    # print(path)
    easyWrite(path,str(evalpolyat(pp,x) % PRIME))

def main():
  global _myID, np, pids, secrets
  if len(sys.argv) < 2: sys.exit(-1)
  _myID = int(sys.argv[1])
  print(_myID)

  pids = jload("parties.json")
  ppath = PRIV+str(pids[_myID])
  if not os.path.exists(ppath): os.makedirs(ppath)
  if os.path.exists(ppath+"/secrets.json"):
    secrets=jload(ppath+"/secrets.json")
    print(col.RED+str(secrets)+col.BLN)


  computations=jload("comps.json")
  for c in computations:
    if len(c) == 1:
      computeFromShares(c[0],pids[_myID],pids)
      printComputed(c[0])
      continue
    if len(c) == 2:
      if (c[0] in secrets.keys()):
        distributeNumber(c[0],pids)
      continue
    if c[1] == "+":
      if type(c[2]) == int:
        addConstProtocol(c[0],c[2],c[3])
      else:
        addProtocol(c[0],c[2],c[3])
    elif c[1] == "-":
      if type(c[2]) == int:
        subConstProtocol(c[0],c[2],c[3])
      else:
        subProtocol(c[0],c[2],c[3])
    elif c[1] == "*":
      if type(c[2]) == int:
        mulConstProtocol(c[0],c[2],c[3])
      else:
        mulProtocol(c[0],c[2],c[3])
    elif c[1] == "/": #(NOT WORKING)
      divProtocol(c[0],c[2],c[3])

if __name__ == "__main__":
  main()
