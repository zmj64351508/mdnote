import sqlite3
import os
import errors
import debug

class DatabaseTable(object):
	def __init__(self, connect, name):
		self.connect = connect
		self.name = name

	def select(self, column, condition):
		return self.connect.execute("SELECT " + column + 
				" FROM " + self.name + " " + condition)

	def select_by_id(self, t_id, column):
		return self.select(column, "WHERE id=" + t_id.__str__())

	def update(self, column_val, condition):
		return self.connect.execute("UPDATE " + self.name + 
				" SET " + column_val + " " + condition)

	def delete(self, condition):
		return self.connect.execute("DELETE FROM " + self.name + " " + condition)

	def update_by_id(self, t_id, column_val):
		return self.update(column_val, "WHERE id=" + t_id.__str__())

	def execute(self, string):
		return self.connect.execute(string)

	def commit(self):
		self.connect.commit()

class NotebookTable(DatabaseTable):
	def __init__(self, connect, name):
		super(NotebookTable, self).__init__(connect, name)

	def create(self):
		self.connect.execute("CREATE TABLE IF NOT EXISTS " + self.name + """ (
				id integer PRIMARY KEY autoincrement, 
				name varchar(10)
			)""")

	def insert(self, nb_name):
		self.connect.execute("INSERT INTO notebook VALUES(null, '" + nb_name + "')")

	#def update_note(self, nb_id, n_id):
		#cursor = self.select_by_id(nb_id, "note_ids")
		#note_ids = cursor.next()[0] +  n_id.__str__() + ";"
		#self.update_by_id(nb_id, "note_ids='" + note_ids + "'")

class NoteTable(DatabaseTable):
	def __init__(self, connect, name):
		super(NoteTable, self).__init__(connect, name)

	def create(self):
		self.connect.execute("CREATE TABLE IF NOT EXISTS " + self.name + """ (
				id integer primary key autoincrement, 
				path varchar(10),
				nb_id integer
			)""")

	def insert(self, n_path, nb_id):
		self.connect.execute("INSERT INTO note VALUES(null, '" + n_path + "', " + str(nb_id) + ")")

	def insert_note(self, note, notebook):
		if type(note) != Note:
			raise TypeError
		debug.message(debug.DEBUG, "Inserting " + note.get_relpath() + " to database")
		self.insert(note.get_relpath(), notebook.get_id())
		#self.connect.execute("INSERT INTO note VALUES(null, '" + note.get_relpath() + "', null, null)")
		cursor = self.select("id", "WHERE path='" + note.get_relpath() + "'")
		n_id = cursor.next()[0]
		note.set_id(n_id)
		return n_id

class TagTable(DatabaseTable):
	def __init__(self, connect, name):
		super(TagTable, self).__init__(connect, name)

	def create(self):
		self.connect.execute("CREATE TABLE IF NOT EXISTS " + self.name + """ (
				id integer primary key autoincrement, 
				name varchar(10)
			)""")
	
	def insert(self, name):
		self.connect.execute("INSERT INTO " + self.name + " VALUES(null, '" + name + "')")

class NoteVsTagTable(DatabaseTable):
	def create(self):
		self.connect.execute("CREATE TABLE IF NOT EXISTS " + self.name + """ (
				id integer primary key autoincrement, 
				n_id integer,
				t_id integer
			)""")

	def insert(self, n_id, t_id):
		self.connect.execute("INSERT INTO " + self.name + 
				" VALUES(null, " + n_id.__str__() + ", " + t_id.__str__() + ")")
	
