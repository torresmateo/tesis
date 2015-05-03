#!/usr/bin/python
#-*- coding: utf-8 -*-

# este módulo permite registrar las pruebas de los distintos algoritmos en una base de datos.


import psycopg2 #conección con PostgreSQL
import platform #para obtener el nombre de la computadora
import datetime #para pruebas de guardado de fechas de inicio y fin 
import json
from collections import OrderedDict

#debug
import pprint

#sacado de http://code.activestate.com/recipes/577186-accessing-cursors-by-field-name/ para acceder a los objetos por nombre
class reg(object):
	def __init__(self, cursor, row):
		for (attr, val) in zip((d[0] for d in cursor.description), row) :
			setattr(self, attr, val)

#clases de utilidad para crear con facilidad objetos en la base de datos
class Simulation:
	def __init__(self, hyper_volume_reference_point, computer, init_time, end_time, method, params, command, id = None):
		self.id = id
		self.hyperVolumeReferencePoint = hyper_volume_reference_point
		self.computer = platform.uname() #este campo en realidad es necesariamente el uname, por lo tanto se ignora el parámetro
		self.initTime = init_time
		self.endTime = end_time
		self.method = method
		self.params = params
		self.command = command

		#para guardar en archivos y no en base de datos
		self.populations = OrderedDict()
		self.populationIndex = 0

	def __str__(self):
		string = "id: " + str(self.id) + "\n"
		string += "hyperVolumeReferencePoint: " + str(self.hyperVolumeReferencePoint) + "\n"
		string += "computer: " + str(self.computer) + "\n"
		string += "initTime: " + str(self.initTime) + "\n"
		string += "endTime: " + str(self.endTime) + "\n"
		string += "method: " + str(self.method) + "\n"
		string += "params: " + str(self.params) + "\n"
		string += "command: " + str(self.command) + "\n"
		return string


	def addPopulation(self, population):
		self.populations[self.populationIndex] = population.jsonRepresentation()
		self.populationIndex += 1

	def storeToFile(self, filename = None):
		if filename is None:
			filename = str(self.params) + ".json"
		else:
			filename += str(self.params) + ".json"
		simulationFile = open(filename,'w')
		simulationFile.write(self.jsonRepresentation())
		simulationFile.close()

	def jsonRepresentation(self):
		jsonRep = {"computer":self.computer, "initTime": unicode(self.initTime), "endTime": unicode(self.endTime),
				   "populations": self.populations, "method": self.method}
		return json.dumps(jsonRep)

	def getParameter(self, parameter):
		params = self.params.split(',')
		for param in params:
			name, value = param.split("=")
			if name.strip() == parameter:
				return value.strip()
		return "notFound"

class Population:
	def __init__(self, hyper_volume, is_final_pop, simulation_id, iteration, id = None):
		self.id = id
		self.hyperVolume = hyper_volume
		self.isFinalPop = is_final_pop
		self.simulationId = simulation_id
		self.iteration = iteration

		#para guardar en archivos y no en base de datos
		self.solutions = OrderedDict()
		self.solutionIndex = 0

	def __str__(self):
		string = "id: " + str(self.id) + "\n"
		string += "hyperVolume: " + str(self.hyperVolume) + "\n"
		string += "isFinalPop: " + str(self.isFinalPop) + "\n"
		string += "simulationId: " + str(self.simulationId) + "\n"
		string += "iteration: " + str(self.iteration) + "\n"
		return string


	def addParticle(self, particle):
		self.solutions[self.solutionIndex] = particle.jsonRepresentation()
		self.solutionIndex += 1

	def addGene(self, gene):
		self.solutions[self.solutionIndex] = gene.jsonRepresentation()
		self.solutionIndex += 1

	def jsonRepresentation(self):
		jsonRep = {"isFinalPop":self.isFinalPop, "iteration":self.iteration, "solutions": self.solutions}
		return json.dumps(jsonRep)

	#retorna la cantidad de soluciones encontradas en una población
	#@param: db instancia de la clase Database
	def getSolutionsQty(self,db):
		s = db.getSimulation(self.simulationId)
		method = s.method
		solutions = []
		if method in ["MOPSO","MOPSO_CL"]:
			solutions = db.getParticlesByPopulation(self)
		elif method == "NSGA-II":
			solutions = db.getGenesByPopulation(self)
		elif method == "RANDOM":
			solutions = db.getSolutionsByPopulation(self)
		return len(solutions)

