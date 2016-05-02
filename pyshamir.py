#!/usr/bin/python
#Python implementation of Shamir's Secret Sharing using the BGW protocol
#Author: Patrick Crain
#References:
#  My reference for implementing BGW
#    http://cseweb.ucsd.edu/classes/fa02/cse208/lec12.html
import sys, random, json

#Numpy for matrix stuff
import numpy as np
from numpy import dot
from numpy.linalg import inv

#mpmath for arbitrary float precision
from mpmath import *
mp.dps = 500; mp.pretty = True

t = 2 #Degree of polynomial (Need t+1 points to define)
n = 5 #Total number of parties

PRIME = 22953686867719691230002707821868552601124472329079
# PRIME = 2074722246773485207821695222107608587480996474721117292752992589912196684750549658310084416732550077
SMAX = int(sqrt(PRIME)) #Maximum value for our secrets
PMAX = int(pow(PRIME,1/n)) #Maximum value for polynomial coefficients

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

#Finite fields, from https://jeremykun.com/2014/03/13/programming-with-finite-fields/
def extendedEuclideanAlgorithm(a, b):
  if abs(b) > abs(a):
    (x,y,d) = extendedEuclideanAlgorithm(b, a)
    return (y,x,d)
  if abs(b) == 0:
    return (1, 0, a)
  x1, x2, y1, y2 = 0, 1, 1, 0
  while abs(b) > 0:
    q, r = divmod(a,b)
    x = x2 - q*x1
    y = y2 - q*y1
    a, b, x2, x1, y2, y1 = b, r, x1, x, y1, y
  return (x2, y2, a)

def IntegersModP(p):
  class IntegerModP(int):
    def __init__(self, n):
      self.n = n % p
      self.field = IntegerModP
    def __add__(self, other): return IntegerModP(self.n + other.n)
    def __sub__(self, other): return IntegerModP(self.n - other.n)
    def __mul__(self, other): return IntegerModP(self.n * other.n)
    def __truediv__(self, other): return self * other.inverse()
    def __div__(self, other): return self * other.inverse()
    def __neg__(self): return IntegerModP(-self.n)
    def __eq__(self, other): return isinstance(other, IntegerModP) and self.n == other.n
    def __abs__(self): return abs(self.n)
    def __str__(self): return str(self.n)
    def __repr__(self): return '%d (mod %d)' % (self.n, self.p)
    def __divmod__(self, divisor):
      q,r = divmod(self.n, divisor.n)
      return (IntegerModP(q), IntegerModP(r))
    def inverse(self):
     x,y,d = extendedEuclideanAlgorithm(self.n, self.p)
     return IntegerModP(x)
  IntegerModP.p = p
  IntegerModP.__name__ = 'Z/%d' % (p)
  return IntegerModP

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

def polygen(x,d):
  poly = [x]
  for i in range(0,d):
    poly.append(random.randrange(PMAX))
  return poly

def polyprint(p):
  print (p[0],end="")
  for i in range(1,len(p)):
    print(" + " + str(p[i]) + "x^" + str(i),end="")
  print()

def evalpolyat(p,x):
  # print(col.YLW + str(p) + col.RED + str(x) + col.BLN)
  s = p[0]
  for i in range(1,len(p)):
    s += (p[i]*pow(x,i))
  return s

def testAddition():
  allshares = []
  secretsum = 0
  for j in range(0,2):
    secret1 = random.randrange(PMAX)
    secretsum += secret1
    p1 = polygen(secret1,t)
    print(col.GRN + "p["+str(j)+"]: " + col.BLN + str(p1))
    # polyprint(p)
    shares = []
    for i in range(1,t+2):
      shares.append((i,evalpolyat(p1,i)))
    print(col.GRN + "p["+str(j)+"][j]: " + col.BLN + str(shares))
    allshares.append(shares)
    print()
  sumshares = []
  for i in range(0,t+1):
    sumshares.append((i+1,sum([x[i][1] for x in allshares])))
    # sumshares.append((i+1,sum([x[i][1] for x in allshares])))
  print(col.GRN + "s[j]: " + col.BLN + str(sumshares))
  print("~~~")
  lang = lagrange(sumshares)
  print(col.GRN + str(secretsum) + col.BLN)
  print(col.GRN + str(lang(0)) + col.BLN)

