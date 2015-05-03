#!/usr/bin/python
#-*- coding: utf-8 -*-
import sys
#definicion del problema DTLZ1
import problems.ProblemDTLZ1 as ProblemDTLZ1
import random
import platform
import datetime
#utilitarios de dominación
from commonModules.domination import *
#utilitario para log a la consola
from commonModules.simpleLogger import *
#utilitario para el thread de feedback
from commonModules.RepeatedTimer import *
#utilitario de dinujo
#from commonModules.plotUtils import *
#coneccion con la base de datos
import commonModules.Database as Database
import json
import time
#utilitarios de dibujo

# NSGA-II es el algoritmo de referencia

DEBUG = False	   #flag para imprimir datos de DEBUG
STORE = True 	   #indica si se va a guardar datos en la ejecucion del programa
FILE_STORE = True  #en caso de que STORE sea true, se indica que en lugar de guardar en DB se usan archivos
DB_CONN = False    #determina si el programa se conecta o no a la base de datos

def feedback(args):
	instance = args[0]
	if instance.stopCriteria == 'E':
		log("Generación -> " + 
			str(instance.currentGeneration) + 
			" (" + '{:3.2f}'.format(
				instance.problemInstance.qtyEvaluations /
				instance.evalLimit * 100.0) +
			"%)" + str(instance.problemInstance.qtyEvaluations)
		)
	else:
		log("Generación -> " + 
			str(instance.currentGeneration) + 
			" (" + '{:3.2f}'.format(
				(instance.evalLimit - (instance.future - time.time()))/
				instance.evalLimit * 100) + 
			"%)"
		)
#es cada uno de los vectores de solucion de NSGA2
class Solution:
	def __init__(self, N, M, problemEvalFunc):
		self.N = N				#cardinalidad del vector solucion
		self.M = M				#cantidad de objetivos
		self.objectives = []
		for _ in range(M):
			self.objectives.append(None)
		self.attributes = []
		self.rank = sys.maxint #INFINITO
		self.distance = 0.0
		#funcion de evaluacion del problema
		self.problemEvalFunc = problemEvalFunc

	def evaluateFitness(self):
		self.objectives = self.problemEvalFunc(self.attributes, self.M)

	# realiza el la operación de cruzamiento entre esta solución y otra
	# @param otherParent = otra solución con la cual producir hijos
	def crossover(self, otherParent):
		children = Solution(self.N, self.M, self.problemEvalFunc)
		slicePoint = random.randint(0,self.N - 1)
		#children.attributes.extend(self.attributes[:slicePoint])	
		#children.attributes.extend(otherParent.attributes[slicePoint:])	
		children.attributes.extend(self.attributes[:self.N/2])	
		children.attributes.extend(otherParent.attributes[self.N/2:])	
		return children

	def mutate(self):
		self.attributes[random.randint(0,self.N - 1)] = random.random()

	# genera una lista de popSize soluciones de cardinalidad N para NSGA-II 
	# a partir del problema dado
	# @param N = cardinalidad del vector de espacio de búsqueda
	# @param M = cantidad de objetivos
	# @param popSize = tamaño de la población
	# @param generateRandomSolution = función que según el problema crea una solucion 
	#	en espacio de búsqueda
	# @param problemEvalFunc = función de evaluación del problema
	@staticmethod
	def generateFirstPopulation(N, M, popSize, generateRandomSolution, problemEvalFunc):
		#se instancian varias soluciones de NSGA-II
		solutionList = []
		for i in range (popSize):
			rawSolution = generateRandomSolution(N)
			tempSolution = Solution(N,M,problemEvalFunc)
			for j in range(N):
				tempSolution.attributes.append(rawSolution[j])
			solutionList.append(tempSolution)
		return solutionList

	def __str__(self):
		return  "N = " + str(self.N) + "\nobjectives = " + str(self.objectives) + "\nattributes = " + str(self.attributes) + "\nrank = " + str(self.rank) + "\ndistance = " + str(self.distance)


		
