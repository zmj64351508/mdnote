#!/usr/bin/python

import sys, os, subprocess, re, socket

show_result = True

ok_count = 0
fail_count = 0

def run_cmd(command, verbose, expected_result=""):
	global ok_count
	global fail_count
	if verbose:
		print "#### <COMMOND>", command
	if show_result:
		os.system(command)

	if expected_result:
		try:
			output = subprocess.check_output(command, shell=True)
			match = re.findall(r'^[^(\[DEBUG\])].*$', output, re.M)
			#for a in match:
			result = ""
			for line in match:
				result += line + '\n'
			if cmp(result, expected_result) == 0:
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"
		except subprocess.CalledProcessError as e:
			#print "return code is ", e.returncode, "expected is ", int(expected_result)
			if int(e.returncode) == expected_result:
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"

	else:
		os.system(command + "> /dev/null")

def run_sub_cmd_noserver(sub_command, verbose, expected_result=""):
	run_cmd(os.path.join(os.pardir, "mdnote.py ") + sub_command, verbose, expected_result)

def run_sub_cmd_server(sub_command, verbose, expected_result=""):
	global ok_count
	global fail_count
	global con
	if verbose:
		print "$$$$ <COMMOND>", sub_command
	if sub_command[-1] != "\n":
		sub_command += "\n"

	output = []
	con.send(sub_command)
	buf = ""
	while 1:
		data = con.recv(1024)
		if not data:
			exit()
		sys.stdout.write(data)
		buf += data
		last_packet = data.strip().split("\n")[-1]
		if last_packet.find("<return>") == 0:
			output = buf.strip().split("\n")
			break
	if expected_result:
		retval = output[-1][len("<return>"):] 
		if cmp(retval, "None") == 0:
			pass
		elif int(retval) != 0:
			if int(retval) == expected_result:
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"
			return
		output = output[:-1]
		result = ""
		for line in output:
			result += line + "\n"

		print "##############################"
		print result
		print "##############################"
		if cmp(result, expected_result) == 0:
			ok_count += 1
			print "\033[0;32mOK\033[0m"
		else:
			fail_count += 1
			print "\033[0;31mFail\033[0m"

notebook_count = 2
note_per_notebook = 3

start_dir = os.getcwd()
test_dir = "test_dir"
con = None

