import os
import socket
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
		self.server = Server(general_commands)
		self.auto_exit = False

	def main(self, argc, argv):
		if argc < 1:
			self.usage()
			raise errors.UsageError()
		opts, args = getopt.getopt(argv[1:], "", ["auto-exit"])
		for op, value in opts:
			if op in ("--auto-exit"):
				self.auto_exit = True

		self.server.start(self.auto_exit)
						
	def usage(self):
		print "usage: mdnote server"

def kill_handler(signal, frame):
	global server_socket
	debug.message(debug.INFO, "exit because of signal")
	server_socket.close()
	sys.exit(0)

def break_handler(signal, frame):
	pass

class Server(object):
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
		debug.message(debug.DEBUG, "starting server")
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#server.setblocking(False)
		#server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		server.bind((host, port))
		server.listen(0)

		inputs = [server]
		outputs = []
		self.output_buffer = {}
		timeout = 5

		# need to handler signal
		global server_socket
		server_socket = server
		signal.signal(signal.SIGINT, kill_handler)
		signal.signal(signal.SIGTERM, kill_handler)

		debug.message(debug.DEBUG, "started server, listening")
		while True:
			try:
				connection, client_addr = server.accept()
			except socket.error:
				debug.message(debug.DEBUG, "accept is interrupted")
			else:
				debug.message(debug.DEBUG, "new client ", client_addr, " accepted.")
				self.threads_lock.acquire()
				thread = ServerThread(self, connection, client_addr, self.general_commands)
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
				if fd is server:
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

class ServerCommand(object):
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
			path = argv[1]

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
		self.general_commands[argv[0]].server_main(thread, argc, argv)
		open_lock.release()

	def do_close(self, thread, argc, argv):
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
			cmd = self.general_commands[argv[0]].server_main
		return cmd(thread, argc, argv)

	def get_notespace(self):
		return self.notespace

class ServerThread(threading.Thread):
	def __init__(self, server, connection, client_addr, general_commands):
		super(ServerThread, self).__init__()
		self.connection = connection
		self.client_addr = client_addr
		self.__stopped = True
		self.output_buffer = []
		self.server_commands = ServerCommand(general_commands)
		self.server = server

	def run(self):
		self.__stopped = False
		while not self.__stopped:
			data = self.connection.recv(1024)
			if not data:
				break
			cmds = data.strip().split("\n")
			for cmd in cmds:
				self.parse_input(cmd)
				self.actual_send_result()
		debug.message(debug.INFO, "closing connection")
		self.server_commands.close()
		self.connection.close()
		# whether we are the only thread
		self.server.threads_lock.acquire()
		thread_count = self.server.check_alive_thread()
		debug.message(debug.DEBUG, "thread count is ", thread_count)
		if thread_count == 1:
			debug.message(debug.INFO, "terminate self")
			os.kill(os.getpid(), signal.SIGTERM)
		self.server.threads_lock.release()

	def stop(self):
		self.__stopped = True

	def parse_input(self, data):
		if not data:
			return

		args = self.format_args(data)
		try:
			result = self.server_commands.run_command(self, len(args), args)
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
		return self.server_commands.get_notespace()


