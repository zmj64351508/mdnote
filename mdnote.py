#!/usr/bin/python
import sys, os
import glob
import errors

# import all module like cmd_* and build cmd_dict like "list":cmd_list
def find_files(dirname, pattern):
	cwd = os.getcwd()
	if dirname:
		os.chdir(dirname)

	result = []
	for filename in glob.iglob(pattern):
		result.append(filename)
	os.chdir(cwd)
	return result

# assume all the cmd_*.py file are under the dir of this file
mdnote_path = os.path.realpath(os.path.dirname(sys.argv[0]))
files = find_files(mdnote_path, "cmd_*.py")
local_vars = locals()
cmd_dict = {}
for file_name in files:
	module_name = os.path.basename(file_name)[:-3]
	local_vars[module_name] = __import__(module_name)
	cmd_dict[module_name[4:]] = local_vars[module_name].Command()

def list_cmds():
	print "commands here"

def main(argc, argv):
	if argc < 2:
		list_cmds()
		exit(1)

	cmd_name = argv[1];
	cmd = cmd_dict.get(cmd_name)
	if not cmd:
		list_cmds()
		exit(1)

	try:
		cmd.run(argc - 1, argv[1:])
	except errors.UsageError as e:
		cmd.usage()
		exit(2)
	except errors.NoSuchRecord as e:
		exit(4)
	except errors.ErrorBase as e:
		exit(3)

	exit(0)


if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
