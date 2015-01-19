#!/usr/bin/python

import sys, os, subprocess, re, socket, time
try:
	import colorama
	has_colorama = True
except:
	has_colorama = False
	print "Haven't colorama, printing without color on NOT ANSI color shell"
	print "You may want to install colorama through: pip install colorama"
	print ""


show_result = True

ok_count = 0
fail_count = 0

def cmp_result(actual, expected):
	actual_len = len(actual)
	expected_len = len(expected)
	if actual_len != expected_len:
		return False

	i = 0
	while i < actual_len:
		# ignoring None
		if expected[i] is None:
			i += 1
			continue
		if cmp(expected[i], actual[i]) != 0:
			return False
		i += 1

	return True

def run_cmd(command, verbose, *expected_result):
	global ok_count
	global fail_count
	if verbose:
		print "#### <COMMOND>", command
	if show_result:
		os.system(command)

	if expected_result:
		if type(expected_result[0]) is list:
			expected_result = tuple(expected_result[0])

		try:
			output = subprocess.check_output(command, shell=True)
			match = re.findall(r'^[^(\[DEBUG\])].*$', output, re.M)

			# if running on Windows, each line is ended by a '\r'
			i = 0
			while i < len(match):
				if match[i][-1] == '\r':
					match[i] = match[i][:-1]
				i += 1

			print "##################"
			print match
			print "##################"
			print expected_result
			print "##################"
			#if cmp(tuple(match), expected_result) == 0:
			if cmp_result(tuple(match), expected_result):
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"
		except subprocess.CalledProcessError as e:
			#print "return code is ", e.returncode, "expected is ", int(expected_result)
			if int(e.returncode) == expected_result[0]:
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"

	else:
		os.system(command + "> /dev/null")

def run_sub_cmd_noserver(sub_command, verbose, *expected_result):
	run_cmd(os.path.join(os.pardir, "mdnote.py ") + sub_command, verbose, *expected_result)

def run_sub_cmd_server(sub_command, verbose, *expected_result):
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
			print "Connection broken"
			exit()
		sys.stdout.write(data)
		buf += data
		last_packet = data.strip().split("\n")[-1]
		if last_packet.find("<return>") == 0:
			output = buf.strip().split("\n")
			break
	if expected_result:
		if type(expected_result[0]) is list:
			expected_result = tuple(expected_result[0])

		retval = output[-1][len("<return>"):] 
		if cmp(retval, "None") == 0:
			pass
		elif int(retval) != 0:
			if int(retval) == expected_result[0]:
				ok_count += 1
				print "\033[0;32mOK\033[0m"
			else:
				fail_count += 1
				print "\033[0;31mFail\033[0m"
			return
		output = output[:-1]

		#if cmp(tuple(output), expected_result) == 0:
		if cmp_result(tuple(output), expected_result):
			ok_count += 1
			print "\033[0;32mOK\033[0m"
		else:
			fail_count += 1
			print "\033[0;31mFail\033[0m"

notebook_count = 2
note_per_notebook = 3

run_sub_cmd = None
start_dir = os.getcwd()
test_dir = "test_dir"
con = None
targets = [
	"add note -n",
	"add note -t",
	"list note",
	"general"
]

def remove(src):
	'''delete files and folders'''
	if os.path.isfile(src):
		os.remove(src)
	elif os.path.isdir(src):
		for item in os.listdir(src):
			itemsrc=os.path.join(src,item)
			remove(itemsrc) 
		os.rmdir(src)

def create_empty_files(*file_names):
	for file_name in file_names:
		f = open(file_name, "w")
		f.close()

def init_notespace(is_server):
	global con
	if is_server:
		try:
			con.close()
		except Exception:
			pass

	os.chdir(start_dir)
	# wait for a while, otherwise we may not able to delete the directory
	time.sleep(0.5)
	remove(test_dir)
	os.makedirs(test_dir)
	os.chdir(test_dir)

	if is_server:
		con = socket.socket()
		con.connect(("localhost", 46000))
	run_sub_cmd("init " + os.getcwd(), True)


