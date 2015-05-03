#!/usr/bin/python
#-*- coding: utf-8 -*-

# este módulo calcula el Epsilon-Indicator entre dos simulaciones
# condiciones: las simulaciones deben ser de la misma cantidad de dimensiones (espacio objetivo)
import Database
import datetime
from domination import *
import pprint

class EpsilonIndicator():
	def __init__(self, firstSimulationId, secondSimulationId, filename = ''):
		#se obtiene la primera simulación
		self.firstSimulationId = firstSimulationId
		self.firstSimulation = db.getSimulation(self.firstSimulationId)
		self.firstFinalPop = db.getFinalPopulationBySimulation(self.firstSimulation)
		print firstSimulationId
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
		print secondSimulationId
		#se obtienen las soluciones de la primera población
		if self.secondSimulation.method in ['MOPSO','MOPSO_CL']:
			self.secondSimulationSolutions = db.getParticlesByPopulation(self.secondFinalPop)
		elif self.secondSimulation.method == 'NSGA-II':
			self.secondSimulationSolutions = db.getGenesByPopulation(self.secondFinalPop)
		elif self.secondSimulation.method == 'RANDOM':
			self.secondSimulationSolutions = db.getSolutionsByPopulation(self.secondFinalPop)
		
		if filename == '':
			self.filename = "epsilon-" + datetime.datetime.now().strftime("%Y-%m-%d,%H_%M_%S") + ".tex"
		else:
			self.filename = filename
		self.filename = "../latex/epsilon/" + self.filename
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

	\\title{$\epsilon$-Indicator Metric}
	\\author{Mateo Torres}
	%\institute{Universidad Cat\\'olica ``Nuestra Se\~nora de la Asunci\\'on''}
	\maketitle
	'''
		reportData = '''
	\\begin{tabular}{|r|c|c|}
		\hline
		\\textbf{M\\'etodo} & $ A = $'''+escapeSpecialChars(str(self.firstSimulation.method))+'''  & $B = $'''+escapeSpecialChars(str(self.secondSimulation.method))+''' \\\\
		\hhline{|=|=|=|}
		\\textbf{Cant. Soluciones} & '''+str(self.firstFinalPop.getSolutionsQty(db))+''' & ''' + str(self.secondFinalPop.getSolutionsQty(db)) + ''' \\\\
		\hline
		\\textbf{$I_\epsilon$} & $I_{\epsilon}(A,B) = ''' + str(self.epsilonAB) + '''$ & $I_{\epsilon}(B,A)''' + str(self.epsilonBA) + '''$ \\\\
		\hline
	\end{tabular}
'''
		self.file.write(header)
		self.file.write(reportData)

	def calcEpsilonIndicator(self):
		self.epsilonAB = 0
		self.epsilonBA = 0
		for zA in self.firstSimulationSolutions:
			for zB in self.secondSimulationSolutions:
				for i in range(len(zA.objectives)):
					if zB.objectives[i] > 0:
						self.epsilonAB = max( self.epsilonAB,zA.objectives[i] / zB.objectives[i] )
					if zA.objectives[i] > 0:
						self.epsilonBA = max( self.epsilonBA,zB.objectives[i] / zA.objectives[i] )
					
	def closeFile(self):
		self.file.write("\end{document}")
		self.file.close()

# 5 20 13 (2 dimensiones)
# 6 21 14 (3 dimensiones)
# 7 22 15 (5 dimensiones)
# 8 23 16 (10 dimensiones)

def escapeSpecialChars(string):
	return string.replace('_','\_')


if __name__ == "__main__":
	db = Database.Database('tesis','torresmateo','a')
	versusPairs = [[1,12],[1,18],[12,18], #combinaciones de 2 dimensiones
				   [2,13],[2,19],[13,19], #combinaciones de 3 dimensiones
				   [3,20],                #combinaciones de 5 dimensiones
				   [4,21]]                #combinaciones de 10 dimensiones
	for a,b in versusPairs:
		ei = EpsilonIndicator(a,b,str(a)+"_vs_"+str(b)+".tex")
		ei.calcEpsilonIndicator()
		ei.generateLatex()
		ei.closeFile()