class Database(object):
	def __init__(self, path):
		self.tables = {
			"notebook":NotebookTable,
			"note":NoteTable,
			#"note_vs_notebook":NoteVsNotebookTable,
			"tag":TagTable,
			"note_vs_tag":NoteVsTagTable,
		}
		self.connect = sqlite3.connect(path)
		# Transfer class to instance
		for name in self.tables:
			self.tables[name] = self.tables[name](self.connect, name)

	def create(self):
		debug.message(debug.DEBUG, "Creating database")
		for name in self.tables:
			self.tables[name].create()
		self.connect.commit()

	def get_connection(self):
		return self.connect

	def get_table(self, name):
		return self.tables[name]

	# insert note to note table
	def new_note(self, note, notebook):
		note_table = self.get_table("note")
		cu = note_table.select("id", "WHERE path='"+note.get_relpath()+"'")
		try:
			record = cu.next()
			n_id = record[0]
		except StopIteration:
			n_id = note_table.insert_note(note, notebook)
		note.set_id(n_id)

	def update_note(self, note, notebook):
		note_table = self.get_table("note")
		if not note.get_id():
			raise errors.NoSuchRecord("update exception: no note " + note.get_relpath())
		note_table.update("nb_id=" + str(notebook.get_id()), "WHERE id='"+str(note.get_id())+"'")

	def update_tag(self, tag, note):
		n_v_t_table = self.get_table("note_vs_tag")
		n_id = note.get_id()
		t_id = tag.get_id()
		if not n_id or not t_id:
			raise errors.NullError("n_id:" + n_id.__str__() + 
					" t_id:" + t_id.__str__() + " Can not be Null")

		cu = n_v_t_table.select("id", "WHERE n_id=" + n_id.__str__() + 
				" AND t_id=" + t_id.__str__())
		try:
			record = cu.next()
			debug.message(debug.WARN, "note: ", note.get_name(),
					" for tag: ", tag.get_name(), 
					" already exists, ignoring")

		except StopIteration:
			n_v_t_table.insert(n_id, t_id)
			
	# insert a new notebook to notebook table
	def new_notebook(self, notebook):
		nb_table = self.get_table("notebook")
		cu = nb_table.select("id", "WHERE name='"+notebook.get_name()+"'")
		try:
			record = cu.next()
			debug.message(debug.WARN, "notebook: ", notebook.get_name(), 
					" already exists, ignoring")
		except StopIteration:
			self.get_table("notebook").insert(notebook.get_name())

	def new_tag(self, tag):
		tag_table = self.get_table("tag")
		cu = tag_table.select("id", "WHERE name='"+tag.get_name()+"'")
		try:
			record = cu.next()
		except StopIteration:
			tag_table.insert(tag.get_name())

	def get_notes_command(self, where):
		return self.connect.execute("""
				SELECT note.id, note.path, notebook.name, tag.id, tag.name from note 
				LEFT JOIN notebook
				ON note.nb_id=notebook.id
				LEFT JOIN note_vs_tag AS nvt
				ON note.id=nvt.n_id
				LEFT JOIN tag
				ON nvt.t_id=tag.id 
				""" + where +
				" ORDER BY note.id "
				)

	def get_notes_by_ids(self, ids):
		note_cond = ""
		for n_id in ids:
			if note_cond:
				note_cond += " OR"
			note_cond += " note.id=" + str(n_id)
		return self.get_notes_command("WHERE " + note_cond)

	def get_notes_record(self, notebook, tags):
		nb_id = None
		notebook_cond = ""
		if notebook:
			notebook_cond = " nb_id=" + str(notebook.get_id())
			nb_id = notebook.get_id()

		t_id = []
		tag_cond = ""
		if tags:
			for tag in tags:
				if tag_cond:
					tag_cond += " OR"
				elif notebook_cond:
					tag_cond += " AND"
				tag_cond += " t_id=" + str(tag.get_id())
				t_id.append(tag.get_id())
			t_id.sort()

		cu = self.connect.execute("""
				SELECT note.id,nb_id,t_id from note 
				LEFT JOIN note_vs_tag as tag 
				ON note.id=tag.n_id 
				WHERE """ + notebook_cond + tag_cond +
				" ORDER BY note.id"
				)
		backup_cu = cu
		result = []
		last_id = None
		this_t_id = []
		this_nb_id = None
		for row in cu:
			# first iteration
			if not last_id:
				if nb_id:
					this_nb_id = row[1]
				if t_id and row[2]:
					this_t_id = [row[2]]
				last_id = row[0]
				continue
			# not a new id
			if row[0] == last_id:
				if t_id and this_t_id[-1] != row[2]:
					this_t_id.append(row[2])
			# new id
			else:
				# compare this_nb_id and this_t_id this 
				if this_nb_id == nb_id and cmp(this_t_id, t_id) == 0:
					result.append(last_id)
				if nb_id:
					this_nb_id = row[1]
				if t_id and row[2]:
					this_t_id = [row[2]]
			last_id = row[0]
		# for the last iteration
		if this_nb_id == nb_id and cmp(this_t_id, t_id) == 0:
			result.append(last_id)
		return result

	def get_notes_detail_by_ids(self, ids):
		cursor = self.get_notes_by_ids(ids)
		return self.get_notes_detail_by_cursor(cursor)

	def get_notes_detail_by_cursor(self, cursor):
		notes_detail = []
		last = None
		for row in cursor:
			# note record has another tag
			if last and last[0] == row[0] and last[3] != row[3]:
				notes_detail[-1]["tag"].append(row[4])
			# new note record
			else:
				notes_detail.append({"path":row[1], "notebook":row[2], "tag":[row[4]]})
			last = row

		return notes_detail

	def get_all_notes_detail(self):
		note_table = self.get_table("note")
		cursor = self.get_notes_command("")
		return self.get_notes_detail_by_cursor(cursor)
		
	def get_note_id(self, note_path):
		db_table = self.get_table("note")
		cu = db_table.select("id", "WHERE path='" + note_path + "'")
		return self.__check_uniq_result(cu)

	def get_notebook_id(self, nb_name):
		db_table = self.get_table("notebook")
		cu = db_table.select("id", "WHERE name='" + nb_name +"'")
		return self.__check_uniq_result(cu)
	
	def get_tag_id(self, tag_name):
		db_table = self.get_table("tag")
		cu = db_table.select("id", "WHERE name='" + tag_name +"'")
		return self.__check_uniq_result(cu)

	def get_all_notebooks(self):
		db_table = self.get_table("notebook")
		cu = db_table.select("id, name", "")
		name = []
		for row in cu:
			name.append(row[1])
		return name

	def get_all_tags(self):
		db_table = self.get_table("tag")
		cu = db_table.select("id, name", "")
		name = []
		for row in cu:
			name.append(row[1])
		return name

	def clear_note_tags(self, note):
		db_table = self.get_table("note_vs_tag")
		db_table.delete("WHERE n_id=" + str(note.get_id()))

	def __check_uniq_result(self, cu):
		found = 0
		this_id = None
		for row in cu:
			if row[0]:
				this_id = row[0]
				found += 1
		if found > 1:
			raise errors.NotUnique()
		return this_id

	def commit(self):
		self.connect.commit()

