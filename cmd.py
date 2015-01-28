import errors
import sys

class TargetFactory(object):
	def __init__(self, target_list):
		self.targets = target_list

	def Create(self, name):
		#try:
			return self.targets[name]()
		#except Exception:
			#raise errors.UsageError()

class CommandBase(object):
	def main(self, argc, argv):
		print "Command Base main"
		pass

	def server_main(self, server_thread, argc, argv):
		print "Command Base server main"
		pass

	def usage(self):
		print "Command base"

	def output_result(self, server, *strings):
		output = unicode("").encode("utf8")
		for string in strings:
			output += unicode(string).encode("utf8")
		if server:
			server.send_data(output)
		else:
			sys.stdout.write(output)

# Command such as "add <target> xxx"
class CommandWithTarget(CommandBase):
	def __init__(self, target_factory):
		self.target_factory = target_factory

	def get_target(self, argc, argv):
		# at least need command "add <target>"
		if argc < 2:
			self.usage()
			raise error.UsageError()

		target_name = argv[1]
		return self.target_factory.Create(target_name)

	def main(self, argc, argv):
		target = self.get_target(argc, argv)
		target.main(argc - 1, argv[1:])

	def server_main(self, server, argc, argv):
		target = self.get_target(argc, argv)
		target.server_main(server, argc - 1, argv[1:])

	def usage(self):
		print "Command With Target"

# Command such as "init xxx"
class CommandGeneral(CommandBase):
	def usage(self):
		print "General command"


