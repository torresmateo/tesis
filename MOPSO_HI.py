#!/usr/bin/python
#-*- coding: utf-8 -*-
import sys
import problems.ProblemDTLZ1 as ProblemDTLZ1
import random
import platform
import datetime
from commonModules.domination import *
from commonModules.simpleLogger import *
from commonModules.RepeatedTimer import *
#from commonModules.plotUtils import *
import commonModules.Database as Database
import json
import copy
import time
import numpy
import math
# MOPSO es el algoritmo de referencia
# version independiente del hardware
import pprint

DEBUG = False	   #flag para imprimir datos de DEBUG
PLOT = False	   #flag para generar graficos (EN DESUSO)
STORE = True 	   #indica si se va a guardar datos en la ejecucion del programa
FILE_STORE = True  #en caso de que STORE sea true, se indica que en lugar de guardar en DB se usan archivos
DB_CONN = False    #determina si el programa se conecta o no a la base de datos



def feedback(args):
	instance = args[0]
	if instance.stopCriteria == 'E':
		log("Iteración -> " +
			str(instance.currentIteration) +
			" (" + '{:3.2f}'.format(
				instance.problemInstance.qtyEvaluations/
				instance.evalLimit * 100.0) +
			"%) gBest = " + str(len(instance.globalBest.particles))
		)
	else:
		log("Iteración -> " +
			str(instance.currentIteration) +
			" (" + '{:3.2f}'.format(
				(instance.evalLimit - (instance.future - time.time()))/
				instance.evalLimit * 100) +
			"%) gBest = " + str(len(instance.globalBest.particles))
		)


