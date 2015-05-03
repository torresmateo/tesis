#!/usr/bin/python
#-*- coding: utf-8 -*-

# módulo con funciones utiles para determinar si un vector domina a otro
# se asume minimización

# determina si el vector A domina al vector B
# @return boolean = True si A domuna a B, False en caso contrario
def isDominatedBy(A,B):
	equalQty = 0
	lowerQty = 0
	for i in range(len(A)):
		if A[i] < B[i]:
			lowerQty += 1
		elif A[i] == B[i]:
			equalQty += 1
		else:
			return False
	if lowerQty >= 1:
		return True
	return False
	
# determina si algun vector del conjunto A domina al vector B
# @return boolean
def isDominatedBySet(A,B):
	for V in A:
		if isDominatedBy(V,B):
			return True
	return False

# @return List = indices de los vectores en A dominados por B
def getDominatedElements(A,B):
	indexList = []
	for V in A:
		if isDominatedBy(B,V):
			indexList.append(A.index(V))
	return indexList;


#dados dos conjuntos A y B, retorna los elementos de A que dominados por algun elemento de B
#se asume que cada conjunto es no dominado en si mismo
def extractDominated(A,B):
	dominated = []
	for b in B:
		for a in A:
			if isDominatedBy(b,a) and not( a in dominated ):
				dominated.append(a)
	return dominated

#dados dos conjuntos A y B, retorna los elementos de A que dominan a algun elemento de B
#se asume que cada conjunto es no dominado en si mismo
def extractDominance(A,B):
	dominance = []
	for a in A:
		for b in B:
			if isDominatedBy(a,b):
				dominance.append(a)
				break
	return dominance

#dado un conjunto A de soluciones, devuelve el conjunto no dominado de soluciones
def getNonDominatedSet(A):
	B = A[:]
	return [b for b in B if not isDominatedBySet(A, b)]
