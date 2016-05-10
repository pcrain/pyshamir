#!/usr/bin/python
#Python implementation of Shamir's Secret Sharing using the BGW protocol
#Author: Patrick Crain
#BGW reference: http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html

import sys, os, random, json, time, shutil
from random import shuffle

#Numpy for matrix stuff
import numpy as np
from numpy import dot
from numpy.linalg import inv

#mpmath for arbitrary float precision
from mpmath import *
mp.dps = 500; mp.pretty = True

N = 50 #Total number of parties

T = int(N/2-1) #Degree of polynomial (Need t+1 points to define)
IDS = [i for i in range(1,N+1)]

#Max value for our finite field arithmetic
DEBUG = True
PRIME = 2074722246773485207821695222107608587480996474721117292752992589912196684750549658310084416732550077
SMAX = int(sqrt(PRIME)) #Maximum value for our secrets
PMAX = int(pow(PRIME,1/N)) #Maximum value for polynomial coefficients
CLOUD="_cloud/" #Directory for temporary computation files

#Terminal color codes
class col:
  BLN      ='\033[0m'            # Blank
  UND      ='\033[1;4m'          # Underlined
  INV      ='\033[1;7m'          # Inverted
  CRT      ='\033[1;41m'         # Critical
  BLK      ='\033[1;30m'         # Black
  RED      ='\033[1;31m'         # Red
  GRN      ='\033[1;32m'         # Green
  YLW      ='\033[1;33m'         # Yellow
  BLU      ='\033[1;34m'         # Blue
  MGN      ='\033[1;35m'         # Magenta
  CYN      ='\033[1;36m'         # Cyan
  WHT      ='\033[1;37m'         # White

def dprint(string):
  if DEBUG:
    print(string)

def dnprint(string,prec):
  if DEBUG:
    nprint(string,prec)

    #Cleans up temporary files between runs
def cleanup():
  if not os.path.exists(CLOUD):
    return
  for f in os.listdir(CLOUD):
    file_path = os.path.join(CLOUD, f)
    try:
      if os.path.isfile(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path): shutil.rmtree(file_path)
    except Exception as e:
      print(e)

#Load data from a JSON file
#  fname = file to load from
def jload(fname):
  with open(fname,'r') as j:
    x = json.load(j)
  return x

#Compute the greatest common denominator of a and b
#  a = first number
#  b = second number
def extendedEuclideanAlgorithm(a, b):
  if abs(b) > abs(a):
    (x,y,d) = extendedEuclideanAlgorithm(b, a)
    return (y,x,d)
  if abs(b) == 0:
    return (1, 0, a)
  x1, x2, y1, y2 = 0, 1, 1, 0
  while b != 0:
    q = floor(a / b)
    r = floor(fmod(a,b))
    x = x2 - q*x1
    y = y2 - q*y1
    a, b, x2, x1, y2, y1 = b, r, x1, x, y1, y
  return (x2, y2, a)

#Find the multiplicative inverse of n mod PRIME
#  n = number to find the multiplicative inverse for
def inverse(n):
 x,y,d = extendedEuclideanAlgorithm(n, PRIME)
 return floor(fmod(x,PRIME))

#Compute the lagrange polynomial for a list of points
#Based on code from (https://github.com/rhyzomatic/pygarble)
#  points = a list of points (x,y)
def lagrange(points):
  def P(x):
    total = 0
    n = len(points)
    for i in range(0,n):
      xi, yi = points[i]
      # print(type(yi))
      def g(i, n):
        tot_mul = 1
        for j in range(0,n):
          if i == j:
            continue
          xj, yj = points[j]
          tot_mul *= (x - xj) / mpf(xi - xj)
        return tot_mul
      total += yi * g(i, n)
    return total
  return P

#Generate a polynomial of degree d with intercept y
#  y = y-intercept of polynomial
#  d = degree of polynomial
def polygen(y,d):
  poly = [y]
  for i in range(0,d):
    poly.append(random.randrange(PMAX))
  return poly

#Evaluate a polyonmial p at point x
#  p = polynomial to evaluate
#  x = point to evaluate the polynomial at
def evalpolyat(p,x):
  # print(col.YLW + str(p) + col.RED + str(x) + col.BLN)
  s = p[0]
  for i in range(1,len(p)):
    s += (p[i]*pow(x,i))
  return s

