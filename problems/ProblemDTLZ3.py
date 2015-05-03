#!/usr/bin/python
#-*- coding: utf-8 -*-
from math import cos, pi, sin
from random import random, uniform
from lib.differentBaseNumbers import obtainDigit


class ProblemDTLZ3():
	def __init__(self):
		#cantidad de evaluaciones realizadas
		self.qtyEvaluations = 0

	@staticmethod
	def getProblemDescription():
		return "DTLZ3"

	#genera un vector de cardinalidad n con valores random
	#genera un vector de carinalidad n con valores random
	@staticmethod
	def DTLZ3_generateRandomSolution(n, ndiv = 0, index = 0):
		retVal = []
		if ndiv == 0:
			for _ in range(n):
				retVal.append(random())
		else:
			for i in range(n):
				divCoord = obtainDigit(index, ndiv, i)
				retVal.append(uniform(1.0/ndiv * divCoord, 1.0/ndiv * (divCoord + 1)))
		return retVal

	#genera de
	@staticmethod
	def DTLZ3_generateRandomValue():
		return random()


	# DTLZ3_g es la función llamada pro las funciones objetivo
	# definida por:
	# 100( |X_M| + SUM[(x_i - 0.5)^2 - cos(20 * PI * (x_i - 0.5))] )
	# para todo x_i en X_M
	# @param List X_M: Conjunto al cual aplicarle la función g
	@staticmethod
	def DTLZ3_g(X_M):
		#calculamos la sumatoria
		gSum = 0
		for x_i in X_M:
			gSum += ((x_i - 0.5) ** 2) - cos(20 * pi * (x_i - 0.5))
		return 100 * (len(X_M) + gSum)

	# DTLZ3_f son las funciones objetivo definidas, para el DTLZ1 es como sigue:
	# Min f_1(X) =  (1 + g(X_M)) * cos(x_1 * PI_HALF ) * ... * cos(x_{M-1} * PI_HALF)
	# Min f_1(X) =  (1 + g(X_M)) * cos(x_1 * PI_HALF ) * ... * sin(x_{M-1} * PI_HALF)
	# Min   .						 .
	# Min   .						 .
	# Min   .						 .
	# Min f_{M-1}(X) = (1 + g(X_M)) * sin(x_1 * PI_HALF)
	# Min f_M(X) = 0.5(1 - x_1)(1 + g(X_M))
	#
	# sujeto a 0 <= x_i <= 1
	#
	# @param int i : Subindice de la función
	# @param List X : vector de valores
	# @param int M : cantidad de objetivos del problema
	def DTLZ3_f(self, i, X, M):
		result = 1
		#para los primeros M-i elementos en X se prepara la multiplicatoria
		for x_i in X[:M-i]:
			result *= cos(x_i * pi / 2.0)
		#se agrega el factor sin
		if i > 1: #segun la definicion de DTLZ2 el objetivo f_1(x) no cuenta con el factor seno
			result *= sin(X[M - i] * pi / 2.0)
		#se agrega el factor (1 + g(X_M))
		result *= (1 + self.DTLZ3_g(X[M-1:]))
		return result

	# retorna un vector con los valores asociados a una solución
	# @param List X : vector solución
	# @param int M : cantidad de funciones objetivo
	def DTLZ3(self, X, M):
		solution = []
		for i in range(1,M+1):
			solution.append(self.DTLZ3_f(i, X, M))
		return solution

	####################################################################################
	#             funciones independientes al hardware
	####################################################################################

	#esta función cuenta cuantas veces se llamó a la función DTLZ_f, que es la que
	#hace la evaluación para cada objetivo
	def DTLZ3_HI(self,X,M):
		#se suma la cantidad de objetivos a la cantidad de evaluaciones
		self.qtyEvaluations += 1
		#se llama a la función de evaluación de DTLZ1
		return self.DTLZ3(X,M)



