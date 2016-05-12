Python Implementation of Shamir's Secret Sharing using the BGW Protocol
Author: Patrick Crain

----------

Usage:

All of the code in the project is in two main files: pyshamir.py contains the bulk of the logic, the Party class functions, and a bunch of auxilliary functions for the code. party.py contains the main program logic and high level protocols used for secure computation. Multiple instances of the party.py scripts are executed to actually carry out the computations; the "tester" shell script carries out these executions by automatically launching 10 party.py instances with ids 0-9

When a party.py instance is loaded, it does three things.  First, it looks for file in the current directory named "parties.json" and loads a list of party ids from it, assigning itself the nth id in the list, where n is the number passed to the invocation on the command line.  Second it looks for a file called "known-secrets/[id]/secrets.json" (where [id] is the party's id) in the current directory, and loads any secrets known to the party. Third, it looks for a file called "comps.json" in the current directory; it uses this file to determine the computations to carry out. The file consists of an array of commands to carry out, using the following notation:

  |["n"]|             |The party who knows the secret "n" distributes shares of it to all parties in the computation|
  |["n",[]]           |All parties compute n from their shares (output is in yellow)|
  |["n",[a,b]]        |Parties with ids a and b compute n from their shares (output is in cyan)|
  |["n",<op>,"p","s"] |All parties perform computation <op> on shares of "n" and "p" and save the new share as "s".  <op> is one of "+" (addition), "-" (subtraction), or "*" (multiplication)|
  |["n",<op>,c,"s"]   |All parties perform computation <op> on shares of "n" and the constant c and save the new share as "s".  <op> is one of "+" (addition), "-" (subtraction), or "*" (multiplication)|
