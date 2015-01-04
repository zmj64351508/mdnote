class ErrorBase(Exception):
	def __init__(self, value=""):
		self.value = value
	def __init(self):
		self.value = None
	def __str__(self):
		return self.value

class NotFoundError(ErrorBase):
	pass

class UsageError(ErrorBase):
	pass

class NullError(ErrorBase):
	pass

class NotUnique(ErrorBase):
	pass

class NoSuchRecord(ErrorBase):
	pass
