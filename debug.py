import sys, os

DEBUG = 0
INFO  = 1
WARN  = 2
ERROR = 3

level_label = ("DEBUG", "INFO ", "WARN ", "ERROR")

debug_level = DEBUG

def message(level, *args):
	if level >= debug_level:
		sys.stdout.write("[" + level_label[level] + "] " + "[" + str(os.getpid()) + "] ")
		for arg in args:
			try:
				sys.stdout.write(str(arg))
			except:
				sys.stdout.write(arg)
		sys.stdout.write("\n")

