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
import commonModules.Database as Database
import json
import copy
import time
import numpy
import math
# MOPSO es el algoritmo de referencia
# version independiente del hardware
import pprint

DEBUG = False	# por defecto no es una ejecución de debug
PLOT = False	# por defecto no se dibuja
STORE = True	# por defecto se guarda información en la base de datos

def feedback(args):
	instance = args[0]
	log("Iteración -> " +
		str(instance.currentIteration) +
		" (" + '{:3.2f}'.format(
			instance.problemInstance.qtyEvaluations/
			instance.evalLimit * 100.0) +
		"%) gBest = " + str(len(instance.globalBest.particles)) +
		 "qtyEval = " + str(instance.problemInstance.qtyEvaluations)
	)

class HyperCube:
	def __init__(self, calif):
		self.calif = calif
		self.particles = []

	#elimina del hipercubo la particula indicada
	def removeParticleAt(self, index):
		ret = self.particles[index]
		del self.particles[index]
		return ret
	#elimina del hipercubo una partícula aleatoria
	def removeParticle(self):
		return self.removeParticleAt(random.randint(0,len(self.particles) - 1))
	#agrega una particula al hipercubo
	def addParticle(self,particle):
		self.particles.append(particle)
		
	#calcula la calificacion del hipercubo
	def updateCalif(self, x):
		if len(self.particles) != 0:
			self.calif = float(x) / len(self.particles)

	def getSize(self):
		return len(self.particles)

	#selecciona una partícula que representa a este hipercubo
	def selectBest(self):
		#@TODO implementar un mejor método de selección
		return self.particles[random.randint(0,len(self.particles) -1)]
