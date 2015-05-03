__author__ = 'torresmateo'

import math

def dotProduct(vector1, vector2):
	if len(vector1) != len(vector2):
		print "can't perform dot product on different length vectors"
		return
	return sum([a*b for a,b in zip(vector1,vector2)])

def norm(vector):
	return math.sqrt(sum([a*a for a in vector]))

def add(vector1, vector2):
	return [a+b for a,b in zip(vector1, vector2)]

def sub(vector1, vector2):
	return [a-b for a,b in zip(vector1, vector2)]

def mul(vector1, scalar):
	return [a*scalar for a in vector1]

def div(vector1, scalar):
	if scalar is 0:
		print "can't divide a vector by zero"
		return
	return [a/scalar for a in vector1]

def getUnitary(vector):
	vecNorm = norm(vector)
	return div(vector,vecNorm)

def projection(vector1, vector2):
	#second vector can't be the zero vector
	if vector2.count(vector2[0]) == len(vector2) and vector2[0] is 0:
		#all elements in vector are the same and zero
		print "error, can't project a vector onto vector zero"
		return

	u = getUnitary(vector2)
	return mul(u, dotProduct(vector1, vector2))

