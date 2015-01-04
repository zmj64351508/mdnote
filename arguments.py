def get_multi_arg(value):
	args = value.split(";")
	for i in range(len(args)):
		args[i] = args[i].strip()
	return args
