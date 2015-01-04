import sys

DEBUG = 0
INFO  = 1
WARN  = 2
ERROR = 3

level_label = ("DEBUG", "INFO ", "WARN ", "ERROR")

debug_level = DEBUG

def message(level, *args):
	if level >= debug_level:
		sys.stdout.write("[" + level_label[level] + "] ")
		for arg in args:
			sys.stdout.write(arg.__str__())
		sys.stdout.write("\n")

