# Command:
#     init
import os
import debug
from cmd import *
from notebook import Notebook
from notebook import Notespace

class Main(CommandGeneral):
	def __init__(self):
		super(Main, self).__init__()
		self.notebooks = {}

	def main(self, argc, argv):
		if argc < 1:
			self.usage()
			exit()

		# create notespace first if necessary
		self.notespace = Notespace()
		if not self.notespace.find_notespace("."):
			debug.message(debug.DEBUG, "No notespace found, creating notespace")
			self.notespace.create(".")

			# create Notebooks
			debug.message(debug.DEBUG, "Creating default notebook")
			self.notespace.create_default_notebook()
		else:
			debug.message(debug.DEBUG, "Notespace already exists do nothing")


	def usage(self):
		print "usage: mdnote init"

