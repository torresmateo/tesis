#!/usr/bin/python
#-*- coding: utf-8 -*-

# este módulo calcula el coverage entre dos simulaciones
# condiciones: las simulaciones deben ser de la misma cantidad de dimensiones (espacio objetivo)
import Database
import datetime
from domination import *
import pprint

class CoverageIndicator():
	@staticmethod
	def calcCoverage(firstSimulationSolutions, secondSimulationSolutions):
		#preparamos las listas de objetivos
		firstSolutionList = []
		secondSolutionList = []
		for objectives in firstSimulationSolutions:
			firstSolutionList.append(objectives)
		for objectives in secondSimulationSolutions:
			secondSolutionList.append(objectives)
		#soluciones de la primera simulación dominan a la segunda
		firstDominance = extractDominance(firstSolutionList, secondSolutionList)
		#soluciones de la segunda simulación dominan a la primera
		secondDominance = extractDominance(secondSolutionList, firstSolutionList)
		#soluciones de la primera simulación dominadas por la segunda
		firstDominated = extractDominated(firstSolutionList, secondSolutionList)
		#soluciones de la segunda simulación dominadas por la primera
		secondDominated = extractDominated(secondSolutionList, firstSolutionList)

		return [firstDominance, secondDominance, firstDominated, secondDominated]