#repositorio de partículas
class ParticleRepo:
	def __init__(self,N,M,QtyParticles, deleteCriteria = None, selectCriteria = None):
		#cantidad de dimensiones de la partícula
		self.N = N							
		#cantidad de objetivos
		self.M = M							
		#cantidad máxima de partículas soportadas por el repositorio
		self.qtyParticles = QtyParticles
		#lista de soluciones encontradas	
		self.particles = []				
		#método de eliminación de partículas
		self.deleteCriteria = deleteCriteria
		#se ve que estrucuta de datos usar para el criterio de borrado segun la opcion utilizada
		if self.deleteCriteria is "crowding":
			#distancias partícula a partícula
			self.crowdingMatrix = {}
			#suma de las distancias (factor de crowding)
			self.crowdingDistances = {}
		#criterio de seleccion, por dedfecto es random
		self.selectCriteria = selectCriteria
		if self.selectCriteria is "roulette":
			self.totalFitness = 0
			self.relativeFitness = []
			self.probabilities = []

	def squaredEuclideanDistance(self, a, b):
		#por cada objetivo
		distance = 0
		for i in range(self.M):
			distance += (a.objectives[i] - b.objectives[i]) ** 2
		return distance

	#agrega la paricula particle al calculo del crowding para cada particula del repositorio
	#se utiliza la distancia euclidiana al cuadrado como representante de la distancia de una partícula a otra
	def crowdingAssignment(self):
		#como el método utilizado para agregar las partículas es append, la partícula
		#que debe calcularse es siempre la última

		#el factor de crowding para la particula recien insertada empieza en 0
		self.crowdingDistances[self.particles[-1]] = 0
		#se actualiza la información de las partículas existentes
		for i in range(0,len(self.particles) -1):
			#se agrega la distanncia particula a particula
			self.crowdingMatrix[(self.particles[i], self.particles[-1])] = \
				self.squaredEuclideanDistance(self.particles[i], self.particles[-1])
			#se actualiza el factor de crowding de ambas partículas
			self.crowdingDistances[self.particles[i]] += self.crowdingMatrix[
				(self.particles[i], self.particles[-1])
			]
			self.crowdingDistances[self.particles[-1]] += self.crowdingMatrix[
				(self.particles[i], self.particles[-1])
			]

	def compareCrowdingInformation(self):
		keys = self.crowdingDistances.keys()
		wat = [x for x in keys if x not in self.particles]
		print wat


	#elimina de la matriz de crowding los elementos relacionados a la partícula particle
	def deleteCrowdingInformation(self, particle):
		deleteIndexes = [(q,p) for q,p in self.crowdingMatrix
						 if q is particle or p is particle]
		for i,j in deleteIndexes:
			#se actualiza el factor de crowding de la partícula que no se borra del
			# repositorio
			if i is particle:
				self.crowdingDistances[j] -= self.crowdingMatrix[(i,j)]
			else:
				self.crowdingDistances[i] -= self.crowdingMatrix[(i,j)]
			del self.crowdingMatrix[(i,j)]
		del self.crowdingDistances[particle]

	#agrega una partícula al repositorio
	def add(self,particle, isGlobalRep = False):
		#se realiza una copia del elemento en el repositorio, de tal manera que al 
		#actualizar el pool de partículas la información no se pierda en el repositorio 
		#y de cualquier manera podamos acceder al objeto y sus métodos
		
		#si el repositorio está lleno, se elimina una partícula del mismo
		#if len(self.particles) >= self.qtyParticles: and not isGlobalRep:
		if len(self.particles) >= self.qtyParticles:# and not isGlobalRep:
			#print "del"
			#@TODO: elegir mejor la partícula que se va a eliminar
			if self.deleteCriteria is "crowding":
				#seleccionar la partícula más crowded (minima distancia al resto de las particulas)
				#eliminar esa particula
				index = self.particles.index(
					min(
						self.crowdingDistances.iterkeys(),
						key=lambda x: self.crowdingDistances[x]
					)
				)
				self.deleteCrowdingInformation(self.particles[index])
				del self.particles[index]
				print index

				#se deben eliminar los elementos del crowing para esta partícula
			else:
				del self.particles[random.randint(0,len(self.particles) - 1)]


		self.particles.append(
			Particle(
				particle.N, 
				particle.M, 
				particle.vMax, 
				particle.pos, 
				particle.vel, 
				particle.objectives
			)
		)
		if self.deleteCriteria is "crowding":
			self.crowdingAssignment()


	#determina si una partícula dada es dominada por algún elemento del repositorio
	def dominates(self,particle):
		if len(self.particles) > 0: 
			return isDominatedBySet(
				[p.objectives for p in self.particles], 
				particle.objectives
			)
		else:
			return False

	def updateRoulette(self):
		if self.selectCriteria is 'roulette' and self.deleteCriteria is 'crowding':
			self.totalFitness = float(sum(self.crowdingDistances.values()))
			self.relativeFitness = [(f[0],f[1]/self.totalFitness) for f in self.crowdingDistances.iteritems()]
			self.probabilities = [(self.relativeFitness[i][0],sum(x[1] for x in self.relativeFitness[:i+1]))
							  for i in range(len(self.relativeFitness))]


	#retorna la partícula que es considerada la mejor del repositorio
	def selectBest(self):
		#@TODO implementar otras opciones de selección
		if self.selectCriteria is 'roulette' and self.deleteCriteria is 'crowding':
			r = random.random()
			for i in range(len(self.probabilities)):
				if r <= self.probabilities[i][1]:
					return self.probabilities[i][0]
		else:
			return self.particles[random.randint(0,len(self.particles) -1)]

	#elimina del repositorio todos los elementos que sean dominados por algun 
	#elemento del mismo se asume que la última partícula insertada es particle
	def removeDominatedElements(self, particle, globalBest = False):
		#p para todo p en el repositorio tal que no es dominado por particle


		if self.deleteCriteria is "crowding":
			nonDominatedElements = [
				p for p in
				self.particles if
				not isDominatedBy(particle.objectives, p.objectives)
			]
			removeElements = [item for item in self.particles if item not in nonDominatedElements]

			#se elimina la informacion de crowding
			for particle in removeElements:
				self.deleteCrowdingInformation(particle)

		self.particles = [
			p for p in
			self.particles if
			not isDominatedBy(particle.objectives, p.objectives)
		]



