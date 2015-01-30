# Command:
#     init
import os, sys
import debug
from cmd import *
from notebook import Notebook
from notebook import Notespace

class Main(CommandGeneral):
	def __init__(self):
		super(Main, self).__init__()
		self.notebooks = {}

	def get_notespace(self, core):
		if core:
			notespace = core.get_notespace()
			debug.message(debug.DEBUG, "notespace path is ", notespace.get_path())
		else:
			notespace = Notespace()
		return notespace

	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def core_main(self, core, argc, argv):
		self.do_main(core, argc, argv)

	def do_main(self, core, argc, argv):
		if argc < 1:
			self.usage()
			exit()
		elif argc == 2:
			path = argv[1].decode("utf8").encode(sys.getfilesystemencoding())
		else:
			path = "."

		# create notespace first if necessary
		self.notespace = self.get_notespace(core)
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

