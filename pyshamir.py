#!/usr/bin/python
#Python implementation of Shamir's Secret Sharing using the BGW protocol
#Author: Patrick Crain
#BGW reference: http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html

import sys, os, random, json, time, shutil
from random import shuffle
from mpmath import * #mpmath for arbitrary float precision
mp.dps = 500; mp.pretty = True

#Max value for our finite field arithmetic
PRIME = 2074722246773485207821695222107608587480996474721117292752992589912196684750549658310084416732550077
DEBUG = True                #Whether to print debug stuff
N     = 30                  #Max number of parties
SMAX  = int(sqrt(PRIME))    #Maximum value for our secrets
PMAX  = int(pow(PRIME,1/N)) #Maximum value for polynomial coefficients
CLOUD = "_cloud/"           #Directory for temporary computation files
PRIV  = "known-secrets/"    #Directory for known secrets

#Terminal color codes
class col:
  BLN  ='\033[0m'    # Blank
  UND  ='\033[1;4m'  # Underlined
  INV  ='\033[1;7m'  # Inverted
  CRT  ='\033[1;41m' # Critical
  BLK  ='\033[1;30m' # Black
  RED  ='\033[1;31m' # Red
  GRN  ='\033[1;32m' # Green
  YLW  ='\033[1;33m' # Yellow
  BLU  ='\033[1;34m' # Blue
  MGN  ='\033[1;35m' # Magenta
  CYN  ='\033[1;36m' # Cyan
  WHT  ='\033[1;37m' # White

def dprint(string):
  if DEBUG:
    print(string)

def dnprint(string,prec):
  if DEBUG:
    nprint(string,prec)

#Load data from a JSON file
#  fname = file to load from
def jload(fname):
  if not os.path.exists(fname):
    return None
  with open(fname,'r') as j:
    x = json.load(j)
  return x

#Compute the greatest common denominator of a and b
#Based on code from (https://github.com/rhyzomatic/pygarble)
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
  return [y] + [random.randrange(PMAX) for i in range(0,d)]

#Evaluate a polyonmial p at point x
#  p = polynomial to evaluate
#  x = point to evaluate the polynomial at
def evalpolyat(p,x):
  return p[0] + sum([(p[i]*pow(x,i)) for i in range(1,len(p))])

#Compute the Vandermonde matrix from an array
#  arr = Array the Vandermonde matrix is based off of
def vandermonde(arr):
  v = []
  for x in arr:
    vr = [1]
    for i in range(1,len(arr)):
      vr.append(x*vr[i-1])
    v.append(vr)
  # dprint(col.GRN + "V: \n" + col.BLN + str(v))
  return matrix(v)

#Compute an (n,t) diagonal matrix
#  n = total number of parties
#  t = threshold number of parties
def diag(n,t):
  a = matrix([[(1 if (i==j and i>=0 and i<=t) else 0) for j in range(0,n)] for i in range(0,n)])
  # dprint(col.GRN + "P:" + col.BLN)
  # dnprint(a,5)
  return a

#Generate the A matrix as described here (http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html)
#  t  = threshold number of parties
#  ps = list of parties involved in the computation
def genMatrixA(t,ps):
  v = vandermonde(ps)
  p = diag(len(ps),t)
  A = (v*p)*(v**-1)
  # dprint(col.GRN + "A: " + col.BLN + "\n" + nstr(A,5))
  return A

#Easy one-line write to file
#  path = file to write to
#  line = string to write
def easyWrite(path,line):
  path = CLOUD+path
  with open(path,"w") as of:
    of.write(line)

