#!/usr/bin/python

import sys, os, subprocess, re

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


notebook_count = 2
note_per_notebook = 3

test_dir = "test_dir"
run_cmd("rm -rf " + test_dir, False)
os.makedirs(test_dir)
os.makedirs(test_dir + "/sub_dir")
os.chdir(test_dir)

for i in range(3):
	run_cmd("touch default_" + str(i), False)

for notebook_idx in range(notebook_count):
	for note_idx in range(note_per_notebook):
		run_cmd("touch notebook_" + str(notebook_idx) + "_" + str(note_idx), False)

run_cmd('../mdnote.py init', True)

# not specified notes
run_cmd('../mdnote.py add note -n notebook1', True, 2)

# not existed file
run_cmd('../mdnote.py add note not_existed', True)

# different path
run_cmd('../mdnote.py add note default_0', True)
run_cmd('../mdnote.py add note ./default_1', True)
run_cmd('../mdnote.py add note ~/Program/mdnote/test_dir/default_2', True)

# sub directory
run_cmd('touch sub_dir/sub0 sub_dir/sub1 sub_dir/sub2', False)
run_cmd('../mdnote.py add note sub_dir/sub0', True)
run_cmd('../mdnote.py add note ./sub_dir/sub1', True)
run_cmd('../mdnote.py add note ~/Program/mdnote/test_dir/sub_dir/sub2', True)
run_cmd('../mdnote.py list note -d', True, 
"""default_0|default notebook|
default_1|default notebook|
default_2|default notebook|
sub_dir/sub0|default notebook|
sub_dir/sub1|default notebook|
sub_dir/sub2|default notebook|
""")

run_cmd('../mdnote.py add note -t default1 default_1', True)
run_cmd('../mdnote.py add note -t default1 default_2', True)
run_cmd('../mdnote.py add note -t default2 default_1', True)

# add notes
for notebook_idx in range(notebook_count):
	run_cmd('find -name "notebook_' + str(notebook_idx) + '*" | xargs ../mdnote.py add note -n notebook_' + str(notebook_idx), True)
run_cmd('../mdnote.py add note -n notebook_1 -t "default1" notebook_1_1', True)
run_cmd('../mdnote.py add note -n notebook_1 -t "default1; default2" notebook_1_2', True)

run_cmd('../mdnote.py list note', True,
"""default_0
default_1
default_2
sub_dir/sub0
sub_dir/sub1
sub_dir/sub2
notebook_0_0
notebook_0_2
notebook_0_1
notebook_1_1
notebook_1_0
notebook_1_2
""")
run_cmd('../mdnote.py list note -d', True,
"""default_0|default notebook|
default_1|default notebook|default1;default2;
default_2|default notebook|default1;
sub_dir/sub0|default notebook|
sub_dir/sub1|default notebook|
sub_dir/sub2|default notebook|
notebook_0_0|notebook_0|
notebook_0_2|notebook_0|
notebook_0_1|notebook_0|
notebook_1_1|notebook_1|default1;
notebook_1_0|notebook_1|
notebook_1_2|notebook_1|default1;default2;
"""
)

run_cmd('../mdnote.py list note -n notebook_1', True,
"""notebook_1_1
notebook_1_0
notebook_1_2
""")
run_cmd('../mdnote.py list note -n "default notebook"', True,
"""default_0
default_1
default_2
sub_dir/sub0
sub_dir/sub1
sub_dir/sub2
""")
run_cmd('../mdnote.py list note -t default1', True, 
"""default_1
default_2
notebook_1_1
notebook_1_2
"""
) 
run_cmd('../mdnote.py list note -t "default1; default2"', True, 
"""default_1
notebook_1_2
""") 
run_cmd('../mdnote.py list note -d -n notebook_1 -t "default1; default2"', True,
"""notebook_1_2|notebook_1|default1;default2;
""") 


run_cmd('../mdnote.py list note -n not_exsit_nb', True, 4)

run_cmd('../mdnote.py list notebook', True,
"""default notebook
notebook_0
notebook_1
"""
)

print "====== Result ========"
print "Success:", ok_count
print "   Fail:", fail_count
