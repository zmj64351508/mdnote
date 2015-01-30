import os, sys
import getopt
import glob, time

import debug
import errors
import arguments
from cmd import *
from notebook import Notebook
from notebook import Notespace

class RmGeneral(object):
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
		self.arg_purge = False
		self.target_general = RmGeneral()

	def core_main(self, core, argc, argv):
		return self.do_main(core, argc, argv)
	
	def main(self, argc, argv):
		return self.do_main(None, argc, argv)

	def do_main(self, core, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "", 
				["purge"])
		for op, value in opts:
			if op in ("--purge"):
				self.arg_purge = True

		self.notespace = self.target_general.get_notespace(core)
		notes_path = self.notespace.norm_note_path(args)
		debug.message(debug.DEBUG, "notes path are ", notes_path)
		return self.notespace.remove_notes_by_path(notes_path, self.arg_purge, True)

	def usage(self):
		print "usage: mdnote list"

class Main(CommandWithTarget):
	def __init__(self):
		target_factory = TargetFactory({
			"note":NoteTarget,
			#"notebook":NotebookTarget,
			#"tag":TagTarget,
			#"target":TargetTarget,
		})
		super(Main, self).__init__(target_factory)

	def usage(self):
		print "cmd_rm"