#Easy one-line read from file
#  path = file to read from
def easyRead(path):
  path = CLOUD+path
  if not os.path.exists(path):
    print("Waiting for " + path + "...")
    while not os.path.exists(path):
      time.sleep(1)
  with open(path,"r") as inf:
    return inf.read().split("\n")[0]

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
    self.ranpoly[s1+"*"+s2] = polygen(0,t*2)
    # print(col.GRN + "r[i]: " + col.BLN + str(self.ranpoly))

  #Generate shares from a random polynomial and distribute them to disk
  #  s1     = name of first share the random shares are based off
  #  s2     = name of second share the random shares are based off
  #  oids   = list of other parties to send shares to
  def writeRanShares(self,s1,s2,oids):
    name=s1+"*"+s2
    for o in oids:
      s = evalpolyat(self.ranpoly[name],o)
      easyWrite(str(o)+"/"+str(self.id)+"-"+s1+"-"+s2+"-ranshare",str(s))

  #Accept random shares from parties listen in oids (from disk)
  #  s1     = name of first share the random shares are based off
  #  s2     = name of second share the random shares are based off
  #  oids   = list of parties to receive shares from
  def loadRanShares(self,s1,s2,oids):
    name=s1+"*"+s2
    for o in oids:
      share = mpmathify(easyRead(str(self.id)+"/"+str(o)+"-"+s1+"-"+s2+"-ranshare"))
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

  #Share a previously computed share of v to other parties
  #  s1     = name of first share the v share is based off
  #  s2     = name of second share the v share is based off
  #  oids   = list of other parties to send shares to
  def shareVShare(self,s1,s2,oids):
    rpoly = polygen(self.vshares[s1+"*"+s2],int((len(oids)-1)/2))
    for o in oids:
      s = evalpolyat(rpoly,o)
      easyWrite(str(o)+"/"+str(self.id)+"-"+s1+"-"+s2+"-vsubshare",str(s))

  #Run a linear protocol to compute Av
  #  s1     = name of first share the linear share is based off
  #  s2     = name of second share the linear share is based off
  #  oids   = list of other parties to send shares to
  def computeLinearShares(self,s1,s2,oids):
    name=s1+"*"+s2
    A = genMatrixA(int((len(oids)-1)/2),oids)
    ki = 0
    for k in oids:
      total = 0
      ii = 0
      for i in oids:
        vs = mpmathify(easyRead(str(self.id)+"/"+str(i)+"-"+s1+"-"+s2+"-vsubshare"))
        total += (vs*A[ki,ii])
        ii += 1
      easyWrite(str(k)+"/"+str(self.id)+"-"+s1+"-"+s2+"-vnewshare",str(total))
      ki += 1

  #Reconstruct degree t share for s1*s2
  #  s1     = name of first share to reconstruct from
  #  s2     = name of second share to reconstruct from
  #  oids   = list of other parties to send shares to
  def reconstructSShare(self,s1,s2,oids):
    svals = []
    for o in oids:
      v = easyRead(str(self.id)+"/"+str(o)+"-"+s1+"-"+s2+"-vnewshare")
      svals.append((o,mpmathify(v)))
    s = nint(lagrange(svals)(0)) % PRIME
    self.sshares[s1+"*"+s2] = (self.id,s)
    # print(col.BLU+str(s)+col.BLN)
    # s = evalpolyat(spoly,0)

  #Load a secret share from disk
  #  name = name of the share to load
  def loadSecretShare(self,name):
    if not DEBUG:
      print(col.WHT+"Loading share " + str(self.id) + " of "+name+col.BLN)
    fname = str(self.id)+"/"+name+"-share"
    line = mpmathify(easyRead(fname))
    self.secretshares[name] = (self.id,line)
    return(self.secretshares[name])

  #Write the sum of shares s1,s2 to disk
  #  s1      = name of first share the summed share is based off
  #  s2      = name of second share the summed share is based off
  #  newname = name of the new summed share
  def writeSummedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+s1+"+"+s2+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+newname+"-share",str(self.secretshares[s1][1]+self.secretshares[s2][1]))

  #Write the sum of share s and constant c to disk
  #  s1      = name of share to be summed
  #  s2      = constant to sum share with
  #  newname = name of the new summed share
  def writeConstSumShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+"-"+newname+"-share",str(self.secretshares[s][1]+c))

  #Write the difference of shares s1,s2 to disk
  #  s1      = name of first share the subtracted share is based off
  #  s2      = name of second share the subtracted share is based off
  #  newname = name of the new subtracted share
  def writeSubbedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+s1+"-"+s2+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+newname+"-share",str(self.secretshares[s1][1]-self.secretshares[s2][1]))

  #Write the difference of share s and constant c to disk
  #  s1      = name of share to be subtract from
  #  s2      = constant to subtract with
  #  newname = name of the new summed share
  def writeConstSubShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+newname+"-share",str(self.secretshares[s][1]-c))

  #Write the product of shares s1,s2 to disk
  #  s1      = name of first share the multiplied share is based off
  #  s2      = name of second share the multiplied share is based off
  #  newname = name of the new multiplied share
  def writeMultipliedShare(self,s1,s2,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+newname+"-share",str(self.sshares[s1+"*"+s2][1]))

  #Write the product of share s and constant c to disk
  #  s1      = name of share to be multiplied
  #  s2      = constant to multiply share by
  #  newname = name of the new multiplied share
  def writeConstMultipleShare(self,s,c,newname):
    print(col.WHT+"Writing share "+newname+"[" + str(self.id) + "] to file"+col.BLN)
    easyWrite(str(self.id)+"/"+newname+"-share",str(self.secretshares[s][1]*c))
