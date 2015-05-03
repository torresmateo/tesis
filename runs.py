#!/usr/bin/python
# -*- coding: utf-8 -*-
#import commonModules.DatabaseCorrelation as DatabaseCorrelation
#import commonModules.Database as Database
import sys
import problems.ProblemDTLZ1 as ProblemDTLZ1
import problems.ProblemDTLZ2 as ProblemDTLZ2
import problems.ProblemDTLZ3 as ProblemDTLZ3
import problems.ProblemDTLZ4 as ProblemDTLZ4
import problems.ProblemDTLZ5 as ProblemDTLZ5
import NSGAII_HI as NSGAII
import MOPSO_HI as MOPSO
import time
import datetime
from itertools import product
import os
import platform
from os.path import expanduser
import errno
import random


if platform.system() is not 'Windows':
    globalHome = expanduser("~")
else:
    globalHome = "D:/"


#seguridad para evitar que el programa falle por limite de recursividad con muchas
#dimensiones
sys.setrecursionlimit(10000 * 3)


def problemSelection(runProblem):
    if runProblem == "DTLZ1":
        problem = ProblemDTLZ1.ProblemDTLZ1()
        return problem, problem.DTLZ1_HI, problem.DTLZ1_generateRandomSolution
    elif runProblem == "DTLZ2":
        problem = ProblemDTLZ2.ProblemDTLZ2()
        return problem, problem.DTLZ2_HI, problem.DTLZ2_generateRandomSolution
    elif runProblem == "DTLZ3":
        problem = ProblemDTLZ3.ProblemDTLZ3()
        return problem, problem.DTLZ3_HI, problem.DTLZ3_generateRandomSolution
    elif runProblem == "DTLZ4":
        problem = ProblemDTLZ4.ProblemDTLZ4(100)
        return problem, problem.DTLZ4_HI, problem.DTLZ4_generateRandomSolution
    elif runProblem == "DTLZ5":
        problem = ProblemDTLZ5.ProblemDTLZ5()
        return problem, problem.DTLZ5_HI, problem.DTLZ5_generateRandomSolution

#ejecucion para hacer fine tuning de mopso con respecto a la calidad
# pares de m, n
pairs = [
    # (2,6),
    # (3,7),
    # (4,8),
    # (5,9),
    (6,10),
    # (7,11),
    # (8,12),
    # (9,13),
    # (10,14),
    # (11,15),
    # (12,16),
    # (13,17),
    # (14,18),
    # (15,19),
    # (16,20),
    # (17,21),
    # (18,22),
    # (19,23),
    # (20,24),
    ]

simulation_n = 1
dtlz_version = "2"
for val_m, val_n in pairs:
    a = 0
    folderStr = "dtlz" + dtlz_version + "_m_"+str(val_m)+"_n_"+str(val_n)+"_120_limited"
    simulationFolderPath = globalHome + "/assets/simulations/" + folderStr + "/"
    hyperVolumeFolderPath = globalHome + "/assets/hypervolume/" + folderStr + "/"
    hyperVolumeRFolderPath = globalHome + "/assets/hypervolumeResult/" + folderStr + "/"
    #se verifica que existe la carpeta que se desea crear
    try:
        os.makedirs(simulationFolderPath)
        os.makedirs(hyperVolumeFolderPath)
        os.makedirs(hyperVolumeRFolderPath)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    valuesM = [val_m]
    valuesN = [val_n]
    valuesC1 = [0.25, 0.5]
    valuesC2 = [0.25, 0.5]
    valuesInertia = [8, 10]
    valuesVMax = [16.5, 16.571, 16.572]
    valuesQtyParticles = [1000]

    totalEjecuciones = len(valuesM) * len(valuesN) * len(valuesC1) * len(valuesC2) * len(valuesInertia) * len(valuesVMax) * \
                       len(valuesQtyParticles)


    #para evitar el warning de que no este inicializado
    problemInstance = None
    problemEvalFunc = None
    problemGenerateRandomSolution = None

    runMOPSO = True
    runNSGA = False
    RunProblem = "DTLZ" + dtlz_version
    if runMOPSO:
        for m, n, c1, c2, inertia, vMax, qtyParticles in \
                product(valuesM, valuesN, valuesC1,
                        valuesC2, valuesInertia, valuesVMax,
                        valuesQtyParticles):
            a += 1

            problemInstance, problemEvalFunc, problemGenerateRandomSolution = problemSelection(RunProblem)

            mopso = MOPSO.MOPSO(
                c1,
                c2,
                inertia,
                vMax,
                qtyParticles,
                n,
                m,
                problemEvalFunc,
                problemGenerateRandomSolution,
                problemInstance,
                120,
                'T',
                DeleteCriteria=None,
                Folder=simulationFolderPath,
                SelectCriteria=None,
                SpecialDistribution=True,
                SpecialDistributionNDiv=50
            )
            #check if file exists
            if os.path.isfile(simulationFolderPath + mopso.configurationString() + ".json"):
                print "simulation exists, skipping"
                continue
            print mopso.configurationString()
            mopso.run()
            print m, n, c1, c2, inertia, vMax, qtyParticles
            print str(a) + "/" + str(totalEjecuciones) + "(" + str(float(a) / float(totalEjecuciones) * 100.0) + "%) in " + str(simulation_n) + "/19"
        print a
        print simulationFolderPath
        print hyperVolumeFolderPath
    if runNSGA:
        mutationRates = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        crossoverRates = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
        for m, n, mut_rate, cross_rate, qtyParticles in \
                product(valuesM, valuesN, mutationRates ,
                        crossoverRates, valuesQtyParticles):
            problemInstance, problemEvalFunc, problemGenerateRandomSolution = problemSelection(RunProblem)

            initialPopulation = NSGAII.Solution.generateFirstPopulation(
                val_n,
                val_m,
                qtyParticles,
                problemGenerateRandomSolution,
                problemEvalFunc
            )
            nsga = NSGAII.NSGAII(val_n, val_m, mut_rate, cross_rate, qtyParticles, 700, problemInstance, 'T', simulationFolderPath)
            nsga.run(initialPopulation)
    simulation_n += 1