def vandermonde(arr):
  v = []
  for x in arr:
    vr = [1]
    for i in range(1,len(arr)):
      vr.append(x*vr[i-1])
    v.append(vr)
  v = matrix(v)
  dprint(col.GRN + "V: \n" + col.BLN + str(v))
  return v

#Compute an (n,t) diagonal matrix
#  n = total number of parties
#  t = threshold number of parties
def diag(n,t):
  a = []
  for i in range(0,n):
    aa = []
    for j in range(0,n):
      if i == j and i >= 0 and i <= t:
        aa.append(1)
      else:
        aa.append(0)
    a.append(aa)
  a = matrix(a)
  dprint(col.GRN + "P:" + col.BLN)
  dnprint(a,5)
  return a

#Generate the A matrix as described here (http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html)
#  t  = threshold number of parties
#  ps = list of parties involved in the computation
def genMatrixA(t,ps):
  v = vandermonde(ps)
  p = diag(len(ps),t)
  A = (v*p)*(v**-1)
  dprint(col.GRN + "A: " + col.BLN + "\n" + nstr(A,5))
  return A

#Class for a party involved in the computation
class Party:
  #Constructor for Party
  #  myid = ID / x-value of the party for shares
  #  j    = Party's index in the list of party ids
  def __init__(self,myid,j):
    self.id = myid         #ID / x-value of the party for shares
    self.relid = j         #Party's index in the list of party ids
    self.secretshares = {} #Secrets which this party has shares for
    self.ranpoly = {}      #Secrets which this party has random polynomials for
    self.ranshares = {}    #Secrets which this party has collected random shares for
    self.vshares = {}      #Secrets which this party has computed v-shares for
    self.sshares = {}      #Computed shares of degree-reduced secrets

  #Generate a random polynomial for use in degree reduction
  #  s1   = name of first share the polynomial is based off
  #  s2   = name of second share the polynomial is based off
  #  t    = degree the polynomial will be reduced to
  def genRandomP(self,s1,s2,t):
    name=s1+"*"+s2
    self.ranpoly[name] = polygen(0,t*2)
    # print(col.GRN + "r[i]: " + col.BLN + str(self.ranpoly))

  #Generate shares from a random polynomial and distribute them (in memory)
  #  s1     = name of first share the polynomial is based off
  #  s2     = name of second share the polynomial is based off
  #  others = list of other parties to send shares to
  def sendRanShares(self,s1,s2,others):
    name=s1+"*"+s2
    for o in others:
      s = evalpolyat(self.ranpoly[name],o.id)
      o.acceptRanShare(s,name)
    # print(col.GRN + "rshares[j]: " + col.BLN + str(s))

  #Accept random shares from another party (in memory)
  #  share = value of the share to accept
  #  name  = the name of the share
  def acceptRanShare(self,share,name):
    if name in self.ranshares.keys():
      self.ranshares[name].append(share)
    else:
      self.ranshares[name] = [share]

  #Generate shares from a random polynomial and distribute them to disk
  #  s1     = name of first share the random shares are based off
  #  s2     = name of second share the random shares are based off
  #  oids   = list of other parties to send shares to
  def writeRanShares(self,s1,s2,oids):
    name=s1+"*"+s2
    for o in oids:
      s = evalpolyat(self.ranpoly[name],o)
      easyWrite(CLOUD+str(o)+"/"+str(o)+"-"+str(self.id)+"-"+s1+"-"+s2+"-ranshare",str(s))

  #Accept random shares from parties listen in oids (from disk)
  #  s1     = name of first share the random shares are based off
  #  s2     = name of second share the random shares are based off
  #  oids   = list of parties to receive shares from
  def loadRanShares(self,s1,s2,oids):
    name=s1+"*"+s2
    for o in oids:
      share = mpmathify(easyRead(CLOUD+str(self.id)+"/"+str(self.id)+"-"+str(o)+"-"+s1+"-"+s2+"-ranshare"))
      if name in self.ranshares.keys():
        self.ranshares[name].append(share)
      else:
        self.ranshares[name] = [share]

  #Compute shares of v for two other shares
  #  s1     = name of first share the v share is based off
  #  s2     = name of second share the v share is based off
  def computeVShare(self,s1,s2):
    name=s1+"*"+s2
    # self.vshares[name] =  self.secretshares[s1][1]*inverse(self.secretshares[s2][1])
    # self.vshares[name] =  self.secretshares[s1][1]/(self.secretshares[s2][1])
    self.vshares[name] =  self.secretshares[s1][1]*(self.secretshares[s2][1])
    self.vshares[name] += sum(self.ranshares[name])
    # dprint(col.GRN + "v: " + col.BLN + str(self.vshares[name]))

  def shareVShare(self,s1,s2,oids):
    name=s1+"*"+s2
    rpoly = polygen(self.vshares[name],int((len(oids)-1)/2))
    print(col.BLU+str(rpoly)+col.BLN)
    for o in oids:
      s = evalpolyat(rpoly,o)
      easyWrite(CLOUD+str(o)+"/"+str(o)+"-"+str(self.id)+"-"+s1+"-"+s2+"-vsubshare",str(s))

  def computeLinearShares(self,s1,s2,oids):
    name=s1+"*"+s2
    A = genMatrixA(int((len(oids)-1)/2),oids)
    # print(col.BLU+str(A[0,0])+col.BLN)
    ki = 0
    for k in oids:
      total = 0
      ii = 0
      for i in oids:
        vs = easyRead(CLOUD+str(self.id)+"/"+str(self.id)+"-"+str(i)+"-"+s1+"-"+s2+"-vsubshare")
        vs = mpmathify(vs)
        total += (vs*A[ki,ii])
        ii += 1
      easyWrite(CLOUD+str(k)+"/"+str(k)+"-"+str(self.id)+"-"+s1+"-"+s2+"-vnewshare",str(total))
      ki += 1
      # print(col.BLU+str(vs)+col.BLN)

  def reconstructSShare(self,s1,s2,oids):
    name=s1+"*"+s2
    svals = []
    for o in oids:
      v = easyRead(CLOUD+str(self.id)+"/"+str(self.id)+"-"+str(o)+"-"+s1+"-"+s2+"-vnewshare")
      svals.append((o,mpmathify(v)))
    s = nint(lagrange(svals)(0)) % PRIME
    self.sshares[name] = (self.id,s)
    # print(col.BLU+str(s)+col.BLN)
    # s = evalpolyat(spoly,0)

  #Return the share of v for two other shares
  #  s1     = name of first share the v share is based off
  #  s2     = name of second share the v share is based off
  def getVShare(self,s1,s2):
    name=s1+"*"+s2
    return self.vshares[name]

  #Load v shares from disk
  #  s1     = name of first share the v share is based off
  #  s2     = name of second share the v share is based off
  def loadVShare(self,s1,s2):
    fname = CLOUD+str(self.id)+"/"+str(self.id)+"-"+s1+"-"+s2+"-vshare"
    line = easyRead(fname)
    return mpmathify(line)

  #Compute the reduced-degree share of (s1*s2)
  #  s1     = name of first share the new share is based off
  #  s2     = name of second share the new share is based off
  #  v      = v matrix computed from v shares
  #  arow   = row of A matrix as described here: http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html
  def computeSShare(self,s1,s2,v,arow):
    name=s1+"*"+s2
    self.sshares[name] = (self.id,dot(arow,v))

  #Load the reduced-degree share of (s1*s2) from disk
  #  s1     = name of first share the new share is based off
  #  s2     = name of second share the new share is based off
  def loadSShare(self,s1,s2):
    fname = CLOUD+str(self.id)+"/"+str(self.id)+"-"+s1+"-"+s2+"-sshare"
    line = easyRead(fname)
    l1 = int(line.split(",")[0].split("(")[1])
    l2 = mpmathify(line.split(",")[1].split(")")[0])
    return (l1,l2)

  #Return the reduced-degree share of (s1*s2)
  #  s1     = name of first share the new share is based off
  #  s2     = name of second share the new share is based off
  def getSShare(self,s1,s2):
    name=s1+"*"+s2
    return self.sshares[s1+"*"+s2]

  #Load a secret share from disk
  #  name = name of the share to load
  def loadSecretShare(self,name):
    if not DEBUG:
      print(col.WHT+"Loading share " + str(self.id) + " of "+name+col.BLN)
    fname = CLOUD+str(self.id)+"/"+str(self.id)+"-"+name+"-share"
    line = mpmathify(easyRead(fname))
    self.secretshares[name] = (self.id,line)
    return(self.secretshares[name])

  #Write the sum of shares s1,s2 to disk
  #  s1      = name of first share the summed share is based off
  #  s2      = name of second share the summed share is based off
  #  newname = name of the new summed share
  def writeSummedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+s1+"+"+s2+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.secretshares[s1][1]+self.secretshares[s2][1]))

  #Write the sum of share s and constant c to disk
  #  s1      = name of share to be summed
  #  s2      = constant to sum share with
  #  newname = name of the new summed share
  def writeConstSumShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.secretshares[s][1]+c))

  #Write the difference of shares s1,s2 to disk
  #  s1      = name of first share the subtracted share is based off
  #  s2      = name of second share the subtracted share is based off
  #  newname = name of the new subtracted share
  def writeSubbedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+s1+"-"+s2+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.secretshares[s1][1]-self.secretshares[s2][1]))

  #Write the difference of share s and constant c to disk
  #  s1      = name of share to be subtract from
  #  s2      = constant to subtract with
  #  newname = name of the new summed share
  def writeConstSubShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.secretshares[s][1]-c))

  #Write the product of shares s1,s2 to disk
  #  s1      = name of first share the multiplied share is based off
  #  s2      = name of second share the multiplied share is based off
  #  newname = name of the new multiplied share
  def writeMultipliedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.sshares[s1+"*"+s2][1]))

  #Write the product of share s and constant c to disk
  #  s1      = name of share to be multiplied
  #  s2      = constant to multiply share by
  #  newname = name of the new multiplied share
  def writeConstMultipleShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(CLOUD+str(self.id)+"/"+str(self.id)+"-"+newname+"-share",str(self.secretshares[s][1]*c))

  #Load a v vector (previous computed from v shares) from disk
  #  s1     = name of first share the v vector is based off
  #  s2     = name of second share the v vector is based off
  def loadV(self,s1,s2):
    line = easyRead(CLOUD+str(self.id)+"/"+str(self.id)+"-"+s1+"-"+s2+"-v").replace("[","").replace("]","").replace(" ","")
    lv = line.split(",")
    # print(lv)
    return [mpmathify(l) for l in lv]

