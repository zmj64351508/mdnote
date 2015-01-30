import os
import socket
import traceback
import threading
import getopt
#import select
import debug
from cmd import *
from notebook import Notebook
from notebook import Notespace
import signal


host = ""
port = 46000

class Main(CommandGeneral):
	def __init__(self, general_commands):
		super(Main, self).__init__()
		self.notebooks = {}
		self.core = Core(general_commands)
		self.auto_exit = False

	def main(self, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "", ["auto-exit"])
		for op, value in opts:
			if op in ("--auto-exit"):
				self.auto_exit = True

		self.core.start(self.auto_exit)
						
	def usage(self):
		print "usage: mdnote core"

def kill_handler(signal, frame):
	global core_socket
	debug.message(debug.INFO, "exit because of signal")
	core_socket.close()
	try:
		debug.message(debug.INFO, "wait children")
		os.wait()
	except OSError:
		pass
	sys.exit(0)

def break_handler(signal, frame):
	pass

class Core(object):
	def __init__(self, general_commands):
		self.general_commands = general_commands
		self.threads_lock = threading.Lock()
		self.threads = []

	def check_alive_thread(self):
		for thread in self.threads:
			if not thread.isAlive():
				self.threads.remove(thread)
		return len(self.threads)

	def start(self, auto_exit):
		debug.message(debug.DEBUG, "starting core")
		core = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#core.setblocking(False)
		#core.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		core.bind((host, port))
		core.listen(0)

		inputs = [core]
		outputs = []
		self.output_buffer = {}
		timeout = 5

		# need to handler signal
		global core_socket
		core_socket = core
		signal.signal(signal.SIGINT, kill_handler)
		signal.signal(signal.SIGTERM, kill_handler)

		debug.message(debug.DEBUG, "started core, listening")
		while True:
			try:
				connection, client_addr = core.accept()
			except socket.error:
				debug.message(debug.DEBUG, "accept is interrupted")
			else:
				debug.message(debug.DEBUG, "new client ", client_addr, " accepted.")
				self.threads_lock.acquire()
				thread = CoreThread(self, connection, client_addr, self.general_commands, auto_exit)
				self.threads.append(thread)
				self.threads_lock.release()
				thread.start()

		"""
		while True:
			readable, writable, exceptional = select.select(inputs, outputs, inputs, None)
			if not (readable or writable or exceptional):
				debug.message(debug.ERROR, "Time out")
				continue

			for fd in readable:
				if fd is core:
					connection, client_addr = fd.accept()
					connection.setblocking(False)
					inputs.append(connection)
					outputs.append(connection)
					client_name = self.make_client_name(client_addr)
					self.output_buffer[client_name] = []
				else:
					client_name = self.make_client_name(fd.getpeername())
					data = fd.recv(1024)
					self.parse_input(client_name, data)
					if data:
						debug.message(debug.DEBUG, "received data from ", fd.getpeername())
					else:
						debug.message(debug.DEBUG, "closing ", fd.getpeername())
						inputs.remove(fd)
						outputs.remove(fd)
						self.output_buffer[client_name] = None
						fd.close()

			for fd in writable:
				try:
					client_name = self.make_client_name(fd.getpeername())
				except socket.error:
					continue

				for message in self.output_buffer[client_name]:
					fd.send(message)
				self.output_buffer[client_name] = []

			for s in exceptional:
				pass
		"""

open_lock = threading.Lock()