class Notespace(object):
	def __init__(self):
		self.db_name = "note.db"
		self.default_notebook_name = "default notebook"
		self.default_notebook = None
		self.path = None       # path for this notespace
		self.meta_path = None  # path for the meta data for this notespace
		self.db = None

	def create(self, path):
		if not os.path.isdir(path):
			return

		# We need to create meta path and database at first time
		self.path = os.path.abspath(path)
		self.meta_path = os.path.join(self.path, ".mdnote")
		if not os.path.exists(self.meta_path):
			os.mkdir(self.meta_path)
		
		db_path = self.get_database_path(self.meta_path, self.db_name)
		self.create_database(db_path)

	def create_database(self, db_path):
		self.db = Database(db_path)
		self.db.create()
	
	def find_notespace(self, from_path, up_to_root = True):
		notespace_path = None
		meta_path = None
		path = os.path.abspath(from_path)
		while not notespace_path:
			meta_path = os.path.join(path, ".mdnote")
			if os.path.isdir(meta_path):
				notespace_path = path
				break
			# only find the note space in current directory
			if not up_to_root:
				break
			# otherwise find it in parent directory
			parent_path = os.path.abspath(os.path.join(path, os.pardir))
			if cmp(parent_path, path) == 0:
				break
			path = parent_path

		if not notespace_path:
			return None

		# database should be created with notespace. If there's no database it's an error
		db_path = self.get_database_path(meta_path, self.db_name)
		if os.path.exists(db_path):
			self.db = Database(db_path)
		else:
			return None

		# Everything found ready. Notespace can be used now
		self.path = notespace_path
		self.meta_path = meta_path
		return notespace_path

	# find a note in notespace directory
	def find_note_from_path(self, note_path):
		if not os.path.isabs(note_path):
			note_path = os.path.join(self.path, note_path)
		if os.path.isfile(note_path):
			# Note need to know the relative path
			return Note(self, os.path.relpath(note_path, self.path))
		else:
			return None

	def filter_note_detail(self, notebook, tags):
		path = []
		ids = self.get_database().get_notes_record(notebook, tags)
		if ids:
			return self.get_database().get_notes_detail_by_ids(ids)
		else:
			return None

	def get_all_notes_detail(self):
		return self.get_database().get_all_notes_detail()

	def get_all_notes_path_by_notebook(self, notebook):
		path = []
		cursor = self.get_database().get_all_notes_by_notebook(notebook)
		for row in cursor:
			path.append(row[1])
		return path

	def get_all_notes_path_by_tag(self, tag):
		path = []
		cursor = self.get_database().get_all_notes_by_tag(tag)
		for row in cursor:
			path.append(row[1])
		return path

	def get_all_notebooks(self):
		return self.get_database().get_all_notebooks()
	
	def get_all_tags(self):
		return self.get_database().get_all_tags()

	def exists(self):
		return self.path != None

	def get_path(self):
		return self.path

	def get_meta_path(self):
		return self.meta_path

	def get_database(self):
		return self.db

	def get_database_path(self, meta_path, db_name):
		if meta_path == None or db_name == None:
			return None
		return os.path.join(meta_path, db_name)

	# Whether the notespace has the notebook named given
	def find_notebook(self, nb_name):
		nb = Notebook(self, nb_name)
		return nb.get_self_if_exists()

	def find_tag(self, tag_name):
		tag = Tag(self, tag_name)
		return tag.get_self_if_exists()

	def create_tag(self, tag_name):
		tag = Tag(self, tag_name)
		tag.create()
		return tag

	def create_notebook(self, nb_name):
		notebook = Notebook(self, nb_name)
		notebook.create()
		return notebook

	def create_default_notebook(self):
		self.default_notebook = Notebook(self, self.default_notebook_name)
		self.default_notebook.create()
		return self.default_notebook

	def get_default_notebook(self):
		if not self.default_notebook:
			self.default_notebook = self.find_notebook(self.default_notebook_name)
		return self.default_notebook