#Generate shares of a secret and distribute them
#  name    = name of the shares to distribute
#  secret  = value to distribute
#  t       = threshold of the polynomial to generate
#  parties = parties to distribute to
def genShares(name,secret,t,parties):
  pg = polygen(secret,t)
  dprint(col.GRN + "num: " + col.BLN + str(pg))
  for p in parties:
    p.secretshares[name] = (p.id,evalpolyat(pg,p.id) % PRIME)
  if DEBUG:
    print(col.GRN + "num[j]: " + col.BLN + str([p.secretshares[name] for p in parties]))

#Easy one-line write to file
#  path = file to write to
#  line = string to write
def easyWrite(path,line):
  with open(path,"w") as of:
    of.write(line)

#Easy one-line read from file
#  path = file to read from
def easyRead(path):
  if not os.path.exists(path):
    print("Waiting for " + path + "...")
    while not os.path.exists(path):
      time.sleep(1)
  with open(path,"r") as inf:
    return inf.read().split("\n")[0]

def testAddition(ids):
  ps = [Party(ids[x],x) for x in range(0,len(ids))]  #Generate new parties with the specified ids
  p,q = [random.randrange(SMAX) for i in range(0,2)] #Generate two numbers to multiply
  genShares("p",p,T,ps); genShares("q",q,T,ps)       #Distribute the two numbers to all parties
  print(col.YLW + str(p) + "+" + str(q) + col.BLN)

  sumshares = [(pa.id,pa.secretshares["p"][1] + pa.secretshares["q"][1]) for pa in ps]

  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(p+q) + col.BLN)
  print(col.MGN + str(ids) + col.GRN + "\n  " + str(int(nint(lagrange(sumshares)(0)))%PRIME) + col.BLN)