class Coverage():
	def __init__(self, firstSimulationId, secondSimulationId, filename = ''):
		#se obtiene la primera simulación
		self.firstSimulationId = firstSimulationId
		self.firstSimulation = db.getSimulation(self.firstSimulationId)
		self.firstFinalPop = db.getFinalPopulationBySimulation(self.firstSimulation)
		#se obtienen las soluciones de la primera población
		if self.firstSimulation.method in ['MOPSO','MOPSO_CL']:
			self.firstSimulationSolutions = db.getParticlesByPopulation(self.firstFinalPop)
		elif self.firstSimulation.method == 'NSGA-II':
			self.firstSimulationSolutions = db.getGenesByPopulation(self.firstFinalPop)
		elif self.firstSimulation.method == 'RANDOM':
			self.firstSimulationSolutions = db.getSolutionsByPopulation(self.firstFinalPop)
		
		#se obtiene la primera simulación
		self.secondSimulationId = secondSimulationId
		self.secondSimulation = db.getSimulation(self.secondSimulationId)
		self.secondFinalPop = db.getFinalPopulationBySimulation(self.secondSimulation)
		#se obtienen las soluciones de la primera población
		if self.secondSimulation.method in ['MOPSO','MOPSO_CL']:
			self.secondSimulationSolutions = db.getParticlesByPopulation(self.secondFinalPop)
		elif self.secondSimulation.method == 'NSGA-II':
			self.secondSimulationSolutions = db.getGenesByPopulation(self.secondFinalPop)
		elif self.secondSimulation.method == 'RANDOM':
			self.secondSimulationSolutions = db.getSolutionsByPopulation(self.secondFinalPop)
		
		if filename == '':
			self.filename = "coverage-" + datetime.datetime.now().strftime("%Y-%m-%d,%H_%M_%S") + ".tex"
		else:
			self.filename = filename
		self.filename = "../latex/coverage/" + self.filename
		self.file = open(self.filename, "w")
		self.closedFile = False

	def generateLatex(self):
		header = '''\documentclass{article}
% http://sourceforge.net/projects/pgfplots/
\usepackage{pgfplots}
\usepackage{tabularx}
\usepackage{hhline}
\usepackage{amssymb,amsmath}
\pgfplotsset{compat=newest}
\pagestyle{empty}
\\begin{document}

	\\title{Coverage Metric}
	\\author{Mateo Torres}
	%\institute{Universidad Cat\\'olica ``Nuestra Se\~nora de la Asunci\\'on''}
	\maketitle
	'''
		#coverage del primero sobre el segundo
		firstCoverage = '$\\dfrac{'+str(len(self.firstDominated))+'}{'+str(self.firstFinalPop.getSolutionsQty(db))+'} = '+str(float(len(self.firstDominated))/float(self.firstFinalPop.getSolutionsQty(db)))+'$'
		secondCoverage = '$\\dfrac{'+str(len(self.secondDominated))+'}{'+str(self.secondFinalPop.getSolutionsQty(db))+'} = '+str(float(len(self.secondDominated))/float(self.secondFinalPop.getSolutionsQty(db)))+'$'
		firstComplementaryCoverage = '$\\dfrac{'+str(len(self.firstDominance))+'}{'+str(self.firstFinalPop.getSolutionsQty(db))+'} = '+str(float(len(self.firstDominance))/float(self.firstFinalPop.getSolutionsQty(db)))+'$'
		secondComplementaryCoverage = '$\\dfrac{'+str(len(self.secondDominance))+'}{'+str(self.secondFinalPop.getSolutionsQty(db))+'} = '+str(float(len(self.secondDominance))/float(self.secondFinalPop.getSolutionsQty(db)))+'$'
		
		reportData = '''
	\\begin{tabular}{|r|c|c|}
		\hline
		\\textbf{M\\'etodo} & '''+str(self.firstSimulation.method)+'''  & '''+str(self.secondSimulation.method)+''' \\\\
		\hhline{|=|=|=|}
		\\textbf{Cant. Soluciones} & '''+str(self.firstFinalPop.getSolutionsQty(db))+''' & ''' + str(self.secondFinalPop.getSolutionsQty(db)) + ''' \\\\
		\hline
		\\textbf{Cant. Soluciones Dominantes } & ''' + str(len(self.firstDominance)) + ''' & ''' + str(len(self.secondDominance)) + ''' \\\\
		\hline
		\\textbf{Cant. Soluciones Dominandas } & ''' + str(len(self.firstDominated)) + ''' & ''' + str(len(self.secondDominated)) + ''' \\\\
		\hline & &\\\\[-1em]
		\\textbf{Coverage} & ''' + firstCoverage  + ''' & ''' + secondCoverage + ''' \\\\[0.5em]
		\hline & &\\\\[-1em]
		\\textbf{Coverage Complementario} & ''' + firstComplementaryCoverage  + ''' & ''' + secondComplementaryCoverage + ''' \\\\[0.5em]
		\hline
	\end{tabular}
'''
		self.file.write(header)
		self.file.write(reportData)

	def calcCoverage(self):
		#preparamos las listas de objetivos
		firstSolutionList = []
		secondSolutionList = []
		for s in self.firstSimulationSolutions:
			firstSolutionList.append(s.objectives)
		for s in self.secondSimulationSolutions:
			secondSolutionList.append(s.objectives)
		#soluciones de la primera simulación dominan a la segunda
		self.firstDominance = extractDominance(firstSolutionList, secondSolutionList)
		#soluciones de la segunda simulación dominan a la primera
		self.secondDominance = extractDominance(secondSolutionList, firstSolutionList)
		#soluciones de la primera simulación dominadas por la segunda
		self.firstDominated = extractDominated(firstSolutionList, secondSolutionList)
		#soluciones de la segunda simulación dominadas por la primera
		self.secondDominated = extractDominated(secondSolutionList, firstSolutionList)

		
		pprint.pprint(firstSolutionList)
		pprint.pprint(secondSolutionList)
		pprint.pprint(self.firstDominance)
		pprint.pprint(self.secondDominance)
		pprint.pprint(self.firstDominated)
		pprint.pprint(self.secondDominated)


	def closeFile(self):
		self.file.write("\end{document}")
		self.file.close()

# 5 20 13 (2 dimensiones)
# 6 21 14 (3 dimensiones)
# 7 22 15 (5 dimensiones)
# 8 23 16 (10 dimensiones)

if __name__ == "__main__":
	db = Database.Database('tesis','torresmateo','a')
	versusPairs = [[5,20],[5,13],[20,13], #combinaciones de 2 dimensiones
				   [6,21],[6,14],[21,14], #combinaciones de 3 dimensiones
				   [7,22],[7,15],[22,15], #combinaciones de 5 dimensiones
				   [8,23],[8,16],[23,16]] #combinaciones de 10 dimensiones
	for a,b in versusPairs:
		c = Coverage(a,b,str(a)+"_vs_"+str(b)+".tex")
		c.calcCoverage()
		c.generateLatex()
		c.closeFile()