#partícula de MOPSO
class Particle:
	def __init__(self, n, m, pos, vel, objectives, population_id, id = None):
		self.id = id
		self.n = n
		self.m = m
		self.pos = pos
		self.vel = vel
		self.objectives = objectives
		self.populationId = population_id


	def __str__(self):
		string = 'id: ' + str(self.id) + "\n"
		string += 'n: ' + str(self.n) + "\n"
		string += 'm: ' + str(self.m) + "\n"
		string += 'pos: ' + str(self.pos) + "\n"
		string += 'vel: ' + str(self.vel) + "\n"
		string += 'objectives: ' + str(self.objectives) + "\n"
		string += 'populationId: ' + str(self.populationId) + "\n"
		return string


	def jsonRepresentation(self):
		jsonRep = {"m": self.m, "n": self.n, "pos": self.pos, "vel": self.vel, "objectives": self.objectives}
		return json.dumps(jsonRep)

#solucion de NSGA
class Gene:
	def __init__(self, n, m, attributes, objectives, hyper_volume_contribution, nsga2_rank, nsga2_distance, population_id, id = None):
		self.id = id
		self.n = n
		self.m = m
		self.attributes = attributes
		self.objectives = objectives
		self.hyperVolumeContribution = hyper_volume_contribution
		self.nsga2Rank = nsga2_rank
		self.nsga2Distance = nsga2_distance
		self.populationId = population_id

	def __str__(self):
		string = 'id: ' + str(self.id) + "\n"
		string += 'n: ' + str(self.n) + "\n"
		string += 'm: ' + str(self.m) + "\n"
		string += 'attributes: ' + str(self.attributes) + "\n"
		string += 'objectives: ' + str(self.objectives) + "\n"
		string += 'hyperVolumeContribution: ' + str(self.hyperVolumeContribution) + "\n"
		string += 'nsga2Rank: ' + str(self.nsga2Rank) + "\n"
		string += 'nsga2Distance: ' + str(self.nsga2Distance) + "\n"
		string += 'populationId: ' + str(self.populationId) + "\n"
		return string

	def jsonRepresentation(self):
		jsonRep = {"m": self.m, "n": self.n, "attributes": self.attributes, "objectives": self.objectives,
				   "nsga2Rank": self.nsga2Rank, "nsga2Distance": self.nsga2Distance}
		return json.dumps(jsonRep)

class Solution:
	def __init__(self, n, m, attributes, objectives, population_id, id = None):
		self.id = id
		self.n = n
		self.m = m
		self.attributes = attributes
		self.objectives = objectives
		self.populationId = population_id


	def __str__(self):
		string = 'id: ' + str(self.id) + "\n"
		string += 'n: ' + str(self.n) + "\n"
		string += 'm: ' + str(self.m) + "\n"
		string += 'attributes: ' + str(self.attributes) + "\n"
		string += 'objectives: ' + str(self.objectives) + "\n"
		string += 'populationId: ' + str(self.populationId) + "\n"
		return string


	def jsonRepresentation(self):
		jsonRep = {"n": self.n, "m": self.m, "objectives": self.objectives, "attributes": self.attributes}
		return json.dumps(jsonRep)


