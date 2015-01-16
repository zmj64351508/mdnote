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

	def get_notespace(self, server):
		if server:
			notespace = server.get_notespace()
			debug.message(debug.DEBUG, "notespace path is ", notespace.get_path())
		else:
			notespace = Notespace()
		return notespace

	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def server_main(self, server, argc, argv):
		self.do_main(server, argc, argv)

	def do_main(self, server, argc, argv):
		if argc < 1:
			self.usage()
			exit()
		elif argc == 2:
			path = argv[1]
		else:
			path = "."

		# create notespace first if necessary
		self.notespace = self.get_notespace(server)
		if not self.notespace.find_notespace(path, up_to_root = False):
			debug.message(debug.DEBUG, "No notespace found, creating notespace")
			self.notespace.create(path)

			# create Notebooks
			debug.message(debug.DEBUG, "Creating default notebook")
			self.notespace.create_default_notebook()
		else:
			debug.message(debug.DEBUG, "Notespace already exists do nothing")

	def usage(self):
		print "usage: mdnote init"