def vandermonde(arr):
  v = []
  for x in arr:
    vr = [1]
    for i in range(1,len(arr)):
      vr.append(x*vr[i-1])
    v.append(vr)
  v = matrix(v)
  # print(col.GRN + "V: \n" + col.BLN + str(v))
  return v

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
  # print(col.GRN + "P: \n" + col.BLN,end="")
  # nprint(a,5)
  return a

def genMatrixA(degree,parties):
  v = vandermonde(parties)
  p = diag(len(parties),degree)
  vp = v*p
  A = vp*(v**-1)
  print(col.GRN + "A: " + col.BLN + "\n" + nstr(A,5))
  return A
  # return dot(dot(v,p),inv(v))

def genShares(name,secret,t,parties):
  pg = polygen(secret,t)
  print(col.GRN + "num: " + col.BLN + str(pg))
  shares = []
  for p in parties:
    p.sshares[name] = (p.id,evalpolyat(pg,p.id) % PRIME)
    shares.append(p.sshares[name])
  print(col.GRN + "num[j]: " + col.BLN + str(shares))
  return shares

class Party:
  def __init__(self,id):
    self.id = id
    self.sshares = {}
    self.genranpoly = {}
    self.getranshares = {}
    self.vshares = {}
  def genRandomP(self,s1,s2,t):
    self.genranpoly[s1+"*"+s2] = polygen(0,t*2)
    # print(col.GRN + "r[i]: " + col.BLN + str(self.genranpoly))
  def sendRanShare(self,other,s1,s2):
    name=s1+"*"+s2
    s = evalpolyat(self.genranpoly[name],other.id)
    other.acceptRanShare(s,name)
    # print(col.GRN + "rshares[j]: " + col.BLN + str(s))
  def acceptRanShare(self,share,name):
    if name in self.getranshares.keys():
      self.getranshares[name].append(share)
    else:
      self.getranshares[name] = [share]
  def computeVShare(self,s1,s2,rp):
    name=s1+"*"+s2
    self.vshares[name] =  self.sshares[s1][1]*self.sshares[s2][1]
    self.vshares[name] += sum(self.getranshares[name])
    print(col.GRN + "v: " + col.BLN + str(self.vshares[name]))

def testMultiplication():
  print(col.CYN + str(t+1) + "-way secrets with degree t=" + str(t) + " polynomials among " + str(n) + " parties" + col.BLN)
  pids = random.sample(range(1,n*10),t*2+1)
  parties = [Party(x) for x in pids]
  print(col.MGN + "Parties: " + col.BLN + str(pids))
  #Generate and distribute shares of the two numbers we want to multiply
  p = random.randrange(SMAX)
  q = random.randrange(SMAX)
  secretprod = p*q
  genShares("p",p,t,parties)
  genShares("q",q,t,parties)
  #Generate a random polynomial with r(0) == 0 for each party
  [pa.genRandomP("p","q",t) for pa in parties]
  #Distribute the jth share of party i's r to party j
  [[i.sendRanShare(j,"p","q") for i in parties] for j in parties]
  #Compute the A matrix
  A = genMatrixA(t,pids)
  #Compute shares of the v matrix
  [pa.computeVShare("p","q",pids) for pa in parties]
  #Distribute the v matrix
  v = [pa.vshares["p*q"] for pa in parties]
  #Compute the shares of the new product
  s = [(pids[j],dot(A[j,:],v)) for j in range(0,len(pids))]
  print(col.GRN + "s: " + col.BLN + nstr(s,5))
  print(col.MGN + "Answer: " + col.GRN + "\n  " + str(secretprod) + col.BLN)
  print(col.MGN + str(len(pids)) + " Parties: " + col.GRN + "\n  " + str(int(nint(lagrange(s)(0)))%PRIME) + col.BLN)

def main():
  pass
  # mod23 = IntegersModP(23)
  # print(mod23(7).inverse())
  # print(mod23(7).inverse() * mod23(7))

  # testAddition()       #Addition
  testMultiplication() #Multiplication

if __name__ == "__main__":
  # execute only if run as a script
  main()