#malla adaptativa de hipercubos de soluciones
class HyperCubes:
	#@param particleRepo -> repositorio de partículas
	#@param nDiv         -> número de divisiones en cada objetivo (cantidad de secciones 
	#                       de la malla adaptativa)
	def __init__(self, particleRepo, nDiv):
		self.particleRepo = particleRepo
		self.nDiv = nDiv
		#cantidad de objetivos
		self.M = particleRepo.M
		#número de hipercubos
		self.size = self.nDiv ** self.M 
		#lista que contiene los máximos de cada objetivo
		self.maxObj = [float("-inf") for _ in range(self.M)]
		#lista que contiene los mínimos de cada objetivo
		self.minObj = [float("inf") for _ in range(self.M)]
		#amplitud de cada uno de los hipercubos
		self.amp = [0 for _ in range(self.M)]
		#coordenadas de inicio en cada objetivo
		self.ini = [0 for _ in range(self.M)]
		#hipercubos, se crean hipercubos vacios al iniciar
		print "se crean hipercubos " + str(self.size)
		self.hyperCubes = [HyperCube(0) for _ in range(self.size)]
		print "se terminan de crear hipercubos"


	def assignSolutionsToHyperCubes(self):
		#se determinan valores extremos
		for i in range(self.M):
			self.maxObj[i] = self.particleRepo.particles[1].objectives[i]
			self.minObj[i] = self.particleRepo.particles[1].objectives[i]
			for j in range(len(self.particleRepo.particles)):
				if self.maxObj[i] < self.particleRepo.particles[j].objectives[i]:
					self.maxObj[i] = self.particleRepo.particles[j].objectives[i]
				elif self.minObj[i] > self.particleRepo.particles[j].objectives[i]:
					self.minObj[i] = self.particleRepo.particles[j].objectives[i]

		#se determinan las dimensiones de los hipercubos
		for i in range(self.M):
			#amplitud de los hipercubos en cada objetivo
			self.amp[i] = ( self.maxObj[i] - self.minObj[i] ) / ( self.nDiv - 1 )
			#coordenadas de inicio en cada objetivo
			self.ini[i] = self.minObj[i] - self.amp[i] / 2.0
		
		for i in range(len(self.particleRepo.particles)):
			#número del hipercubo para la solución
			pos = 0 
			for j in range(self.M):
				aux = math.floor( ( self.particleRepo.particles[i].objectives[j] - 
									self.ini[j] ) / self.amp[j] )
				pos += aux * ( self.nDiv ** j )
				if aux >= self.nDiv or aux < 0:
					pos = 0
					break
			self.hyperCubes[int(pos)].addParticle(self.particleRepo.particles[i])
		#calificar hipercubos
		for i in range(self.size):
			self.hyperCubes[i].updateCalif(10)
			

	#elimina una partícula del hipercubo mas poblado
	def deleteParticle(self):
		#seleccionamos el hipercubo mas poblado
		biggestHyperCube = self.hyperCubes[1]
		for hc in self.hyperCubes:
			if biggestHyperCube.getSize() < hc.getSize():
				biggestHyperCube = hc
		#se elimina una partícula aleatoria del hipercubo
		particle = biggestHyperCube.removeParticle()
		self.particleRepo.removeParticle(particle)
		return particle
		
	def reset(self):
		#lista que contiene los máximos de cada objetivo
		self.maxObj = [float("-inf") for _ in range(self.M)]
		#lista que contiene los mínimos de cada objetivo
		self.minObj = [float("inf") for _ in range(self.M)]
		#amplitud de cada uno de los hipercubos
		self.amp = [0 for _ in range(self.M)]
		#coordenadas de inicio en cada objetivo
		self.ini = [0 for _ in range(self.M)]
		#hipercubos, se crean hipercubos vacios al iniciar
		self.hyperCubes = [HyperCube(0) for _ in range(self.size)]
	#inserta una partícula a la coleccion de hipercubos
	def insertParticle(self, particle):
		#si el repositorio esta lleno, se elimina una partícula del hipercubo mas poblado
		if self.particleRepo.isFull():
			self.deleteParticle()
		pos = 0
		for i in range(self.M):
			oMax = self.ini[i] + self.amp[i] * self.nDiv
			#por debajo o por encima de los hipercubos
			if particle.objectives[i] < self.ini[i] or particle.objectives[i] > oMax:
				#se deben reasignar los hipercubos, por lo tanto 
				#se agrega la partícula al repositorio global
				self.particleRepo.add(particle)
				#se borran todos los elementos del hipercubo para reasignar partículas
				self.reset()
				#se reasignan las partículas
				self.assignSolutionsToHyperCubes()
				return
			aux = math.floor( ( particle.objectives[i] - 
								self.ini[i] ) / self.amp[i] )
			pos += aux * ( self.nDiv ** i )
			if aux > self.nDiv or aux < 0:
				pos = 0
				break
		#se inserta la partícula al repositorio global
		addedParticle = self.particleRepo.add(particle)
		#se agrega la partícula a un hipercubo
		self.hyperCubes[int(pos)].addParticle(addedParticle)
		#se actualiza la calificación del hipercubo
		self.hyperCubes[int(pos)].updateCalif(10)
	
	def getSize(self):
		size = 0
		for hc in self.hyperCubes:
			size += hc.getSize()
		return size

	#selección de la mejor partícula por el método de la ruleta
	def selectBest(self):
		#la suma de todos los fitness de los hipercubos
		totalFitness = float(sum(x.calif for x in self.hyperCubes if x.getSize() > 0))
		accumulatedRange = 0.0
		#para cada hipercubo con al menos una particula, se genera un diccionario con la 
		# siguiente estructura:
		#	[indice_hipercubo] = (rango_min, rango_max)
		#	[indice_hipercubo] = (rango_min, rango_max)
		#	[indice_hipercubo] = (rango_min, rango_max)
		#
		# donde rango_min y rango_max representa la frontera de probabilidad para cada
		# hipercubo
		lastIndex = 0
		rouletteRanges = {}
		for i in range(len(self.hyperCubes)):
			if self.hyperCubes[i].getSize() > 0:
				rouletteRanges[i] = (
					accumulatedRange ,
					accumulatedRange + self.hyperCubes[i].calif/totalFitness
				) 
				accumulatedRange += self.hyperCubes[i].calif/totalFitness
				lastIndex = i
		#para evitar errores de precisión, asignamos 1 como final del último rango
		minRange,_ = rouletteRanges[lastIndex]
		rouletteRanges[lastIndex] = (minRange, 1.0)
		
		#se hace girar la ruleta
		spin = random.random()

		selection = 0
		for k,v in rouletteRanges.iteritems():
			minRange,maxRange = v
			if minRange <= spin <= maxRange:
				selection = k
				break
		
		return self.hyperCubes[selection].selectBest()