#partícula
class Particle:
	def __init__(
			self, 
			N,
			M,
			VMax,
			pos = None, 
			vel = None, 
			objectives = None, 
			QtyParticles = 1,
			problemEvalFunc = None,
			generateRandomSolution = None,
			SpecialDistributionNDiv = 0,
			SpecialDistributionIndex = 0
	):
		#variables de configuración
		self.vMax = VMax				#velocidad máxima
		self.N = N						#cantidad de dimensiones de la partícula
		self.M = M						#cantidad de objetivos
		self.objectives = []			#vector de evaluación de la partícula
		self.pos = []					#vector posición
		self.vel = []					#vector de velocidad
		self.qtyParticles = QtyParticles
		self.problemEvalFunc = problemEvalFunc
		self.generateRandomSolution = generateRandomSolution

		#el constructor se utilizará de dos maneras:
		#	para crear instancias de ejecución
		#	para crear instancias simples (que serán guardadas en los repositorios)
		#		si no se define la posición, se crea la instancia normalmente, 
		#		de lo contrario, se evita el
		#		overhead de crear repositorios sin sentido
		if pos is None:
			#variables de ejecución
			#repositorio local de mejores soluciones encontradas
			self.localBest = ParticleRepo(self.N, self.M, self.qtyParticles)		

			#se inicializan los vectores
			for _ in range(self.M):
				self.objectives.append(None)
			#@TODO, verificar si esto es correcto, la idea es que las posiciones esten 
			#si o si situadas dentro de los boundaries del problema
			if SpecialDistributionNDiv > 0:
				rawSolution = self.generateRandomSolution(self.N, SpecialDistributionNDiv, SpecialDistributionIndex)
			else:
				rawSolution = self.generateRandomSolution(self.N)

			for i in range(self.N):
				self.pos.append(rawSolution[i])
				self.vel.append(random.uniform(-VMax,VMax))
			self.evaluate()
			self.updateLocalBest()
		#en caso en que la posición ya esté definida se crea una instancia simple
		else:
			self.pos = copy.deepcopy(pos)
			self.vel = copy.deepcopy(vel)
			self.objectives = copy.deepcopy(objectives)
	#asigna el valor de la función objetivo con la posición actual
	def evaluate(self):
		#TODO, implementar otros problemas aparte de DTLZ1
		self.objectives = self.problemEvalFunc(self.pos, self.M)

	#verifica si la configuración actual debe incluirse en el repositorio de 
	#mejores soluciones locales y actualiza el repositorio si es necesario
	def updateLocalBest(self):
		if not self.localBest.dominates(self):
			self.localBest.add(self)
			self.localBest.removeDominatedElements(self)

	#calcula la siguiente configuración de la partícula
	def step(self, gBest, lBest, Inertia, C1, C2):
		#para cada componente
		#reboteCount = 0
		for i in range(self.N):
			self.vel[i] = (Inertia * self.vel[i] +
						  C1 * random.random() * (gBest.pos[i] - self.pos[i]) +
						  C2 * random.random() * (lBest.pos[i] - self.pos[i]))
			#si la velocidad supera los límites, se restringe la velocidad al
			#límite alcanzado
			if self.vel[i] > self.vMax:
				self.vel[i] = self.vMax
			elif self.vel[i] < -self.vMax:
				self.vel[i] = -self.vMax
			#se actualiza la posición de la componente
			self.pos[i] += self.vel[i]

			#@TODO: verificar boundaries dependiendo del problema, 
			#esto es válido para DTLZ1, 
			#sin embargo no es necesariamente válido para otros problemas.

			#si la componente sale de los límites, se vuelve a insertar al espacio de 
			#búsqueda y se cambia el sentido de la velocidad en esta componente
			if self.pos[i] < 0:
				self.pos[i] = (1 - (self.pos[i] - math.floor(self.pos[i])))
				self.vel[i] *= -1
			elif self.pos[i] > 1:
				self.pos[i] =  (math.ceil(self.pos[i]) - self.pos[i])
				self.vel[i] *= -1
		#print "cantidad de rebotes = " + str(reboteCount)