#implementacion del algortimo NSGA-II
class NSGAII:
	def __init__(self,
				 VectorCardinality,
				 numObjectives, 
				 mutationRate,
				 crossoverRate,
				 PopSize,
				 EvalLimit,
				 ProblemInstance,
				 StopCriteria,
				 Folder = None
	):
		self.N = VectorCardinality
		self.M = numObjectives
		self.mutationRate = mutationRate
		self.crossoverRate = crossoverRate
		self.popSize = PopSize
		self.evalLimit = EvalLimit
		self.problemInstance = ProblemInstance
		self.stopCriteria = StopCriteria
		self.currentGeneration = 1
		self.future = 0
		self.execTime = 0
		self.folder = Folder
		random.seed()

		self.simulation = None

	#compara dos soluciones utilizando el "crowded-comparison operator" 
	#retorna mayor a cero si s_i <_n s_j
	def crowdedComparison(self, s_i, s_j):
		if s_i.rank < s_j.rank:
			return 1
		elif s_i.rank > s_j.rank:
			return -1
		elif s_i.distance > s_j.distance:
			return 1
		elif s_i.distance < s_j.distance:
			return -1
		return 0

	#algoritmo de ordenamiento de soluciones de NSGA-II
	def fastNonDominatedSort(self, P):
		F = {} #conjunto de frentes
		F[1] = [] #inicializamos el primer frente
		S = {} #conjunto de soluciones dominadas
		n = {} #conjunto de contadores de dominacion
		for p in P: #para cada solución en P
			S[p] = [] #Soluciones dominadas por p = vacio
			n[p] = 0  #Contador de soluciones que dominan a p = 0
			for q in P: #para las demas soluciones (p se ignora
				#implicitamente, ya que una solución no puede
				#dominarse a sí misma
				if isDominatedBy(p.objectives,q.objectives):
					S[p].append(q)        #se añade q al set de soluciones dominadas por p
				elif isDominatedBy(q.objectives,p.objectives):
					n[p] += 1             #se incrementa el contador de dominación de p
			if n[p] == 0: 
				p.rank = 0
				F[1].append(p) #p pertenece al primer frente

		i = 1
		#se ordenan los demas frentes pasando soluciones a los frentes siguientes
		while len(F[i]) != 0:#mientras el frente actual tenga soluciones
			Q = [] #se usa para guardar los miembros del siguiente frente
			for p in F[i]: #para todas las soluciones en el frente actual
				for q in S[p]: #para todas las soluciones dominadas
					#por la solución actual
					n[q] -= 1 #se resta el contador de dominación de
							#la solución dominada
					if n[q] == 0: #si su contador es cero
						q.rank = i+1
						Q.append(q) #se añade la solución dominada al
									#siguiente frente
			i+=1
			F[i] = Q
		return F
	#quick-sort usando "crowding-comparison operator" como criterio de ordenamiento
	def crowdingQuickSort(self, P):
		if P == []:
			return []
		else:
			pivot = P[0]
			lesser = self.crowdingQuickSort([x for x in P[1:] if self.crowdedComparison(x,pivot) < 0])
			greater = self.crowdingQuickSort([x for x in P[1:] if self.crowdedComparison(x,pivot) >= 0])
			return lesser + [pivot] + greater
	#quick-sort usando el objetivo como criterio de ordenamiento
	def objectiveQuickSort(self, P, index):
		if P == []:
			return []
		else:
			pivot = P[0]#TODO, ver si es conveniente elegir otro pivot
			lesser = self.objectiveQuickSort([x for x in P[1:] if x.objectives[index] < pivot.objectives[index]],index)
			greater = self.objectiveQuickSort([x for x in P[1:] if x.objectives[index] >= pivot.objectives[index]],index)
			return lesser + [pivot] + greater
		

	#ordena las soluciones de un frente con respecto al "crowding-comparison operator"
	def sortByCrowding(self, P):
		return self.crowdingQuickSort(P)
		
	#wrapper para poder configurar el algoritmo de ordenamiento deseado
	def sortByObjective(self, P, objIndex):
		return self.objectiveQuickSort(P, objIndex)

	def crowdingDistanceAssignment(self, I):
		for i in I:#se ceran todas las distancias del frente dado
			i.distance = 0; 
		for objective in range(self.M):#para cada objetivo
			#se ordena el frente dado con respecto a el objetivo actual
			I = self.sortByObjective(I, objective)
			#se asigna INFINITO como distancias de las soluciones de los extremos
			I[0].distance = I[len(I) - 1].distance = float('inf')
			#al resto de las soluciones se les asigna un "promedio" del cuboide para esta solucion
			for i in range(1, len(I) - 1):
				if (I[len(I) - 1].objectives[objective] - I[0].objectives[objective]) != 0:
					I[i].distance += (I[i + 1].objectives[objective] -  I[i - 1].objectives[objective])/(I[len(I) - 1].objectives[objective] - I[0].objectives[objective])        

	# crea una nueva población Q, descendiente de P
	# @param P = Población Ancestro 
	def makeNewPop(self,P):
		Q = []

		while len(Q) != len(P):
			selectedSolutions = [None, None]

			while selectedSolutions[0] == selectedSolutions[1]:
				for i in range(2):
					s1 = random.choice(P)
					s2 = s1
					while s1 == s2:
						s2 = random.choice(P)
					if self.crowdedComparison(s1, s2) > 0:
						selectedSolutions[i] = s1
					else:
						selectedSolutions[i] = s2

			if random.random() < self.crossoverRate:
				child_solution = selectedSolutions[0].crossover(selectedSolutions[1])
				if random.random() < self.mutationRate:
					child_solution.mutate()

					child_solution.evaluateFitness()

					Q.append(child_solution)

		return Q

	#algoritmo principal
	#P               -> generacion inicial
	def run(self, P):
		self.future = time.time() + self.evalLimit

		if STORE:
			self.storeSimulation()

		self.future = time.time() + self.evalLimit
		for s in P:
			s.evaluateFitness();
		Q = []
		self.currentGeneration = 0 #para contar la cantidad de generaciones logradas
		while True:
			self.currentGeneration+=1
			print "current generation: " + str(self.currentGeneration)
			R = []
			R.extend(P)
			R.extend(Q)
			
			F = self.fastNonDominatedSort(R)
			del P[:]
			i = 1
			while ( i < len(F) ) and (len(P) + len(F[i]) <= self.popSize):
				self.crowdingDistanceAssignment(F[i])
				P.extend(F[i])
				i+=1
			if(len(P) < self.popSize):
				self.crowdingDistanceAssignment(F[i])
				auxFront = self.sortByCrowding(F[i])
				P.extend(auxFront[:(self.popSize - len(P))])

			if STORE:
				self.storePopulation(P)

			Q = self.makeNewPop(P)
			#condición de parada
			if self.stopCriteria == 'E':
				if(self.problemInstance.qtyEvaluations >= self.evalLimit):
					print "evaluaciones realizadas: " + str(self.problemInstance.qtyEvaluations)
					break
			else:
				if(time.time() > self.future):
					print "evaluaciones realizadas: " + str(self.problemInstance.qtyEvaluations)
					break

		if STORE:
			#actualizamos la base de datos con el tiempo de finalización de la simulación
			self.simulation.endTime = datetime.datetime.now()
			if FILE_STORE:
				self.simulation.storeToFile(self.folder)
			else:
				db.updateSimulation(self.simulation)

	def configurationString(self):
		configuration = "N = " + str(self.N)
		configuration += ", M = "+str(self.M)
		configuration += ", popSize = " + str(self.popSize)
		configuration += ", evalLimit = "+str(self.evalLimit)
		configuration += ", mutationRate = "+str(self.mutationRate)
		configuration += ", crossoverRate = "+str(self.crossoverRate)

		return configuration

	#param P -> poblacion a guardar
	def storePopulation(self, P):
		#se guarda en la base de datos la población de esta iteración
		population = Database.Population(0.0, False, self.simulation.id, self.currentGeneration)
		if not FILE_STORE:
			db.insertPopulation(population,self.simulation)

		for s in P:
			#solution = Database.Solution(s.N, s.M, cPickle.dumps(s.attributes), cPickle.dumps(s.objectives), 0, s.rank, s.distance, population.id)
			solution = Database.Gene(s.N, s.M, s.attributes, s.objectives, 0, s.rank, s.distance, population.id )
			if FILE_STORE:
				population.addGene(solution)
			else:
				db.insertGene(solution,population)

		if FILE_STORE:
			self.simulation.addPopulation(population)

	def storeSimulation(self):
		#se guarda en la base de datos la primera población
		configuration = self.configurationString()

		command = str(sys.argv[0])
		for param in sys.argv[1:]:
			command += " " + param

		self.simulation = Database.Simulation(
			-1.0,
			platform.uname(),
			datetime.datetime.now(),
			datetime.datetime.now(),
			"NSGA-II",
			configuration,
			command
		)
		if not FILE_STORE:
			db.insertSimulation(self.simulation)