class Database:
	def __init__(self, dbName, dbUser, dbPassword, dbHost = "localhost"):
		self.dbName = dbName
		self.dbUser = dbUser
		self.dbPassword = dbPassword
		self.dbHost = dbHost
		self.dbConn = psycopg2.connect(database = self.dbName, user = self.dbUser, password = self.dbPassword, host = self.dbHost)
		#self.dbConn = psycopg2.connect(database = self.dbName, user = self.dbUser, password = self.dbPassword)
		self.dbCursor = self.dbConn.cursor()
		self.createSchema()


	# dada una tabla, verifica su existencia en la base de datos
	# @param tableName = nombre de la tabla cuya existencia es verificada
	# @return boolean = True en caso de que la tabla exista, False en caso contrario
	def checkTable(self, tableName):
		self.dbCursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (tableName,))
		a = self.dbCursor.fetchone()[0]
		return a

	# verifica la estructura de la base de datos de la clase
	# @return boolean = True en caso de que existan todas las tablas, False en caso contrario
	def checkSchema(self):
		return self.checkTable('simulation') and self.checkTable('population') and self.checkTable('solution')

	def createSchema(self):
		if not self.checkSchema():
			print "se crea la base de datos aparentemente"
			sql = """
			create table simulation(
				id serial primary key,
				hyper_volume_reference_point text not null,
				computer text not null,
				init_time timestamp not null,
				end_time timestamp not null,
				method varchar(40) not null,
				params text not null,
				command text not null
			);

			create table population(
				id serial primary key,
				hyper_volume numeric(150,30) not null,
				is_final_pop boolean not null,
				simulation_id integer references simulation(id),
				iteration integer not null
			);

			create table solution(
				id serial primary key,
				json text not null,
				population_id integer references population(id)
			);

			create table global_util(
				id serial primary key,
				name text not null,
				value text not null
			);
			"""
			self.dbCursor.execute(sql)
			self.dbConn.commit()

	#inserta un objeto simulación a la base de datos
	#simulation	-> objeto de simulación a insertar
	def insertSimulation(self, simulation):
		sql = "insert into simulation(hyper_volume_reference_point, computer, init_time, end_time, method, params, command) "
		sql += "values (%(hyper_volume_reference_point)s, %(computer)s, %(init_time)s, %(end_time)s, %(method)s, %(params)s, %(command)s) returning id"
		self.dbCursor.execute(sql,{'hyper_volume_reference_point':json.dumps(simulation.hyperVolumeReferencePoint), 'computer':simulation.computer, 'init_time':simulation.initTime, 'end_time':simulation.endTime, 'method':simulation.method, 'params':simulation.params, 'command':simulation.command}) 
		self.dbConn.commit()
		simulation.id = self.dbCursor.fetchone()[0]
		
	#inserta un objeto población asociado a un objeto simulación
	#population	-> objeto de población a insertar
	#simulation	-> objeto de simulación que será asociado a la población indicada
	def insertPopulation(self, population, simulation):
		sql = "insert into population(hyper_volume, is_final_pop, simulation_id, iteration) "
		sql += "values (%(hyper_volume)s, %(is_final_pop)s, %(simulation_id)s, %(iteration)s) returning id"
		self.dbCursor.execute(sql,{'hyper_volume':population.hyperVolume, 'is_final_pop':population.isFinalPop, 'simulation_id':simulation.id, 'iteration':population.iteration}) 
		self.dbConn.commit()
		population.id = self.dbCursor.fetchone()[0]
	
	#inserta un objeto gen asociado a un objeto población
	#solution	-> objeto de gen a insertar
	#population	-> objeto de población que será asociado al gen indicada
	def insertGene(self, gene, population):
		sql = "insert into solution(json, population_id) "
		sql += "values (%(n)s, %(population_id)s) returning id"
		self.dbCursor.execute(sql,{'n':json.dumps(gene.__dict__), 'population_id':population.id}) 
		self.dbConn.commit()
	
	#inserta un objeto partícula asociado a un objeto población
	#particle	-> objeto de partícula a insertar
	#population	-> objeto de población que será asociado a la partícula indicada
	def insertParticle(self, particle, population):
		sql = "insert into solution(json, population_id) "
		sql += "values (%(n)s, %(population_id)s) returning id"
		self.dbCursor.execute(sql,{'n':json.dumps(particle.__dict__), 'population_id':population.id}) 
		self.dbConn.commit()
	
	#inserta un objeto solución asociado a un objeto población
	#particle	-> objeto de solución a insertar
	#population	-> objeto de población que será asociado a la solución indicada
	def insertSolution(self, solution, population):
		sql = "insert into solution(json, population_id) "
		sql += "values (%(n)s, %(population_id)s) returning id"
		self.dbCursor.execute(sql,{'n':json.dumps(solution.__dict__), 'population_id':population.id}) 
		self.dbConn.commit()
	
	#dado un ID, retorna el objeto simulación
	def getSimulation(self, id):
		sql = "select * from simulation where id = %(id)s"
		self.dbCursor.execute(sql,{'id':id})
		s = reg(self.dbCursor, self.dbCursor.fetchone())
		return Simulation(json.loads(s.hyper_volume_reference_point), s.computer, s.init_time, s.end_time, s.method, s.params, s.command, s.id)
	
	#retorna todas las simulaciones
	def getAllSimulations(self):
		sql = "select * from simulation order by id"
		self.dbCursor.execute(sql)
		simulationList = []
		for row in self.dbCursor.fetchall():
			s = reg(self.dbCursor, row)
			simulationList.append(Simulation(json.loads(s.hyper_volume_reference_point), s.computer, s.init_time, s.end_time, s.method, s.params, s.command, s.id))
		return simulationList
	
	def getSimulationsQty(self):
		sql = "select count(*) qty from simulation"
		self.dbCursor.execute(sql)
		return self.dbCursor.fetchone()[0]

	#dado un ID, retorna el objeto población
	def getPopulation(self, id):
		sql = "select * from population where id = %(id)s"
		self.dbCursor.execute(sql,{'id':id})
		p = reg(self.dbCursor, self.dbCursor.fetchone())
		return Population(p.hyper_volume, p.is_final_pop, p.simulation_id, p.iteration, p.id)
	
	#dada una simulación, retorna una lista con las poblaciones asociadas
	def getPopulationsBySimulation(self, simulation):
		sql = "select * from population where simulation_id = %(id)s order by id"
		self.dbCursor.execute(sql,{'id':simulation.id})
		populationList = []
		for row in self.dbCursor.fetchall():
			p = reg(self.dbCursor, row)
			populationList.append(Population(p.hyper_volume, p.is_final_pop, p.simulation_id, p.iteration, p.id))
		return populationList
	
	def getFinalPopulationBySimulation(self, simulation):
		sql = "select * from population where simulation_id = %(id)s and is_final_pop is true"
		self.dbCursor.execute(sql,{'id':simulation.id})
		population = self.dbCursor.fetchone()
		if population is not None:
			p = reg(self.dbCursor, population)
			return Population(p.hyper_volume, p.is_final_pop, p.simulation_id, p.iteration, p.id)
		return None

	#dado un ID, retorna el objeto gen
	def getGene(self, id):
		sql = "select * from solution where id = %(id)s"
		self.dbCursor.execute(sql,{'id':id})
		s = reg(self.dbCursor, self.dbCursor.fetchone())
		decoded = json.loads(s.json)
		return Gene(decoded['n'], decoded['m'], decoded['attributes'], decoded['objectives'], decoded['hyperVolumeContribution'], decoded['nsga2Rank'], decoded['nsga2Distance'], decoded['populationId'], s.id)
		#pprint.pprint(s)
	
	#dado un ID, retorna el objeto particula
	def getParticle(self, id):
		sql = "select * from solution where id = %(id)s"
		self.dbCursor.execute(sql,{'id':id})
		p = reg(self.dbCursor, self.dbCursor.fetchone())
		decoded = json.loads(s.json)
		return Particle(decoded['n'], decoded['m'], decoded['pos'], decoded['vel'], decoded['objectives'], decoded['populationId'], p.id)
		#pprint.pprint(s)
	
	#dado un ID, retorna el objeto solución
	def getSolution(self, id):
		sql = "select * from solution where id = %(id)s"
		self.dbCursor.execute(sql,{'id':id})
		s = reg(self.dbCursor, self.dbCursor.fetchone())
		decoded = json.loads(s.json)
		return Solution(decoded['n'], decoded['m'], decoded['attributes'], decoded['objectives'], decoded['populationId'], s.id)
	
	#dada una población, retorna una lista con los genes asociados
	def getGenesByPopulation(self, population):
		sql = "select * from solution where population_id = %(id)s order by id"
		self.dbCursor.execute(sql,{'id':population.id})
		geneList = []
		for row in self.dbCursor.fetchall():
			g = reg(self.dbCursor, row)
			decoded = json.loads(g.json)
			#solo se agregan los genes del primer frente
			if decoded['nsga2Rank'] == 0:
				geneList.append(Gene(decoded['n'], decoded['m'], decoded['attributes'], decoded['objectives'], decoded['hyperVolumeContribution'], decoded['nsga2Rank'], decoded['nsga2Distance'], decoded['populationId'], g.id))
		return geneList
	
	#dada una población, retorna una lista con las partículas asociadas
	def getParticlesByPopulation(self, population):
		sql = "select * from solution where population_id = %(id)s order by id"
		self.dbCursor.execute(sql,{'id':population.id})
		particleList = []
		for row in self.dbCursor.fetchall():
			p = reg(self.dbCursor, row)
			decoded = json.loads(p.json)
			particleList.append(Particle(decoded['n'], decoded['m'], decoded['pos'], decoded['vel'], decoded['objectives'],decoded['populationId'], p.id))
		return particleList
	
	#dada una población, retorna una lista con los genes asociados
	def getSolutionsByPopulation(self, population):
		sql = "select * from solution where population_id = %(id)s order by id"
		self.dbCursor.execute(sql,{'id':population.id})
		geneList = []
		for row in self.dbCursor.fetchall():
			g = reg(self.dbCursor, row)
			decoded = json.loads(g.json)
			geneList.append(Solution(decoded['n'], decoded['m'], decoded['attributes'], decoded['objectives'], decoded['populationId'], g.id))
		return geneList
	

	#guarda el estado de la simulación dada
	def updateSimulation(self, simulation):
		sql = "update simulation set hyper_volume_reference_point = %(hyper_volume_reference_point)s, computer = %(computer)s, init_time = %(init_time)s, end_time = %(end_time)s, method = %(method)s, params = %(params)s, command = %(command)s where id = %(id)s"
		self.dbCursor.execute(sql,{'hyper_volume_reference_point':json.dumps(simulation.hyperVolumeReferencePoint), 'computer':simulation.computer, 'init_time':simulation.initTime, 'end_time':simulation.endTime, 'method':simulation.method, 'params':simulation.params, 'command':simulation.command, 'id':simulation.id})
		self.dbConn.commit()
		
	#guarda el estado de la población dada
	def updatePopulation(self, population):
		sql = "update population set hyper_volume = %(hyper_volume)s, is_final_pop = %(is_final_pop)s, simulation_id = %(simulation_id)s, iteration = %(iteration)s where id = %(id)s"
		self.dbCursor.execute(sql,{'hyper_volume':population.hyperVolume, 'is_final_pop':population.isFinalPop, 'simulation_id':population.simulationId, 'iteration':population.iteration, 'id':population.id})
		self.dbConn.commit()
	
	#guarda el estado de la solución dada
	def updateGene(self, gene):
		sql = "update solution set json = %(json)s, population_id = %(population_id)s where id = %(id)s"
		self.dbCursor.execute(sql,{'json':gene.json, 'population_id':gene.populationId, 'id':gene.id})
		self.dbConn.commit()
	
	#guarda el estado de la solución dada
	def updateParticle(self, particle):
		sql = "update solution set json = %(json)s, population_id = %(population_id)s where id = %(id)s"
		self.dbCursor.execute(sql,{'json':particle.json, 'population_id':particle.populationId, 'id':particle.id})
		self.dbConn.commit()
	
	#guarda el estado de la solución dada
	def updateSolution(self, solution):
		sql = "update solution set json = %(json)s, population_id = %(population_id)s where id = %(id)s"
		self.dbCursor.execute(sql,{'json':solution.json, 'population_id':solution.populationId, 'id':solution.id})
		self.dbConn.commit()
	#============================================================================================================================================================
	#SECCION DE LAS VARIABLES GLOBALES DE BASE DE DATOS
	#============================================================================================================================================================
	
	def setGlobalUtilValue(self,name, value):
		if self.getGlobalUtilValue(name) is None:
			sql = "insert into global_util (name,value)"
			sql += "values (%(name)s, %(value)s)"
		else:
			sql = "update global_util set value = %(value)s"
			sql += "where name = %(name)s"
		self.dbCursor.execute(sql,{'name':name, 'value':json.dumps(value)})
		self.dbConn.commit()
		
	#dado un nombre de variable, retorna el valor
	def getGlobalUtilValue(self,name):
		sql = "select * from global_util where name = %(name)s"
		self.dbCursor.execute(sql,{'name':name})
		utilVariable = self.dbCursor.fetchone()
		if(utilVariable is not None):
			s = reg(self.dbCursor, utilVariable)
			return json.loads(s.value)
		return None

#script de testing de funciones de base de datos
if __name__ == "__main__":
	db = Database('tesis','torresmateo','a')
	print db.getSimulationsQty()
	db.setGlobalUtilValue('hola',[1,2,123,3])
	print db.getGlobalUtilValue('hola')
	