class MOPSO:
	def __init__(self, C1, C2, Inertia, VMax, QtyParticles, N, M,
				 problemEvalFunc, generateRandomSolution, problemInstance,
				 EvalLimit = 0, StopCriteria = None, DeleteCriteria = None,
				 Folder = None, SelectCriteria = None,
				 SpecialDistribution = False, SpecialDistributionNDiv = 2,
				 SpecialDistributionForceMultiple = False):
		#variables de configuración
		self.C1 = C1 						#parámetro cognitivo
		self.C2 = C2 						#parámetro social
		self.inertia = Inertia 				#parámetro de inercia
		self.vMax = VMax 					#velocidad máxima
		self.qtyParticles = QtyParticles	#cantidad de partículas
		self.N = N							#cardinalidad de partículas
		self.M = M							#cantidad de objetivos
		self.currentIteration = 1			#iteración actual del loop
		self.evalLimit = EvalLimit			#tiempo de ejecución
		self.problemEvalFunc = problemEvalFunc
		self.generateRandomSolution = generateRandomSolution
		self.problemInstance = problemInstance
		self.specialDistribution = SpecialDistribution
		self.specialDistributionNDiv = SpecialDistributionNDiv
		self.specialDistributionForceMultiple = SpecialDistributionForceMultiple
		#variables de ejecución
		#pool de partículas
		self.particles = []	
		#repositorio de mejores soluciones globales
		self.deleteCriteria = DeleteCriteria
		self.selectCriteria = SelectCriteria
		self.globalBest = ParticleRepo(
			self.N,
			self.M,
			self.qtyParticles,
			self.deleteCriteria,
			self.selectCriteria
		)
		self.simulation = None
		self.stopCriteria = StopCriteria
		self.future = None
		self.folder = Folder

	def initialiseParticlePool(self):
		#se inicializa el pool de partículas
		for i in range(self.qtyParticles):
			#se genera una partícula con posición y velocidad iniciales randomizadas
			if self.specialDistribution:
				p = Particle(
					self.N,
					self.M,
					self.vMax,
					QtyParticles = self.qtyParticles,
					problemEvalFunc = self.problemEvalFunc,
					generateRandomSolution = self.generateRandomSolution,
					SpecialDistributionNDiv= self.specialDistributionNDiv,
					SpecialDistributionIndex=i
				)
			else:
				p = Particle(
					self.N,
					self.M,
					self.vMax,
					QtyParticles = self.qtyParticles,
					problemEvalFunc = self.problemEvalFunc,
					generateRandomSolution = self.generateRandomSolution
				)
			#se incluye la partícula generada en el pool
			self.particles.append(p)
			#se actualiza el repositorio global
			self.updateGlobalBest(p)


	#verifica si la partícula dada debe incluirse en el repositorio de 
	#mejores soluciones globales y actualiza el repositorio si es necesario
	def updateGlobalBest(self,particle):
		if not self.globalBest.dominates(particle):
			self.globalBest.add(particle, isGlobalRep=True)
			self.globalBest.removeDominatedElements(particle, True)

	#loop principal
	def run(self):
		self.initialiseParticlePool()
		self.future = time.time() + self.evalLimit

		if STORE:
			self.storeSimulation()
			self.storePopulation()
		if PLOT:
			print "plot disabled"
			#plotInitForMOPSO(fig,ax,im)
		#condición de parada, tiempo
		while True:
			self.currentIteration += 1
			#en caso de que sea necesario, se actualiza la informacion de la ruleta
			self.globalBest.updateRoulette()
			#para cada partícula
			for i in range(self.qtyParticles):
				#se recupera el mejor global
				gBest = self.globalBest.selectBest()
				#se recupera el mejor local de la partícula
				lBest = self.particles[i].localBest.selectBest()
				#la partícula avanza 
				self.particles[i].step(gBest, lBest, self.inertia, self.C1, self.C2)
			#para cada partícula 
			for i in range(self.qtyParticles):
				#se evalúa la partícula con la función objetivo
				self.particles[i].evaluate()
				#se actualiza el repositorio global
				self.updateGlobalBest(self.particles[i])
				#se actualiza el repositorio global de la partícula
				self.particles[i].updateLocalBest()
			
			if STORE:
				self.storePopulation()
			if PLOT:
				print "plot disabled"
				#plotForMOPSO(p, fig, ax, im)
			#condición de parada
			if self.stopCriteria == 'E':
				if self.problemInstance.qtyEvaluations >= self.evalLimit:
					break
			else:
				if time.time() > self.future:
					break
		print "currentIteration = " + str(self.currentIteration)
		if STORE:
			#actualizamos la base de datos con el tiempo de finalización de la simulación
			self.simulation.endTime = datetime.datetime.now()
			if FILE_STORE:
				self.simulation.storeToFile(self.folder)
			else:
				db.updateSimulation(self.simulation)
		

		# print self.currentIteration
		# print len(self.globalBest.particles)
		# for p in self.globalBest.particles:
		# 	print sum(p.objectives)
		# for p in self.globalBest.particles:
		# 	print p.pos

	def storePopulation(self):
		#se guarda en la base de datos la colección de ṕartículas inicial
		population = Database.Population(0.0, False, self.simulation.id, self.currentIteration)
		if not FILE_STORE:
			db.insertPopulation(population,self.simulation)
		
		for p in self.globalBest.particles:
			part = Database.Particle(p.N, p.M, p.pos, p.vel, p.objectives, population.id )
			if FILE_STORE:
				population.addParticle(part)
			else:
				db.insertParticle(part,population)

		if FILE_STORE:
			self.simulation.addPopulation(population)

	def configurationString(self):
		configuration = "N = " + str(self.N)
		configuration += ", M = "+str(self.M)
		configuration += ", qtyParticles = " + str(self.qtyParticles)
		configuration += ", evalLimit = "+str(self.evalLimit)
		configuration += ", C1 = "+str(self.C1)
		configuration += ", C2 = "+str(self.C2)
		configuration += ", inertia = "+str(self.inertia)
		configuration += ", vMax = "+str(self.vMax)
		configuration += ", deleteCriteria = "+str(self.deleteCriteria)
		configuration += ", selectCriteria = "+str(self.selectCriteria)
		configuration += ", problem = "+str(self.problemInstance.getProblemDescription())
		return configuration


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
			"MOPSO", 
			configuration, 
			command
		)
		if not FILE_STORE:
			db.insertSimulation(self.simulation)


