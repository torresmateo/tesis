#!/usr/bin/python
#-*- coding: utf-8 -*-

import datetime

def log(message):
	print "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S:%f") + "] " + message