def result_list_detail(*results):
	actual_result = []
	for result in results:
		actual_result.append("PATH: " + result["path"])
		actual_result.append("NOTEBOOK: " + result["notebook"])
		actual_result.append("TAG: " + result["tag"])
		# ignoring create time and modify time
		actual_result.append(None) #"CREATE TIME: " + result["create_time"]
		actual_result.append(None) #"MODIFY TIME: " + result["modify_time"])
		actual_result.append(" ")
	return actual_result

def run_test_case(is_server):
	global ok_count
	global fail_count
	global run_sub_cmd
	if is_server:
		run_sub_cmd = run_sub_cmd_server
		#run_sub_cmd("server", False)
		global con
		con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	else:
		run_sub_cmd = run_sub_cmd_noserver

	if "add note -n" in targets:
		init_notespace(is_server)

		create_empty_files("note_exist_1", "note_exist_2", "note_exist_3")
		create_empty_files("note_new_1", "note_new_2", "note_new_3")
		# add -n without -f, all notes are not in notespace
		run_sub_cmd("add note -n notebook_exist note_exist_1 note_exist_2 note_exist_3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_2", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_3", "notebook":"notebook_exist", "tag":""},
		))

		# add -n without -f
		# 1. all notes are in notespace
		# 2. new notebook specified
		run_sub_cmd("add note -n notebook_not_exist note_exist_1 note_exist_2 note_exist_3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_2", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_3", "notebook":"notebook_exist", "tag":""},
		))
		run_sub_cmd("list notebook", True, 
		"default notebook",
		"notebook_exist",
		)

		# add -n without -f
		# 1. just 1 note are not in notespace, but didn't exist in directory
		# 2. new notebook specified
		run_sub_cmd("add note -n notebook_not_exist not_exist note_exist_2 note_exist_3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_2", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_3", "notebook":"notebook_exist", "tag":""},
		))
		run_sub_cmd("list notebook", True, 
		"default notebook",
		"notebook_exist",
		)

		# add -n without -f
		# 1. just 1 note are not in notespace
		# 2. new notebook specified
		run_sub_cmd("add note -n new_notebook note_new_1 note_exist_2 note_exist_3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_2", "notebook":"notebook_exist", "tag":""},
			{"path":"note_exist_3", "notebook":"notebook_exist", "tag":""},
			{"path":"note_new_1",   "notebook":"new_notebook",   "tag":""},
		))
		run_sub_cmd("list notebook", True, 
		"default notebook",
		"notebook_exist",
		"new_notebook",
		)

		# add -n -f
		# 1. just 1 note are not in notespace
		run_sub_cmd("add note -f -n new_notebook note_exist_1 note_exist_2 note_exist_3 note_new_2", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"new_notebook", "tag":""},
			{"path":"note_exist_2", "notebook":"new_notebook", "tag":""},
			{"path":"note_exist_3", "notebook":"new_notebook", "tag":""},
			{"path":"note_new_1",   "notebook":"new_notebook", "tag":""},
			{"path":"note_new_2",   "notebook":"new_notebook", "tag":""},
		))

		# add -n -f
		# 1. just 1 note are not in notespace, but not exist
		# 2. new notebook specified
		run_sub_cmd("add note -f -n new_notebook_2 note_exist_1 not_exist", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"new_notebook_2", "tag":""},
			{"path":"note_exist_2", "notebook":"new_notebook", "tag":""},
			{"path":"note_exist_3", "notebook":"new_notebook", "tag":""},
			{"path":"note_new_1",   "notebook":"new_notebook", "tag":""},
			{"path":"note_new_2",   "notebook":"new_notebook", "tag":""},
		))
		
		# add -n -f
		# 1. just 1 note are not in notespace
		# 2. new notebook specified
		run_sub_cmd("add note -f -n new_notebook_2 note_exist_1 note_new_3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note_exist_1", "notebook":"new_notebook_2", "tag":""},
			{"path":"note_exist_2", "notebook":"new_notebook", "tag":""},
			{"path":"note_exist_3", "notebook":"new_notebook", "tag":""},
			{"path":"note_new_1",   "notebook":"new_notebook", "tag":""},
			{"path":"note_new_2",   "notebook":"new_notebook", "tag":""},
			{"path":"note_new_3",   "notebook":"new_notebook_2", "tag":""},
		))

	if "add note -t" in targets:
		init_notespace(is_server)
		create_empty_files("note1", "note2", "note3", "note4")

		run_sub_cmd("add note -t tag1 note1 note2", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note1", "notebook":"default notebook", "tag":"tag1;"},
			{"path":"note2", "notebook":"default notebook", "tag":"tag1;"},
		))
		
		# without -f
		run_sub_cmd("add note -t tag2 note1 note2", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note1", "notebook":"default notebook", "tag":"tag1;tag2;"},
			{"path":"note2", "notebook":"default notebook", "tag":"tag1;tag2;"},
		))

		# with -f
		run_sub_cmd("add note -f -t tag2 note1 note3", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note1", "notebook":"default notebook", "tag":"tag2;"},
			{"path":"note2", "notebook":"default notebook", "tag":"tag1;tag2;"},
			{"path":"note3", "notebook":"default notebook", "tag":"tag2;"},
		))
		
		# not exist file
		run_sub_cmd("add note note4", True)
		run_sub_cmd("add note -f -t tag3 not_exist", True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note1", "notebook":"default notebook", "tag":"tag2;"},
			{"path":"note2", "notebook":"default notebook", "tag":"tag1;tag2;"},
			{"path":"note3", "notebook":"default notebook", "tag":"tag2;"},
			{"path":"note4", "notebook":"default notebook", "tag":""},
		))
		run_sub_cmd("list tag", True,
		"tag1",
		"tag2",
		)
	
	if "list note" in targets:
		init_notespace(is_server)
		os.mkdir("sub_dir")
		create_empty_files("note1", "note2", "note3", "note4", "except_note", "sub_dir/sub1", "sub_dir/sub2")
		run_sub_cmd('add note -n notebook1 note1 note2 except_note', True)
		run_sub_cmd('add note -t tag1 note1 note3', True)
		run_sub_cmd('add note -n notebook2 -t tag2 note4 sub_dir/sub1', True)
		run_sub_cmd('add note -n notebook2 -t "tag2;tag3" sub_dir/sub2', True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"note1", "notebook":"notebook1", "tag":"tag1;"},
			{"path":"note2", "notebook":"notebook1", "tag":""},
			{"path":"except_note", "notebook":"notebook1", "tag":""},
			{"path":"note3", "notebook":"default notebook", "tag":"tag1;"},
			{"path":"note4", "notebook":"notebook2", "tag":"tag2;"},
			{"path":os.path.normpath("sub_dir/sub1"), "notebook":"notebook2", "tag":"tag2;"},
			{"path":os.path.normpath("sub_dir/sub2"), "notebook":"notebook2", "tag":"tag2;tag3;"},
		))
		run_sub_cmd("list note -n notebook1", True, 
			"note1",
			"note2",
			"except_note"
		)
		run_sub_cmd("list note -n notebook1 note*", True, 
			"note1",
			"note2",
		)
		run_sub_cmd("list note sub_dir/*", True,
			os.path.normpath("sub_dir/sub1"),
			os.path.normpath("sub_dir/sub2"),
		)
		run_sub_cmd("list note " + os.path.abspath("note1"), True,
			"note1",
		)
		run_sub_cmd("list note ./note1 ../test_dir/note2" , True,
			"note1",
			"note2",
		)
	
	if "general" in targets:
		init_notespace(is_server)
		# common test
		os.makedirs("sub_dir")

		for i in range(3):
			create_empty_files("default_" + str(i))

		for notebook_idx in range(notebook_count):
			for note_idx in range(note_per_notebook):
				create_empty_files("notebook_" + str(notebook_idx) + "_" + str(note_idx))

		run_sub_cmd('init ' + os.getcwd(), True)

		# not specified notes
		run_sub_cmd('add note -n notebook1', True, 2)

		# not existed file
		run_sub_cmd('add note not_existed', True)

		# different path
		run_sub_cmd('add note default_0', True)
		run_sub_cmd('add note ./default_1', True)
		run_sub_cmd('add note ' + os.path.abspath("default_2"), True)

		# sub directory
		create_empty_files("sub_dir/sub0", "sub_dir/sub1", "sub_dir/sub2")
		run_sub_cmd('add note sub_dir/sub0', True)
		run_sub_cmd('add note ./sub_dir/sub1', True)
		run_sub_cmd('add note ' + os.path.abspath("sub_dir/sub2"), True)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"default_0", "notebook":"default notebook", "tag":""},
			{"path":"default_1", "notebook":"default notebook", "tag":""},
			{"path":"default_2", "notebook":"default notebook", "tag":""},
			{"path":os.path.normpath("sub_dir/sub0"), "notebook":"default notebook", "tag":""},
			{"path":os.path.normpath("sub_dir/sub1"), "notebook":"default notebook", "tag":""},
			{"path":os.path.normpath("sub_dir/sub2"), "notebook":"default notebook", "tag":""},
		))

		run_sub_cmd('add note -t default1 default_1', True)
		run_sub_cmd('add note -t default1 default_2', True)
		run_sub_cmd('add note -t default2 default_1', True)

		# add notes
		run_sub_cmd('add note -n notebook_0 notebook_0_0 notebook_0_2 notebook_0_1', True)
		run_sub_cmd('add note -n notebook_1 notebook_1_1 notebook_1_0 notebook_1_2', True)
		run_sub_cmd('add note -n notebook_1 -t "default1" notebook_1_1', True)
		run_sub_cmd('add note -n notebook_1 -t "default1; default2" notebook_1_2', True)

		run_sub_cmd('list note', True,
		"default_0",
		"default_1",
		"default_2",
		os.path.normpath("sub_dir/sub0"),
		os.path.normpath("sub_dir/sub1"),
		os.path.normpath("sub_dir/sub2"),
		"notebook_0_0",
		"notebook_0_2",
		"notebook_0_1",
		"notebook_1_1",
		"notebook_1_0",
		"notebook_1_2",
		)
		run_sub_cmd("list note -d", True, result_list_detail(
			{"path":"default_0", "notebook":"default notebook", "tag":""},
			{"path":"default_1", "notebook":"default notebook", "tag":"default1;default2;"},
			{"path":"default_2", "notebook":"default notebook", "tag":"default1;"},
			{"path":os.path.normpath("sub_dir/sub0"), "notebook":"default notebook", "tag":""},
			{"path":os.path.normpath("sub_dir/sub1"), "notebook":"default notebook", "tag":""},
			{"path":os.path.normpath("sub_dir/sub2"), "notebook":"default notebook", "tag":""},
			{"path":"notebook_0_0", "notebook":"notebook_0", "tag":""},
			{"path":"notebook_0_2", "notebook":"notebook_0", "tag":""},
			{"path":"notebook_0_1", "notebook":"notebook_0", "tag":""},
			{"path":"notebook_1_1", "notebook":"notebook_1", "tag":"default1;"},
			{"path":"notebook_1_0", "notebook":"notebook_1", "tag":""},
			{"path":"notebook_1_2", "notebook":"notebook_1", "tag":"default1;default2;"},
		))

		run_sub_cmd('list note -n notebook_1', True,
		"notebook_1_1",
		"notebook_1_0",
		"notebook_1_2",
		)
		run_sub_cmd('list note -n "default notebook"', True,
		"default_0",
		"default_1",
		"default_2",
		os.path.normpath("sub_dir/sub0"),
		os.path.normpath("sub_dir/sub1"),
		os.path.normpath("sub_dir/sub2"),
		)
		run_sub_cmd('list note -t default1', True, 
		"default_1",
		"default_2",
		"notebook_1_1",
		"notebook_1_2",
		) 
		run_sub_cmd('list note -t "default1; default2"', True, 
		"default_1",
		"notebook_1_2",
		) 
		run_sub_cmd('list note -d -n notebook_1 -t "default1; default2"', True, result_list_detail(
			{"path":"notebook_1_2", "notebook":"notebook_1", "tag":"default1;default2;"},
		))

		run_sub_cmd('list note -n not_exsit_nb', True, 4)

		run_sub_cmd('list notebook', True,
		"default notebook",
		"notebook_0",
		"notebook_1",
		)

		run_sub_cmd('list tag', True,
		"default1",
		"default2",
		)

	print "====== Result ========"
	print "Success:", ok_count
	print "   Fail:", fail_count

if __name__ == "__main__":
	if has_colorama:
		colorama.init()
	run_test_case(False)
	run_test_case(True)