#repositorio de partículas
class ParticleRepo:
	def __init__(self,N,M,QtyParticles):
		#cantidad de dimensiones de la partícula
		self.N = N							
		#cantidad de objetivos
		self.M = M							
		#cantidad máxima de partículas soportadas por el repositorio
		self.qtyParticles = QtyParticles
		#lista de soluciones encontradas	
		self.particles = []				

	#agrega una partícula al repositorio
	def add(self,particle):
		#se realiza una copia del elemento en el repositorio, de tal manera que al 
		#actualizar el pool de partículas la información no se pierda en el repositorio 
		#y de cualquier manera podamos acceder al objeto y sus métodos
		
		#si el repositorio está lleno, se elimina una partícula del mismo, eb esta versión
		#la eliminación se da desde los hipercubos, por lo tanto si se ejecuta esta parte
		#hubo un error!
		if self.isFull():
			#@TODO: elegir mejor la partícula que se va a eliminar
			del self.particles[random.randint(0,self.N-1)]
		addedParticle = Particle(
				particle.N, 
				particle.M, 
				particle.vMax, 
				particle.pos, 
				particle.vel, 
				particle.objectives
			)
		self.particles.append(addedParticle)
		return addedParticle

	def isFull(self):
		return len(self.particles) >= self.qtyParticles
		

	#determina si una partícula dada es dominada por algún elemento del repositorio
	def dominates(self,particle):
		if len(self.particles) > 0: 
			return isDominatedBySet(
				[p.objectives for p in self.particles], 
				particle.objectives
			)
		else:
			return False

	#retorna la partícula que es considerada la mejor del repositorio
	def selectBest(self, hyperCubes = None):
		if hyperCubes is None:
			#@TODO implementar otras opciones de selección
			return self.particles[random.randint(0,len(self.particles) -1)]
		else:
			return hyperCubes.selectBest()
			
	#elimina del repositorio todos los elementos que sean dominados por algun 
	#elemento del mismo se asume que la última partícula insertada es particle
	def removeDominatedElements(self, particle, globalBest = False, hyperCubes = None):
		
		#p para todo p en el repositorio tal que no es dominado por particle
		self.particles = [
			p for p in 
			self.particles if 
			not isDominatedBy(particle.objectives, p.objectives)
		]
		#se eliminan de la colección de hipercubos las partículas que no 
		#se encuentran en el repositorio 
		if globalBest:
			for i in range(len(hyperCubes.hyperCubes)):
				hyperCubes.hyperCubes[i].particles = [
					Par for Par in
					hyperCubes.hyperCubes[i].particles if
					Par in self.particles
				]
	#se encarga de eliminar la partícula dada comparando por valor, esta función
	#no se debe llamar a menos que sea desde la colección de hipercubos.
	def removeParticle(self,particle):
		self.particles.remove(particle)
		


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
			generateRandomSolution = None
			
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
				 problemEvalFunc, generateRandomSolution, problemInstance):
		print "varaibles de configuracion"
		#variables de configuración
		self.C1 = C1 						#parámetro cognitivo
		self.C2 = C2 						#parámetro social
		self.inertia = Inertia 				#parámetro de inercia
		self.vMax = VMax 					#velocidad máxima
		self.qtyParticles = QtyParticles	#cantidad de partículas
		self.N = N							#cardinalidad de partículas
		self.M = M							#cantidad de objetivos
		self.currentIteration = 1			#iteración actual del loop
		self.evalLimit = 0					#tiempo de ejecución
		self.problemEvalFunc = problemEvalFunc
		self.generateRandomSolution = generateRandomSolution
		self.problemInstance = problemInstance
		self.simulation = None

		print "variables de ejecucion"
		#variables de ejecución
		#pool de partículas
		self.particles = []	
		#repositorio de mejores soluciones globales
		self.globalBest = ParticleRepo(self.N, self.M, self.qtyParticles)	
		#se inicializa la colección de hipercubos
		self.hyperCubes = HyperCubes(self.globalBest, 30)
		
		print "inicialización del pool de partículas"
		#se inicializa el pool de partículas
		for _ in range(self.qtyParticles):
			#se genera una partícula con posición y velocidad iniciales randomizadas
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
			self.updateGlobalBest(p, init = True)
		#se inicializa la colección de hipercubos
		print "asignación de soluciones a hipercubos"
		self.hyperCubes.assignSolutionsToHyperCubes()
		

	#verifica si la partícula dada debe incluirse en el repositorio de 
	#mejores soluciones globales y actualiza el repositorio si es necesario
	def updateGlobalBest(self,particle, init = False):
		#si la partícula no es dominada por el repositorio global actual debe agregarse
		if not self.globalBest.dominates(particle):
			#se inserta la partícula tanto a la colección de hipercubos
			#como al repositorio global
			if not init:
				self.hyperCubes.insertParticle(particle)
			else:
				#solo en el inicio se inserta unicamente al repositorio, puesto que
				#aun no se inicializaron los hipercubos
				self.globalBest.add(particle)
			self.globalBest.removeDominatedElements(particle, True, self.hyperCubes)

	#loop principal
	def run(self, EvalLimit):
		self.evalLimit = EvalLimit
		if STORE:
			self.storeSimulation()
			self.storePopulation()
		if PLOT:
			plotInitForMOPSO(fig,ax,im)
		#condición de parada, cantidad de ejecuciones de la función de evaluación
		while True:
			self.currentIteration += 1
			#para cada partícula
			#print "primer for"
			gBest = self.globalBest.selectBest(self.hyperCubes)
			for i in range(self.qtyParticles):
				#se recupera el mejor global
				#gBest = self.globalBest.selectBest()
				#se recupera el mejor local de la partícula
				lBest = self.particles[i].localBest.selectBest()
				#la partícula avanza 
				self.particles[i].step(gBest, lBest, self.inertia, self.C1, self.C2)
			#para cada partícula 
			#(@TODO, ver implicancias de actualizar el repositorio en el primer loop)
			#print "segundo for"
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
				plotForMOPSO(p, fig, ax, im)
			#condición de parada
			if self.problemInstance.qtyEvaluations >= self.evalLimit:
				break
		if STORE:
			#actualizamos la base de datos con el tiempo de finalización de la simulación
			self.simulation.endTime = datetime.datetime.now()
			db.updateSimulation(self.simulation)
		

		print len(self.globalBest.particles)
		print self.hyperCubes.getSize()
		for p in self.globalBest.particles:
			print sum(p.objectives)
		for p in self.globalBest.particles:
			print p.pos

	def storePopulation(self):
		#se guarda en la base de datos la colección de ṕartículas inicial
		population = Database.Population(0.0, False, self.simulation.id, self.currentIteration)
		db.insertPopulation(population,self.simulation)
		
		for p in self.globalBest.particles:
			part = Database.Particle(p.N, p.M, p.pos, p.vel, p.objectives, population.id )
			db.insertParticle(part,population)
			
	def storeSimulation(self):
		#se guarda en la base de datos la primera población
		configuration = "N = " + str(self.N)
		configuration += ", M = "+str(self.M)
		configuration += ", qtyParticles = " + str(self.qtyParticles)
		configuration += ", evalLimit = "+str(self.evalLimit)
		configuration += ", C1 = "+str(self.C1)
		configuration += ", C2 = "+str(self.C2)
		configuration += ", inertia = "+str(self.inertia)
		configuration += ", vMax = "+str(self.vMax)
		
		command = str(sys.argv[0])
		for param in sys.argv[1:]:
			command += " " + param
			
		self.simulation = Database.Simulation(
			-1.0, 
			platform.uname(), 
			datetime.datetime.now(), 
			datetime.datetime.now(), 
			"MOPSO_CL", 
			configuration, 
			command
		)
		db.insertSimulation(self.simulation)