class NoteObject(object):
	def __init__(self, notespace):
		assert(notespace != None)
		self.notespace = notespace
		self.id = self.update_id()

	def get_database(self):
		db = self.notespace.get_database()
		if not db:
			raise errors.NotFoundError("No database")
		return db

	def get_id(self):
		if not self.id:
			self.id = self.update_id()
		return self.id

	def exists(self):
		return True if self.get_id() else False

	def get_self_if_exists(self):
		return self if self.exists() else None

	# this should always return the id from database
	def update_id(self):
		raise NotImplementedError

class NoteContainer(NoteObject):
	def __init__(self, notespace, name):
		assert(name != None)
		self.name = name
		super(NoteContainer, self).__init__(notespace)

	def create(self):
		raise NotImplementedError

	def get_name(self):
		return self.name

	def add_note(self, note_path, sync):
		raise NotImplementedError

class Notebook(NoteContainer):
	def create(self):
		self.get_database().new_notebook(self)
		self.get_database().commit()
		self.id = self.get_id()
		debug.message(debug.DEBUG, "Creating Notebook: ", self.name, " id: ", self.id)

	def notepath_to_note(self, note_path):
		# find note if comes the string as note's name
		note_path = os.path.normpath(note_path)
		if os.path.isabs(note_path):
			note_path = os.path.relpath(note_path, self.notespace.get_path())
		note = self.notespace.find_note_from_path(note_path)
		if not note:
			debug.message(debug.WARN, "Can not find note ", note_path)
		return note

	def update_note(self, note_path, sync):
		note = self.notepath_to_note(note_path)
		if note:
			self.get_database().update_note(note, self)
			if sync:
				self.get_database().commit()
		return note

	def add_note(self, note_path, sync):
		note = self.notepath_to_note(note_path)
		if note:
			self.get_database().new_note(note, self)
			#self.get_database().update_notebook(self, note)
			if sync:
				self.get_database().commit()
		return note

	def update_id(self):
		self.id = self.get_database().get_notebook_id(self.name)
		return self.id

class Tag(NoteContainer):
	def create(self):
		self.get_database().new_tag(self)
		self.get_database().commit()
		self.id = self.get_id()
		debug.message(debug.DEBUG, "Creating Tag: ", self.name, " id: ", self.id)

	# Note is already in the note table and linked with notebook
	def add_note(self, note, sync):
		if type(note) != Note:
			raise TypeError
		if note:
			self.get_database().update_tag(self, note)
			if sync:
				self.get_database().commit()
		else:
			raise errors.NullError
		return note

	def update_note(self, note, sync):
		if type(note) != Note:
			raise TypeError

	def update_id(self):
		self.id = self.get_database().get_tag_id(self.name)
		return self.id

class Note(NoteObject):
	def __init__(self, notespace, note_path):
		self.relpath = os.path.relpath(note_path, notespace.get_path())
		self.name = os.path.basename(note_path)
		super(Note, self).__init__(notespace)

	def update_id(self):
		self.id = self.get_database().get_note_id(self.relpath)
		return self.id

	def set_id(self, n_id):
		self.id = n_id
	
	def get_relpath(self):
		return self.relpath

	def get_name(self):
		return self.name

	def validate_path(self):
		note = self.notespace.find_note_from_path(self.relpath)
		if note:
			return True
		else:
			return False

	def clear_tags(self, sync):
		self.get_database().clear_note_tags(self)
		if sync:
			self.get_database().commit()



