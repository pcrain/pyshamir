#!/usr/bin/python
#Mockup of party for secure computation
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

#Compute a share of (s1*s2) with the same degree as s1 and s2
#  me   = party doing the computation
#  s1   = name of first share to multiply
#  s2   = name of second share to multiply
#  ids  = list of ids of other share-holding parties
def reductionProtocol(me,s1,s2,pids):
  t = int((len(pids)-1)/2)
  rGenProtocol(me,s1,s2,t,pids)       #Load shares
  me.computeVShare(s1,s2)             #Compute share of the v matrix
  me.shareVShare(s1,s2,pids)          #Split v again and share that
  me.computeLinearShares(s1,s2,pids)  #Compute Av
  me.reconstructSShare(s1,s2,pids)    #Compute share of s1*s2

#Load shares s1 and s2, compute s3=s1+s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to add
#  s2   = name of second share to add
#  s3   = name of third share to write to disk
def addProtocol(s1,s2,s3):
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSummedShare(s1,s2,s3)       #Write share for s=p+q

#Load shares s, compute s3=s+c, and write share s3 to file
#  me   = party doing the computation
#  s    = name of share to add
#  c    = name of constant to add
#  s3   = name of share to write to disk
def addConstProtocol(s,c,s3):
  me.loadSecretShare(s)               #Load share for p
  me.writeConstSumShare(s,c,s3)       #Write share for s=p+q

#Load shares s1 and s2, compute s3=s1-s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of share to subtract from
#  s2   = name of share to subtract with
#  s3   = name of third share to write to disk
def subProtocol(s1,s2,s3):
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  me.writeSubbedShare(s1,s2,s3)       #Write share for s=p-q

#Load shares s, compute s3=s-c, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of share to subtract from
#  s2   = name of share to subtract with
#  s3   = name of third share to write to disk
def subConstProtocol(s,c,s3):
  me.loadSecretShare(s)               #Load share for p
  me.writeConstSubShare(s,c,s3)       #Write share for s=p-q

#Load shares s1 and s2, compute s3=s1*s2, and write share s3 to file
#  me   = party doing the computation
#  s1   = name of first share to multiply
#  s2   = name of second share to multiply
#  s3   = name of third share to write to disk
def mulProtocol(s1,s2,s3):
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
  me.loadSecretShare(s)               #Load share for p
  me.writeConstMultipleShare(s,c,s3)  #Write new shares to file

#Load shares s1 and s2, compute s3=s1/s2, and write share s3 to file (NOT WORKING)
#  me   = party doing the computation
#  s1   = name of divisor share
#  s2   = name of dividend share
#  s3   = name of third share to write to disk
def divProtocol(s1,s2,s3):
  me.loadSecretShare(s1)              #Load share for p
  me.loadSecretShare(s2)              #Load share for q
  reductionProtocol(me,s1,s2,pids)    #Generate share for m=p*q
  me.writeMultipliedShare(s1,s2,s3)   #Write new shares to file

#Request computation of s from shares
#  s       = value to compute
#  printit = whether to print the share to the terminal
def computeFromShares(s,printit=True):
  i = pids[_myID]
  sshare = mpmathify(easyRead(str(i)+"/"+s+"-share"))
  [easyWrite(str(p)+"/"+str(i)+"-"+s+"-tmp",str(sshare)) for p in pids]
  ss = [(p,mpmathify(easyRead(str(i)+"/"+str(p)+"-"+s+"-tmp"))) for p in pids]
  n = int(nint(lagrange(ss)(0)))%PRIME
  if printit:
    print(col.YLW+s+" = "+str(n)+col.BLN)
  easyWrite(str(i)+"/"+s+"-computed",str(n))

#Distribute shares of a secret to a list of parties
#  name  = name of the secret to be distributed
def distributeSecret(name):
  t=int((len(pids)-1)/2)
  print(col.WHT+"Distributing polynomials for "+name+col.BLN)
  pp = polygen(secrets[name],t)
  for x in pids:
    if not os.path.exists(CLOUD+str(x)): os.makedirs(CLOUD+str(x))
    easyWrite(str(x)+"/"+name+"-share",str(evalpolyat(pp,x) % PRIME))

def main():
  global _myID, np, pids, secrets, me
  if len(sys.argv) < 2: sys.exit(-1)
  _myID = int(sys.argv[1])
  print(_myID)

  pids = jload("parties.json")
  me = Party(pids[_myID],_myID)       #Generate a new Party with input id
  ppath = PRIV+str(pids[_myID])
  if not os.path.exists(ppath): os.makedirs(ppath)
  secrets = {}
  if os.path.exists(ppath+"/secrets.json"):
    secrets=jload(ppath+"/secrets.json")
    print(col.RED+str(secrets)+col.BLN)

  computations=jload("comps.json")
  for c in computations:
    if len(c) == 1:
      computeFromShares(c[0])
    elif len(c) == 2:
      if (c[0] in secrets.keys()):
        distributeSecret(c[0])
    elif c[1] == "+":
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
