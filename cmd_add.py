import os
import getopt

from cmd import *
import debug
import errors
import arguments
from notebook import Notebook, Note
from notebook import Notespace

class AddGeneral(object):
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
		self.arg_force = False
		self.target_general = AddGeneral()

	def server_main(self, server, argc, argv):
		self.do_main(server, argc, argv)
	
	def main(self, argc, argv):
		self.do_main(None, argc, argv)

	def do_main(self, server, argc, argv):
		opts, args = getopt.getopt(argv[1:], "n:t:f", ["notebook=", "tag=", "force"])
		for op, value in opts:
			if op in ("-n", "--notebook"):
				self.arg_notebook = value
				debug.message(debug.DEBUG, "notebook is ", value)
			elif op in ("-t", "--tag"):
				self.arg_tags = arguments.get_multi_arg(value)
				debug.message(debug.DEBUG, "tag is ", value)
			elif op in ("-f", "--force"):
				self.arg_force = True
				debug.message(debug.DEBUG, "force update")

		self.arg_notes = args
		debug.message(debug.DEBUG, "notes are", self.arg_notes)
		if not self.arg_notes:
			raise errors.UsageError("No note specified")


		# find notespace
		self.notespace = self.target_general.get_notespace(server)

		# add note to notebook
		if self.arg_notebook:
			note = self.add_notes_to_notebook(self.arg_notes, self.arg_notebook, self.arg_force)
		else:
			debug.message(debug.DEBUG, 
					"No notebook specified, using default notebook")
			note = self.add_notes_to_notebook(self.arg_notes, 
					self.notespace.get_default_notebook(), self.arg_force)

		# add tags
		if self.arg_tags:
			self.add_notes_to_tags(note, self.arg_tags, self.arg_force)

		self.notespace.get_database().commit()
	
	# notebook can be class Notebook or notebook path
	def add_notes_to_notebook(self, notes_path, notebook, force_update):
		if type(notebook) == str:
			nb_name = notebook
			notebook = self.notespace.find_notebook(nb_name)
		elif type(notebook) == Notebook:
			pass
		else:
			raise TypeError

		if not force_update:
			# If all the note presented are inserted, but we don't want force update.
			# It should not do any update for the notebook
			notes = []
			need_update = False
			for note_path in notes_path:
				note = Note(self.notespace, note_path)
				if not note.get_id() and note.validate_path():
					debug.message(debug.DEBUG, "at least 1 note is not in notespace, need update")
					need_update = True
				else:
					notes.append(note)
			if not need_update:
				return notes

		# So we finally need to update
		notes = []
		if not notebook:
			debug.message(debug.DEBUG, 
					"Automatically creating notebook ", nb_name)
			notebook = self.notespace.create_notebook(nb_name)

		# try to update
		for note_path in notes_path:
			#notes.append(notebook.add_note(note_path, False))
			note = self.update_add_notes_to_notebook(note_path, notebook, force_update)
			if note:
				notes.append(note)

		return notes

	def update_add_notes_to_notebook(self, note_path, notebook, force_update):
		if force_update:
			try:
				note = notebook.update_note(note_path, False)
			except errors.NoSuchRecord:
				note = notebook.add_note(note_path, False)
		else:
			note = notebook.add_note(note_path, False)
		return note

	def add_notes_to_tags(self, notes, tags, force_update):
		if not notes:
			return

		if force_update:
			for note in notes:
				debug.message(debug.DEBUG, "clearing tags for note " + note.get_relpath())
				note.clear_tags(False)

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