def testMultiplication(ids):
  ps = [Party(ids[x],x) for x in range(0,len(ids))]  #Generate new parties with the specified ids
  p,q = [random.randrange(SMAX) for i in range(0,2)] #Generate two numbers to multiply
  genShares("p",p,T,ps); genShares("q",q,T,ps)       #Distribute the two numbers to all parties
  print(col.YLW + str(p) + "*" + str(q) + col.BLN)

  A = genMatrixA(T,ids)
  [pa.genRandomP   ("p","q",T    ) for pa in ps]     #Generate a random polynomial r for each party
  [pa.writeRanShares("p","q",ids   ) for pa in ps]     #Distribute the jth share of p_i's r to party j
  [pa.loadRanShares("p","q",ids   ) for pa in ps]     #Distribute the jth share of p_i's r to party j
  [pa.computeVShare("p","q"      ) for pa in ps]     #Compute shares of the v matrix
  v = [pa.getVShare("p","q"      ) for pa in ps]     #Aggregate the v matrix (must be done in order)
  [pa.computeSShare(
    "p","q",v,A[pa.relid,:]      ) for pa in ps]     #Compute the shares of the new product
  s = [pa.getSShare("p","q"      ) for pa in ps]     #Aggregate the shares of the new product

  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(p*q) + col.BLN)
  print(col.MGN + str(ids) + col.GRN + "\n  " + str(int(nint(lagrange(s)(0)))%PRIME) + col.BLN)

