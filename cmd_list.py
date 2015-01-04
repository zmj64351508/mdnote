import os, sys
import getopt

import debug
import errors
import arguments
from cmd import Cmd
from notebook import Notebook
from notebook import Notespace

class Command(Cmd):
	def __init__(self):
		Cmd.__init__(self)
		self.arg_notebook = None
		self.arg_tags = None
		self.arg_string = None
		self.arg_detail = False

	def run(self, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "n:t:d", ["notebook=", "tag=", "detail"])
		for op, value in opts:
			if op in ("-n", "--notebook"):
				self.arg_notebook = value
			elif op in ("-t", "--tag"):
				self.arg_tags = arguments.get_multi_arg(value)
			elif op in ("-d", "--detail"):
				self.arg_detail = True

		if len(args) > 1:
			raise errors.UsageError("Too many arguments")
		if args:
			self.arg_string = args[0]
		debug.message(debug.DEBUG, "listing condition:" )
		debug.message(debug.DEBUG, "\tnotebook: ", self.arg_notebook)
		debug.message(debug.DEBUG, "\ttags    : ", self.arg_tags)
		debug.message(debug.DEBUG, "\tstring  : ", self.arg_string)

		# find notespace
		self.notespace = Notespace()
		if not self.notespace.find_notespace("."):
			raise errors.NotFoundError("Can't find notespace maybe you should run init first")

		notebook = None
		if self.arg_notebook:
			notebook = self.find_notebook(self.arg_notebook)

		tags = None
		if self.arg_tags:
			tags = self.find_tags(self.arg_tags)

		if self.arg_string:
			# grep string
			pass

		self.list_filter(notebook, tags)

	def find_notes(self, nb_names, n_names):
		pass

	def find_notebook(self, nb_name):
		if not nb_name:
			return None

		notebook = self.notespace.find_notebook(nb_name)
		if not notebook:
			debug.message(debug.ERROR, "No notebook named ", nb_name)
			raise errors.NoSuchRecord()
		return notebook

	def find_tags(self, tag_names):
		if not tag_names:
			return None

		tags = []
		for name in tag_names: 
			tag = self.notespace.find_tag(name)
			if tag:
				tags.append(tag)
			else:
				debug.message(debug.ERROR, "No tag named ", name)
				raise errors.NoSuchRecord()
		return tags

	def list_filter(self, notebook, tags):
		if tags or notebook:
			notes_detail = self.notespace.filter_note_detail(notebook, tags)
		else:
			notes_detail = self.notespace.get_all_notes_detail()

		if not notes_detail:
			return

		if self.arg_detail:
			for detail in notes_detail:
				sys.stdout.write(detail["path"].__str__() + "|" + detail["notebook"].__str__() + "|")
				for tag in detail["tag"]:
					if tag:
						sys.stdout.write(tag.__str__()+";")
				sys.stdout.write("\n")
		else:
			for detail in notes_detail:
				sys.stdout.write(detail["path"].__str__() + "\n")

	def usage(self):
		print "usage: mdnote list"

