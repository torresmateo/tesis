#!/usr/bin/python
#-*- coding: utf-8 -*-
#import sys
from math import cos, pi
from random import random, uniform
from lib.differentBaseNumbers import obtainDigit

class ProblemDTLZ1():

	def __init__(self):
		#cantidad de evaluaciones realizadas
		self.qtyEvaluations = 0

	@staticmethod
	def getProblemDescription():
		return "DTLZ1"

	#genera un vector de carinalidad n con valores random
	@staticmethod
	def DTLZ1_generateRandomSolution(n, ndiv = 0, index = 0):
		retVal = []
		if ndiv == 0:
			for _ in range(n):
				retVal.append(random())
		else:
			for i in range(n):
				divCoord = obtainDigit(index, ndiv, i)
				retVal.append(uniform(1.0/ndiv * divCoord, 1.0/ndiv * (divCoord + 1)))
		return retVal


	#genera un valor dentro del constraint para la dimensión i
	@staticmethod
	def DTLZ1_generateRandomValue():
		return random()

	# DTLZ1_g es la función llamada por las funciones objetivo
	# definida por:
	# 100( |X_M| + SUM[ (x_i - 0.5)^2 - cos(20 * PI * (x_i - 0.5)) ])
	# para todo x_i en X_M
	# @param List X_M : Conjunto al cual aplicarle la función g
	@staticmethod
	def DTLZ1_g(X_M):
		#calculamos la sumatoria
		gSum = 0
		for x_i in X_M:
			gSum += ((x_i - 0.5) ** 2) - cos(20 * pi * (x_i - 0.5))
		return 100 * ( len(X_M) + gSum)



	# DTLZ1_f son las funciones objetivo definidas, para el DTLZ1 es como sigue:
	# Min f_1(X) = 0.5 * x_1 * x_2 * ... * x_{M-1} * (1 + g(X_M))
	# Min f_2(X) = 0.5 * x_1 * x_2 * ... * (1 - x_{M-1})(1 + g(X_M))
	# Min   .						 .
	# Min   .						 .
	# Min   .						 .
	# Min f_{M-1}(X) = 0.5 * x_1 (1 - x_2)(1 + g(X_M))
	# Min f_M(X) = 0.5(1 - x_1)(1 + g(X_M))
	#
	# sujeto a 0 <= x_i <= 1
	#
	# @param int i : Subindice de la función
	# @param List X : vector de valores
	# @param int M : cantidad de objetivos del problema
	def DTLZ1_f(self, i, X, M):
		result = 0.5
		#para los primeros M-i elementos en X se prepara la multiplicatoria
		for x_i in X[:M-i]:
			result *= x_i
		#se agrega el factor de forma (1-x_i)
		if i > 1:#según la definición de DTLZ1 el objetivo f_1(x) no cuenta con este factor (X_{M-1} está incluido en la multiplicatoria)
			result *= (1 - X[M-i])
		#se agrega el factor (1 + g(X_M))
		result *= (1 + self.DTLZ1_g(X[M-1:]))
		return result

	# retorna un vector con los valores asociados a un solución
	# @param List X : vector solucion
	# @param int M : cantidad de funciones objetivo
	def DTLZ1(self, X,M):
		#solution = {} #dict
		solution = [] #list
		for i in range(1,M+1):
			#solution[i] = DTLZ1_f(i,X,M) #dict
			solution.append(self.DTLZ1_f(i,X,M))
		return solution

	####################################################################################
	#             funciones independientes al hardware
	####################################################################################

	#esta función cuenta cuantas veces se llamó a la función DTLZ_f, que es la que
	#hace la evaluación para cada objetivo
	def DTLZ1_HI(self,X,M):
		#se suma la cantidad de objetivos a la cantidad de evaluaciones
		self.qtyEvaluations += 1
		#se llama a la función de evaluación de DTLZ1
		return self.DTLZ1(X,M)
		