if len(sys.argv) < 9:
	print "Forma de Uso:" 
	print "\t" + sys.argv[0] + "<M> <N> <C1> <C2> <inertia> <vMax> <qtyParticles> <execTime>"
	print "\n\tM = \t\t(entero positivo) cantidad de objetivos"
	print "\n\tN = \t\t(entero positivo) cantidad de elementos del vector"
	print "\n\tC1 = \t\tparámetro cognitivo"
	print "\n\tC2 = \t\tparámetro social" 
	print "\n\tinertia = \t\tparámetro de inercia"
	print "\n\tvMax = \t\tvelocidad máxima"
	print "\n\tqtyParticles = \t\t(entero )cantidad de partículas"
	print "\n\tevalLimit = \t\t(entero positivo)cantidad límite de evaluaciones"
	exit(0)

#se copian los parámetros y se validan
numObjectives = int(sys.argv[1])
vectorCardinality = int(sys.argv[2])
cognitive = float(sys.argv[3])
social = float(sys.argv[4])
inertia = float(sys.argv[5])
vMax = float(sys.argv[6])
qtyParticles = int(sys.argv[7])
evalLimit = float(sys.argv[8])

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


#instancia del problema a resolver
problem = ProblemDTLZ1.ProblemDTLZ1()
#conección con la base de datos para guardar las simulaciones
db = Database.Database('tesis','torresmateo','a')
#se prepara la instancia de MOPSO con los parámetros recibidos
print "inicializando"
m = MOPSO(
	cognitive, 
	social, 
	inertia, 
	vMax, 
	qtyParticles,
	vectorCardinality, 
	numObjectives, 
	problem.DTLZ1_HI, 
	problem.DTLZ1_generateRandomSolution, 
	problem
)
#se inicializa el timer de feedback
rt = RepeatedTimer(1.0, feedback,[m])
#se ejecuta el algoritmo
m.run(evalLimit)
#para asegurar la finalización de la ejecución del programa, se finalizan todos los threads
#de feedback
rt.stop()

print "particulas en repo global " + str(len(m.globalBest.particles))
print "particulas en hipercubos " + str(m.hyperCubes.getSize())

for h in m.hyperCubes.hyperCubes:
	for par in h.particles:
		if par not in m.globalBest.particles:
			print "hay una particula entre los hipercubos que no esta en el repositorio global"