class CoreCommand(object):
	def __init__(self, general_commands):
		self.commands = {
			"open":self.do_open,
			"init":self.do_init,
			"close":self.do_close,
		}
		self.notespace = None
		self.general_commands = general_commands

	def do_open(self, thread, argc, argv):
		global open_lock
		open_lock.acquire()

		if argc <= 1:
			path = os.getcwd()
		else:
			path = argv[1].decode("utf8").encode(sys.getfilesystemencoding())

		if not os.path.isabs(path):
			raise errors.UsageError("open must use absolute path")

		if self.notespace:
			self.notespace.close
		self.notespace = Notespace()
		if not self.notespace.find_notespace(path, up_to_root = False):
			debug.message(debug.ERROR, "No notespace found")
			open_lock.release()
			return -1

		open_lock.release()
		return 0

	def do_init(self, thread, argc, argv):
		global open_lock
		open_lock.acquire()
		if self.notespace:
			self.notespace.close()
		self.notespace = Notespace()
		result = self.general_commands[argv[0]].core_main(thread, argc, argv)
		open_lock.release()
		return result

	def do_close(self, thread, argc, argv):
		debug.message(debug.DEBUG, "do_close")
		thread.stop()
		return 0

	def close(self):
		if self.notespace:
			self.notespace.close()
		self.notespace = None

	def run_command(self, thread, argc, argv):
		debug.message(debug.DEBUG, "run command: ", argv)
		try:
			cmd = self.commands[argv[0]]
		except KeyError:
			cmd = self.general_commands[argv[0]].core_main
		return cmd(thread, argc, argv)

	def get_notespace(self):
		return self.notespace

class CoreThread(threading.Thread):
	def __init__(self, core, connection, client_addr, general_commands, auto_exit):
		super(CoreThread, self).__init__()
		self.connection = connection
		self.client_addr = client_addr
		self.__stopped = True
		self.output_buffer = []
		self.auto_exit = auto_exit
		self.core_commands = CoreCommand(general_commands)
		self.core = core

	def run(self):
		try:
			self.__stopped = False
			while not self.__stopped:
				try:
					data = self.connection.recv(1024)
				except socket.error:
					traceback.print_exc()
					break
				if not data:
					debug.message(debug.INFO, "no data")
					break
				cmds = data.strip().split("\n")
				for cmd in cmds:
					self.parse_input(cmd)
					self.actual_send_result()
		except Exception:
			traceback.print_exc()
		finally:
			debug.message(debug.INFO, "closing connection")
			self.core_commands.close()
			self.connection.close()
			if self.auto_exit:
				# whether we are the only thread
				self.core.threads_lock.acquire()
				thread_count = self.core.check_alive_thread()
				debug.message(debug.DEBUG, "thread count is ", thread_count)
				if thread_count == 1:
					debug.message(debug.INFO, "terminate self")
					os.kill(os.getpid(), signal.SIGTERM)
				self.core.threads_lock.release()

	def stop(self):
		self.__stopped = True

	def parse_input(self, data):
		if not data:
			return

		args = self.format_args(data)
		try:
			result = self.core_commands.run_command(self, len(args), args)
			assert(result != None)
			self.send_return_value(result)
		except errors.UsageError as e:
			self.send_error(e)
			self.send_return_value(2)
		except errors.NoSuchRecord as e:
			self.send_error(e)
			self.send_return_value(4)
		except errors.ErrorBase as e:
			self.send_error(e)
			self.send_return_value(3)

	def is_white_space(self, char):
		if char == " " or char == "\t" or char == "\n":
			return True
		else:
			return False

	def format_args(self, args):
		output = []
		next_quote = None
		start = 0
		i = 0
		while i < len(args):
			if next_quote == None:
				# ignore while space first
				start = i
				while i < len(args) and self.is_white_space(args[i]):
					i += 1
					start = i

				if args[i] == "\"":
					next_quote = "\""
				elif args[i] == "'":
					next_quote = "'"
				else:
					while i < len(args) and not self.is_white_space(args[i]):
						i += 1
					output.append(args[start:i])

			elif args[i] == next_quote:
				output.append(args[start+1:i])
				next_quote = None
			i += 1
		return output


	def send_error(self, exception):
		self.send_data("<error>" + exception.__str__() + "\n")

	def send_return_value(self, retval):
		self.send_data("<return>" + str(retval) + "\n")

	def send_data(self, string):
		debug.message(debug.DEBUG, "sending ", string)
		self.output_buffer.append(string)

	def actual_send_result(self):
		for data in self.output_buffer:
			self.connection.send(data)
		self.output_buffer = []

	def get_notespace(self):
		return self.core_commands.get_notespace()