def run_test_case(is_server):
	global ok_count
	global fail_count
	if is_server:
		run_sub_cmd = run_sub_cmd_server
		#run_sub_cmd("server", False)
		global con
		con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		con.connect(("127.0.0.1", 46000))
	else:
		run_sub_cmd = run_sub_cmd_noserver

	os.chdir(start_dir)
	run_cmd("rm -rf " + test_dir, False)
	os.makedirs(test_dir)
	os.chdir(test_dir)

	run_cmd("touch note_exist_1 note_exist_2 note_exist_3", True)
	run_cmd("touch note_new_1 note_new_2 note_new_3", True)
	run_sub_cmd("init " + os.getcwd(), True)
	if is_server:
		run_sub_cmd('open ' + os.getcwd(), True)
	# add -n without -f, all notes are not in notespace
	run_sub_cmd("add note -n notebook_exist note_exist_1 note_exist_2 note_exist_3", True)
	run_sub_cmd("list note -d", True, 
	"note_exist_1|notebook_exist|\n"\
	"note_exist_2|notebook_exist|\n"\
	"note_exist_3|notebook_exist|\n"\
	)
	# add -n without -f
	# 1. all notes are in notespace
	# 2. new notebook specified
	run_sub_cmd("add note -n notebook_not_exist note_exist_1 note_exist_2 note_exist_3", True)
	run_sub_cmd("list note -d", True, 
	"note_exist_1|notebook_exist|\n"\
	"note_exist_2|notebook_exist|\n"\
	"note_exist_3|notebook_exist|\n"\
	)
	run_sub_cmd("list notebook", True, 
	"default notebook\n"\
	"notebook_exist\n"\
	)

	# add -n without -f
	# 1. just 1 note are not in notespace, but didn't exist in directory
	# 2. new notebook specified
	run_sub_cmd("add note -n notebook_not_exist not_exist note_exist_2 note_exist_3", True)
	run_sub_cmd("list note -d", True,
	"note_exist_1|notebook_exist|\n"\
	"note_exist_2|notebook_exist|\n"\
	"note_exist_3|notebook_exist|\n"\
	)
	run_sub_cmd("list notebook", True, 
	"default notebook\n"\
	"notebook_exist\n"\
	)

	# add -n without -f
	# 1. just 1 note are not in notespace
	# 2. new notebook specified
	run_sub_cmd("add note -n new_notebook note_new_1 note_exist_2 note_exist_3", True)
	run_sub_cmd("list note -d", True,
	"note_exist_1|notebook_exist|\n"\
	"note_exist_2|notebook_exist|\n"\
	"note_exist_3|notebook_exist|\n"\
	"note_new_1|new_notebook|\n"\
	)
	run_sub_cmd("list notebook", True, 
	"default notebook\n"\
	"notebook_exist\n"\
	"new_notebook\n"\
	)

	# add -n -f
	# 1. just 1 note are not in notespace
	run_sub_cmd("add note -f -n new_notebook note_exist_1 note_exist_2 note_exist_3 note_new_2", True)
	run_sub_cmd("list note -d", True,
	"note_exist_1|new_notebook|\n"\
	"note_exist_2|new_notebook|\n"\
	"note_exist_3|new_notebook|\n"\
	"note_new_1|new_notebook|\n"\
	"note_new_2|new_notebook|\n"\
	)

	# add -n -f
	# 1. just 1 note are not in notespace, but not exist
	# 2. new notebook specified
	run_sub_cmd("add note -f -n new_notebook_2 note_exist_1 not_exist", True)
	run_sub_cmd("list note -d", True,
	"note_exist_1|new_notebook_2|\n"\
	"note_exist_2|new_notebook|\n"\
	"note_exist_3|new_notebook|\n"\
	"note_new_1|new_notebook|\n"\
	"note_new_2|new_notebook|\n"\
	)

	# add -n -f
	# 1. just 1 note are not in notespace
	# 2. new notebook specified
	run_sub_cmd("add note -f -n new_notebook_2 note_exist_1 note_new_3", True)
	run_sub_cmd("list note -d", True,
	"note_exist_1|new_notebook_2|\n"\
	"note_exist_2|new_notebook|\n"\
	"note_exist_3|new_notebook|\n"\
	"note_new_1|new_notebook|\n"\
	"note_new_2|new_notebook|\n"\
	"note_new_3|new_notebook_2|\n"\
	)

	run_cmd("rm -rf ./* .mdnote", False)

	# common test
	os.makedirs("sub_dir")

	for i in range(3):
		run_cmd("touch default_" + str(i), False)

	for notebook_idx in range(notebook_count):
		for note_idx in range(note_per_notebook):
			run_cmd("touch notebook_" + str(notebook_idx) + "_" + str(note_idx), False)

	run_sub_cmd('init ' + os.getcwd(), True)
	if is_server:
		run_sub_cmd('open ' + os.getcwd(), True)

	# not specified notes
	run_sub_cmd('add note -n notebook1', True, 2)

	# not existed file
	run_sub_cmd('add note not_existed', True)

	# different path
	run_sub_cmd('add note default_0', True)
	run_sub_cmd('add note ./default_1', True)
	run_sub_cmd('add note ' + os.path.abspath("default_2"), True)

	# sub directory
	run_cmd('touch sub_dir/sub0 sub_dir/sub1 sub_dir/sub2', False)
	run_sub_cmd('add note sub_dir/sub0', True)
	run_sub_cmd('add note ./sub_dir/sub1', True)
	run_sub_cmd('add note ' + os.path.abspath("sub_dir/sub2"), True)
	run_sub_cmd('list note -d', True, 
	"default_0|default notebook|\n"\
	"default_1|default notebook|\n"\
	"default_2|default notebook|\n"\
	"sub_dir/sub0|default notebook|\n"\
	"sub_dir/sub1|default notebook|\n"\
	"sub_dir/sub2|default notebook|\n"\
	)

	run_sub_cmd('add note -t default1 default_1', True)
	run_sub_cmd('add note -t default1 default_2', True)
	run_sub_cmd('add note -t default2 default_1', True)

	# add notes
	run_sub_cmd('add note -n notebook_0 notebook_0_0 notebook_0_2 notebook_0_1', True)
	run_sub_cmd('add note -n notebook_1 notebook_1_1 notebook_1_0 notebook_1_2', True)
	run_sub_cmd('add note -n notebook_1 -t "default1" notebook_1_1', True)
	run_sub_cmd('add note -n notebook_1 -t "default1; default2" notebook_1_2', True)

	run_sub_cmd('list note', True,
	"default_0\n"\
	"default_1\n"\
	"default_2\n"\
	"sub_dir/sub0\n"\
	"sub_dir/sub1\n"\
	"sub_dir/sub2\n"\
	"notebook_0_0\n"\
	"notebook_0_2\n"\
	"notebook_0_1\n"\
	"notebook_1_1\n"\
	"notebook_1_0\n"\
	"notebook_1_2\n"\
	)
	run_sub_cmd('list note -d', True,
	"default_0|default notebook|\n"\
	"default_1|default notebook|default1;default2;\n"\
	"default_2|default notebook|default1;\n"\
	"sub_dir/sub0|default notebook|\n"\
	"sub_dir/sub1|default notebook|\n"\
	"sub_dir/sub2|default notebook|\n"\
	"notebook_0_0|notebook_0|\n"\
	"notebook_0_2|notebook_0|\n"\
	"notebook_0_1|notebook_0|\n"\
	"notebook_1_1|notebook_1|default1;\n"\
	"notebook_1_0|notebook_1|\n"\
	"notebook_1_2|notebook_1|default1;default2;\n"\
	)

	run_sub_cmd('list note -n notebook_1', True,
	"notebook_1_1\n"\
	"notebook_1_0\n"\
	"notebook_1_2\n"\
	)
	run_sub_cmd('list note -n "default notebook"', True,
	"default_0\n"\
	"default_1\n"\
	"default_2\n"\
	"sub_dir/sub0\n"\
	"sub_dir/sub1\n"\
	"sub_dir/sub2\n"\
	)
	run_sub_cmd('list note -t default1', True, 
	"default_1\n"\
	"default_2\n"\
	"notebook_1_1\n"\
	"notebook_1_2\n"\
	) 
	run_sub_cmd('list note -t "default1; default2"', True, 
	"default_1\n"\
	"notebook_1_2\n"\
	) 
	run_sub_cmd('list note -d -n notebook_1 -t "default1; default2"', True,
	"notebook_1_2|notebook_1|default1;default2;\n") 


	run_sub_cmd('list note -n not_exsit_nb', True, 4)

	run_sub_cmd('list notebook', True,
	"default notebook\n"\
	"notebook_0\n"\
	"notebook_1\n"\
	)

	run_sub_cmd('list tag', True,
	"default1\n"\
	"default2\n"\
	)

	print "====== Result ========"
	print "Success:", ok_count
	print "   Fail:", fail_count

if __name__ == "__main__":
	run_test_case(False)
	run_test_case(True)
