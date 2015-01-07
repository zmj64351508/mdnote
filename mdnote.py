#!/usr/bin/python
import sys
import cmd_init
import cmd_add
import cmd_list
import cmd_list_notebook
import errors

cmd_dict = {
	"init":cmd_init.Command(),
	"add" :cmd_add.Command(),
	"list":cmd_list.Command(),
	"list_notebook":cmd_list_notebook.Command(),
}

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
