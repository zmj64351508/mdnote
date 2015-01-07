import os
import getopt

from cmd import *
import debug
import errors
import arguments
from notebook import Notebook
from notebook import Notespace

class NoteTarget(CommandGeneral):
	def __init__(self):
		super(NoteTarget, self).__init__()
		self.arg_notebook = None
		self.arg_tags = None

	def main(self, argc, argv):
		opts, args = getopt.getopt(argv[1:], "n:t:", ["notebook=", "tag="])
		for op, value in opts:
			if op in ("-n", "--notebook"):
				self.arg_notebook = value
				debug.message(debug.DEBUG, "notebook is ", value)
			elif op in ("-t", "--tag"):
				self.arg_tags = arguments.get_multi_arg(value)
				debug.message(debug.DEBUG, "tag is ", value)

		self.arg_notes = args
		debug.message(debug.DEBUG, "notes are", self.arg_notes)
		if not self.arg_notes:
			raise errors.UsageError("No note specified")


		# find notespace
		self.notespace = Notespace()
		if not self.notespace.find_notespace("."):
			raise errors.NotFoundError("Can't find notespace maybe \
					you should run init first")

		# add note to notebook
		if self.arg_notebook:
			note = self.add_notes_to_notebook(self.arg_notes, self.arg_notebook)
		else:
			debug.message(debug.DEBUG, 
					"No notebook specified, using default notebook")
			note = self.add_notes_to_notebook(self.arg_notes, 
					self.notespace.get_default_notebook())

		# add tags
		if self.arg_tags:
			self.add_notes_to_tags(note, self.arg_tags)

		self.notespace.get_database().commit()
	
	# notebook can be class Notebook or notebook path
	def add_notes_to_notebook(self, notes_path, notebook):
		notes = []
		if type(notebook) == str:
			nb_name = notebook
			notebook = self.notespace.find_notebook(nb_name)
			if not notebook:
				debug.message(debug.DEBUG, 
						"Automatically creating notebook ", nb_name)
				notebook = self.notespace.create_notebook(nb_name)
			for note_path in notes_path:
				notes.append(notebook.add_note(note_path, False))

		elif type(notebook) == Notebook:
			for note_path in notes_path:
				notes.append(notebook.add_note(note_path, False))

		return notes

	def add_notes_to_tags(self, notes, tags):
		if type(tags) == list and type(tags[0]) == str:
			for tag_name in tags:
				tag = self.notespace.find_tag(tag_name)
				if not tag:
					tag = self.notespace.create_tag(tag_name)
				for note in notes:
					tag.add_note(note, False)

class NotebookTarget(CommandGeneral):
	pass

class TagTarget(CommandGeneral):
	pass

# The main command class of this command
class Main(CommandWithTarget):
	def __init__(self):
		target_factory = TargetFactory({
			"note":NoteTarget,
			"notebook":NotebookTarget,
			"tag":TagTarget,
		})
		super(Main, self).__init__(target_factory)

	def usage(self):
		print "cmd_add"