#conección con la base de datos para guardar las simulaciones
if DB_CONN:
	db = Database.Database('tesis','torresmateo','a')

if __name__ == "__main__":
	if len(sys.argv) < 10:
		print "Forma de Uso:" 
		print "\t" + sys.argv[0] + "<M> <N> <C1> <C2> <inertia> <vMax> <qtyParticles> <evalLimit>"
		print "\n\tM = \t\t(entero positivo) cantidad de objetivos"
		print "\n\tN = \t\t(entero positivo) cantidad de elementos del vector"
		print "\n\tC1 = \t\tparámetro cognitivo"
		print "\n\tC2 = \t\tparámetro social" 
		print "\n\tinertia = \t\tparámetro de inercia"
		print "\n\tvMax = \t\tvelocidad máxima"
		print "\n\tqtyParticles = \t\t(entero )cantidad de partículas"
		print "\n\tevalLimit = \t\t(entero positivo)cantidad límite de evaluaciones o tiempo límite"
		print "\n\tstopCriteria = \t\t'T' para indicar tiempo 'E' para indicar ejecuciones"
		exit(0)

	#se copian los parámetros y se validan
	numObjectives = int(sys.argv[1])
	vectorCardinality = int(sys.argv[2])
	cognitive = float(sys.argv[3])
	social = float(sys.argv[4])
	inertia = float(sys.argv[5])
	vMax = float(sys.argv[6])
	qtyParticles = int(sys.argv[7])
	evalLimit = int(sys.argv[8])
	stopCriteria = str(sys.argv[9])

	if numObjectives <= 0:
		print "el número de objetivos debe ser positivo"
		exit(0)
	if vectorCardinality <= 0:
		print "la cardinalidad del vector debe ser positivo"
		exit(0)
	if numObjectives + 1 > vectorCardinality:
		print "el número de objetivos debe ser menor a la cardinalidad del vector"
		exit(0)
	if qtyParticles <= 0:
		print "la cantidad de partículas debe ser positiva"
		exit(0)
	if evalLimit <= 0:
		print "la cantidad de evaluaciones debe ser positiva"
		exit(0)
	if stopCriteria not in ['T','E']:
		print "el criterio de  parada no fue definido correctamente"
		exit(0)
	#instancia del problema a resolver
	problem = ProblemDTLZ1.ProblemDTLZ1()
	#se prepara la instancia de MOPSO con los parámetros recibidos
	m = MOPSO(cognitive, social, inertia, vMax, qtyParticles, vectorCardinality, numObjectives, problem.DTLZ1_HI,
			  problem.DTLZ1_generateRandomSolution, problem, evalLimit, stopCriteria,"crowding","simulations")
	#se inicializa el timer de feedback
	rt = RepeatedTimer(1.0, feedback,[m])
	#se ejecuta el algoritmo
	m.run()
	#para asegurar la finalización de la ejecución del programa, se finalizan todos los threads
	#de feedback
	rt.stop()
