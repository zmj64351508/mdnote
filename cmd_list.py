import os, sys
import getopt
import glob, time

import debug
import errors
import arguments
from cmd import *
from notebook import Notebook
from notebook import Notespace

class ListGeneral(object):
	def __init__(self):
		pass

	def get_notespace(self, core):
		if core:
			notespace = core.get_notespace()
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

	def core_main(self, core, argc, argv):
		return self.do_main(core, argc, argv)
	
	def main(self, argc, argv):
		return self.do_main(None, argc, argv)

	def do_main(self, core, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "b:t:d", 
				["notebook=", "tag=", "detail"])
		for op, value in opts:
			if op in ("-b", "--notebook"):
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

		self.notespace = self.target_general.get_notespace(core)

		notebook = None
		if self.arg_notebook:
			notebook = self.find_notebook(self.arg_notebook)

		tags = None
		if self.arg_tags:
			tags = self.find_tags(self.arg_tags)

		# normalize note name specified
		notes_path = self.notespace.norm_note_path(self.arg_string)
		
		result = self.list_filter(notebook, tags, notes_path)
		self.print_result(core, result, self.arg_detail)
		return 0

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

	def list_filter(self, notebook, tags, notes_path):
		if tags or notebook:
			notes_detail = self.notespace.filter_note_detail(notebook, tags)
		else:
			notes_detail = self.notespace.get_all_notes_detail()

		# Filter by note names specified as the last step.
		# We don't want to output any note that is not presented in notes_path except notes_path is None
		result = []
		if notes_path:
			debug.message(debug.DEBUG, "filter for note name: ", notes_path)
			for note_detail in notes_detail:
				if note_detail["path"].encode("utf8") in notes_path:
					result.append(note_detail)
			return result
		else:
			return notes_detail

	def print_result(self, core, result, print_detail):
		if not result:
			return

		if print_detail:
			for detail in result:
				self.output_result(core, "PATH: ", detail["path"], "\n")
				self.output_result(core, "NOTEBOOK: ", detail["notebook"], "\n")
				self.output_result(core, "TAG: ")
				for tag in detail["tag"]:
					if tag:
						self.output_result(core, tag,";")
				self.output_result(core, "\n")
				if core:
					self.output_result(core, "CREATE TIME: ", detail["create_time"], "\n")
					self.output_result(core, "MODIFY TIME: ", detail["modify_time"], "\n")
				else:
					self.output_result(core, "CREATE TIME: ", time.ctime(detail["create_time"]), "\n")
					self.output_result(core, "MODIFY TIME: ", time.ctime(detail["modify_time"]), "\n")
				self.output_result(core, " \n")
		else:
			for detail in result:
				self.output_result(core, detail["path"], "\n")

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

	def core_main(self, core, argc, argv):
		return self.do_main(core, argc, argv)
	
	def main(self, argc, argv):
		return self.do_main(None, argc, argv)

	def do_main(self, core, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "d", 
				["detail"])
		for op, value in opts:
			if op in ("-d", "--detail"):
				self.arg_detail = True

		# find notespace
		self.notespace = self.target_general.get_notespace(core)

		notebooks = self.notespace.get_all_notebooks()
		for notebook in notebooks:
			self.output_result(core, notebook + "\n")
		return 0
	
	def usage(self):
		print "usage: mdnote list notebook"

class TagTarget(CommandGeneral):
	def __init__(self):
		super(TagTarget, self).__init__()
		self.arg_detail = False
		self.target_general = ListGeneral()

	def core_main(self, core, argc, argv):
		return self.do_main(core, argc, argv)
	
	def main(self, argc, argv):
		return self.do_main(None, argc, argv)

	def do_main(self, core, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "d", 
				["detail"])
		for op, value in opts:
			if op in ("-d", "--detail"):
				self.arg_detail = True

		# find notespace
		self.notespace = self.target_general.get_notespace(core)

		tags = self.notespace.get_all_tags()
		for tag in tags:
			self.output_result(core, tag + "\n")
		return 0
	
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

