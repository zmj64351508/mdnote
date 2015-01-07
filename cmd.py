import errors

class TargetFactory(object):
	def __init__(self, target_list):
		self.targets = target_list

	def Create(self, name):
		#try:
			return self.targets[name]()
		#except Exception:
			#raise errors.UsageError()

# Command such as "add <target> xxx"
class CommandWithTarget(object):
	def __init__(self, target_factory):
		self.target_factory = target_factory

	def main(self, argc, argv):
		# at least need command "add <target>"
		if argc < 2:
			self.usage()
			raise error.UsageError()

		target_name = argv[1]
		target = self.target_factory.Create(target_name)
		target.main(argc - 1, argv[1:])

	def usage(self):
		print "usage: mdnote add"

# Command such as "init xxx"
class CommandGeneral(object):
	def __init__(self):
		pass

	def main(self, argc, argv):
		pass

	def usage(self):
		print "General command"
