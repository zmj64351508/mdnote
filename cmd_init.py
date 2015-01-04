# Command:
#     init
import os
import debug
from cmd import Cmd
from notebook import Notebook
from notebook import Notespace

class Command(Cmd):
	def __init__(self):
		Cmd.__init__(self)
		self.notebooks = {}

	def run(self, argc, argv):
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

