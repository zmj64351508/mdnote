import os, sys
import getopt
import glob

import debug
import errors
import arguments
from cmd import *
from notebook import Notebook
from notebook import Notespace

class ListGeneral(object):
	def __init__(self):
		pass

	def get_notespace(self, server):
		if server:
			notespace = server.get_notespace()
			if not notespace:
				raise errors.NotFoundError("No notespace found. Maybe you should run open first")
		else:
			# find notespace
			notespace = Notespace()
			if not notespace.find_notespace("."):
				raise errors.NotFoundError("Can't find notespace maybe you should run init first")
		return notespace

class NoteTarget(CommandGeneral):
	def __init__(self):
		super(NoteTarget, self).__init__()
		self.arg_notebook = None
		self.arg_tags = None
		self.arg_string = None
		self.arg_detail = False
		self.target_general = ListGeneral()

	def server_main(self, server, argc, argv):
		self.do_main(server, argc, argv)
	
	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def do_main(self, server, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "n:t:d", 
				["notebook=", "tag=", "detail"])
		for op, value in opts:
			if op in ("-n", "--notebook"):
				self.arg_notebook = value
			elif op in ("-t", "--tag"):
				self.arg_tags = arguments.get_multi_arg(value)
			elif op in ("-d", "--detail"):
				self.arg_detail = True

		if args:
			self.arg_string = args
		debug.message(debug.DEBUG, "listing condition:" )
		debug.message(debug.DEBUG, "\tnotebook: ", self.arg_notebook)
		debug.message(debug.DEBUG, "\ttags    : ", self.arg_tags)
		debug.message(debug.DEBUG, "\tstring  : ", self.arg_string)

		self.notespace = self.target_general.get_notespace(server)

		notebook = None
		if self.arg_notebook:
			notebook = self.find_notebook(self.arg_notebook)

		tags = None
		if self.arg_tags:
			tags = self.find_tags(self.arg_tags)

		# normalize note name specified
		note_names = self.norm_note_name(self.arg_string)
		
		result = self.list_filter(notebook, tags, note_names)
		self.print_result(server, result, self.arg_detail)

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

	def norm_note_name(self, to_norm):
		note_names = []
		if self.arg_string:
			for path in to_norm:
				# All the path should relative to notespace's path instead of `pwd`.
				# So make the absolute path according to notespace's path
				# so that we can use glob to find the note
				if not os.path.isabs(path):
					path = os.path.join(self.notespace.get_path(), path)

				glob_result = glob.glob(path)

				for real_path in glob_result:
					# At last the path store in database is relative path to notespace' path
					# So we re-build this path
					relative_path = os.path.relpath(real_path, self.notespace.get_path())
					note_names.append(relative_path)
		return note_names

	def list_filter(self, notebook, tags, note_names):
		if tags or notebook:
			notes_detail = self.notespace.filter_note_detail(notebook, tags)
		else:
			notes_detail = self.notespace.get_all_notes_detail()

		# Filter by note names specified as the last step.
		# We don't want to output any note that is not presented in note_names except note_names is None
		result = []
		if note_names:
			debug.message(debug.ERROR, "filter for note name: ", note_names)
			for note_detail in notes_detail:
				if note_detail["path"] in note_names:
					result.append(note_detail)
			return result
		else:
			return notes_detail

	def print_result(self, server, result, print_detail):
		if not result:
			return

		if print_detail:
			for detail in result:
				self.output_result(server, "PATH: " + detail["path"].__str__() + "\n")
				self.output_result(server, "NOTEBOOK: " + detail["notebook"].__str__() + "\n")
				self.output_result(server, "TAG: ")
				for tag in detail["tag"]:
					if tag:
						self.output_result(server, tag.__str__()+";")
				self.output_result(server, "\n \n")
		else:
			for detail in result:
				self.output_result(server, detail["path"].__str__() + "\n")

	def usage(self):
		print "usage: mdnote list"

class NotebookTarget(CommandGeneral):
	def __init__(self):
		super(NotebookTarget, self).__init__()
		self.arg_notebook = None
		self.arg_tags = None
		self.arg_string = None
		self.arg_detail = False
		self.target_general = ListGeneral()

	def server_main(self, server, argc, argv):
		self.do_main(server, argc, argv)
	
	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def do_main(self, server, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "d", 
				["detail"])
		for op, value in opts:
			if op in ("-d", "--detail"):
				self.arg_detail = True

		# find notespace
		self.notespace = self.target_general.get_notespace(server)

		notebooks = self.notespace.get_all_notebooks()
		for notebook in notebooks:
			self.output_result(server, notebook + "\n")
	
	def usage(self):
		print "usage: mdnote list notebook"

class TagTarget(CommandGeneral):
	def __init__(self):
		super(TagTarget, self).__init__()
		self.arg_detail = False
		self.target_general = ListGeneral()

	def server_main(self, server, argc, argv):
		self.do_main(server, argc, argv)
	
	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def do_main(self, server, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "d", 
				["detail"])
		for op, value in opts:
			if op in ("-d", "--detail"):
				self.arg_detail = True

		# find notespace
		self.notespace = self.target_general.get_notespace(server)

		tags = self.notespace.get_all_tags()
		for tag in tags:
			self.output_result(server, tag + "\n")
	
	def usage(self):
		print "usage: mdnote list notebook"

class Main(CommandWithTarget):
	def __init__(self):
		target_factory = TargetFactory({
			"note":NoteTarget,
			"notebook":NotebookTarget,
			"tag":TagTarget,
			#"target":TargetTarget,
		})
		super(Main, self).__init__(target_factory)

	def usage(self):
		print "cmd_list"

