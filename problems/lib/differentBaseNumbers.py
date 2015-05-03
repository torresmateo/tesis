#!/usr/bin/python
#-*- coding: utf-8 -*-

def obtainDigit(number, base, index):
	return (number/base**index)%base

if __name__ == "__main__":
	for i in range(300):
		print str(i) + "\t\t" + str(obtainDigit(i,3,3)) + "\t" + str(obtainDigit(i,3,2)) + \
			  "\t" + str(obtainDigit(i,3,1)) + "\t" + str(obtainDigit(i,3,0))

