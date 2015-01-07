import os, sys
import getopt

from cmd import *
import debug
import errors
import arguments
from notebook import Notebook
from notebook import Notespace

class Main(CommandGeneral):
	def __init__(self):
		super(Main, self).__init__()
		self.arg_notebook = None
		self.arg_tags = None
		self.arg_string = None
		self.arg_detail = False

	def main(self, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "n:t:d", 
				["notebook=", "tag=", "detail"])
		for op, value in opts:
			if op in ("-d", "--detail"):
				self.arg_detail = True

		# find notespace
		self.notespace = Notespace()
		if not self.notespace.find_notespace("."):
			raise errors.NotFoundError("Can't find notespace maybe\
					you should run init first")

		notebooks = self.notespace.get_all_notebooks()
		for notebook in notebooks:
			print notebook
	
	def usage(self):
		print "usage: mdnote list-notebook"