#conección con la base de datos para guardar las simulaciones
if DB_CONN:
	db = Database.Database('tesis','torresmateo','a')

if __name__ == "__main__":
	#inicio del programa
	if len(sys.argv) < 8:
		print "Forma de Uso:" 
		print "\t" + sys.argv[0] + " <M> <n> <popSize> <crossoverRate> <mutationRate> <qtyGen>"
		print "\n\tM = \t\t(entero positivo) cantidad de objetivos" 
		print "\n\tn = \t\t(entero positivo) cantidad de elementos en el vector" 
		print "\n\tpopSize = \t(entero positivo) tamaño de la población" 
		print "\n\tcrossoverRate = (real positivo [0:1]) probabilidad de crossover" 
		print "\n\tmutationRate = \t(real positivo [0:1]) probabilidad de mutación" 
		print "\n\ts = \t(real positivo) cantidad de segundos de ejecución" 
		print "\n\tstopCriteria = \t\t'T' para indicar tiempo 'E' para indicar ejecuciones"
		exit(0)

	#se copian los parámetros y se validan
	numObjectives = int(sys.argv[1])
	vectorCardinality = int(sys.argv[2])
	popSize = int(sys.argv[3])
	crossoverRate = float(sys.argv[4])
	mutationRate = float(sys.argv[5])
	evalLimit = float(sys.argv[6])
	stopCriteria = str(sys.argv[7])


	if(numObjectives <= 0):
		print "el número de objetivos debe ser positivo"
		exit(0)
	if(vectorCardinality <= 0):
		print "la cardinalidad del vector debe ser positivo"
		exit(0)
	if(numObjectives + 1 > vectorCardinality):
		print "el número de objetivos debe ser menor a la cardinalidad del vector"
		exit(0)
	if(crossoverRate > 1.0 or crossoverRate < 0.0):
		print "la probabilidad de crossover debe ser un número real entre 0.0 y 1.0"
		exit(0)
	if(mutationRate > 1.0 or mutationRate < 0.0):
		print "la probabilidad de mutación debe ser un número real entre 0.0 y 1.0"
		exit(0)
	if(popSize <= 0):
		print "la cardinalidad de la población debe ser positiva"
		exit(0)
	if(evalLimit <= 0):
		print "el límite de evaluaciones debe ser positivo"
		exit(0)
	if stopCriteria not in ['T','E']:
		print "el criterio de  parada no fue definido correctamente"
		exit(0)

	#seguridad para evitar que el programa falle por limite de recursividad con muchas
	#dimensiones
	sys.setrecursionlimit(popSize * 3)

	problem = ProblemDTLZ1.ProblemDTLZ1()
	#se genera la primera población
	initialPopulation = Solution.generateFirstPopulation(vectorCardinality, numObjectives, popSize, problem.DTLZ1_generateRandomSolution, problem.DTLZ1_HI)
	#se prepara el objeto NSGA con los parámetros proveídos
	#'''
	n = NSGAII(
		vectorCardinality,
		numObjectives,
		mutationRate,
		crossoverRate,
		popSize,
		evalLimit,
		problem,
		'T',
		Folder = None
	)
	#se inicializa el timer de feedback
	rt = RepeatedTimer(1.0, feedback,[n])
	#se ejecuta el algoritmo
	n.run(initialPopulation)
	#para asegurar la finalización de la ejecución del programa, se finalizan todos los threads
	#de feedback
	rt.stop()