def protocol():
  for i in IDS:
    fpath = CLOUD+str(i)
    if not os.path.exists(fpath): os.makedirs(fpath)
  #Constant
  ps = [Party(IDS[x],x) for x in range(0,len(IDS))]  #Generate new parties with the specified ids
  #Main Generate
  p,q = [random.randrange(SMAX) for i in range(0,2)] #Generate two numbers to multiply
  print(col.YLW + str(p) + "*" + str(q) + col.BLN)
  pp = polygen(p,T)
  dprint(col.GRN + "p: \n" + col.BLN + str(pp))
  qq = polygen(q,T)
  dprint(col.GRN + "q: \n" + col.BLN + str(qq))
  [easyWrite(CLOUD+str(pa.id)+"/"+str(pa.id)+"-p-share",str(evalpolyat(pp,pa.id) % PRIME)) for pa in ps]
  [easyWrite(CLOUD+str(pa.id)+"/"+str(pa.id)+"-q-share",str(evalpolyat(qq,pa.id) % PRIME)) for pa in ps]
  #Individual Load and write
  [pa.loadSecretShare("p") for pa in ps]
  [pa.loadSecretShare("q") for pa in ps]
  [pa.genRandomP   ("p","q",T    ) for pa in ps]     #Generate a random polynomial r for each party
  [pa.writeRanShares("p","q",IDS   ) for pa in ps]     #Distribute the jth share of p_i's r to party j
  [pa.loadRanShares("p","q",IDS   ) for pa in ps]     #Distribute the jth share of p_i's r to party j
  #Individual compute
  [pa.computeVShare("p","q"      ) for pa in ps]     #Compute shares of the v matrix
  dprint(col.GRN + "v: " + col.BLN + str([pa.getVShare("p","q") for pa in ps]))
  [easyWrite(CLOUD+str(pa.id)+"/"+str(pa.id)+"-p-q-vshare",str(pa.vshares["p*q"])) for pa in ps]
  v2 = [pa.loadVShare("p","q"      ) for pa in ps]     #Aggregate the v matrix (must be done in order)
  [easyWrite(CLOUD+str(pa.id)+"/"+str(pa.id)+"-p-q-v",str(v2)) for pa in ps]
  v = ps[0].loadV("p","q")

  A = genMatrixA(T,IDS)
  [pa.computeSShare(
    "p","q",v,A[pa.relid,:]      ) for pa in ps]     #Compute the shares of the new product
  [easyWrite(CLOUD+str(pa.id)+"/"+str(pa.id)+"-p-q-sshare",str(pa.sshares["p*q"])) for pa in ps]
  #Main Finish
  s = [pa.loadSShare("p","q"      ) for pa in ps]     #Aggregate the shares of the new product
  if DEBUG:
    # sp = [(s[i][0],nstr(s[i][1],5)) for i in range(0,len(s))]
    print(col.GRN + "s: \n" + col.BLN + str(s))
  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(p*q) + col.BLN)
  print(col.MGN + str(IDS) + col.GRN + "\n  " + str(int(nint(lagrange(s)(0)))%PRIME) + col.BLN)

def runtests():
  # print(
  #   col.CYN + str(t+1) + "-way secrets with degree t=" +
  #   str(t) + " polynomials among " + str(n) + " parties" + col.BLN
  # )
  partyids = random.sample(range(1,N*10),T*2+1)
  for i in partyids:
    fpath = CLOUD+str(i)
    if not os.path.exists(fpath): os.makedirs(fpath)
  print(col.RED + "ADDITION" + col.BLN)
  testAddition(partyids)       #Addition
  print()
  print(col.RED + "MULTIPLICATION" + col.BLN)
  testMultiplication(partyids) #Multiplication
  print()

def main():
  cleanup()
  if not os.path.exists(CLOUD):
    os.makedirs(CLOUD)
  runtests()
  # protocol()

if __name__ == "__main__":
  main()
