from __future__ import print_function

import subprocess
import sys
import os

path = os.path.split(__file__)[0]
if path:
	os.chdir(path)

environments = ['26', '27', '32', '33', '34']

target = "pypi" if "--push" in sys.argv else "test"

returnvalues = {}

def run(pyver, cmds, target=None):
	cmd = [r"C:\Python%s\Python.exe" % pyver, "setup.py"] + cmds
	if target:
		cmd += ["-r", target]

	print(" ".join(cmd), end=" ")
	retval = subprocess.call(cmd, stdout=open("%s%s.log" % (cmds[0], pyver), 'w'), stderr=subprocess.STDOUT, cwd="..")
	if not retval:
		print("[OK]")
	else:
		print("[FAILED (%i)]" % retval)
	return retval

run("27", ["register"], target)

if 'failed' in open('register27.log').read():
	raise Exception

for pyver in environments:
	print()
	try:
		os.unlink('mwparserfromhell/parser/_tokenizer.pyd')
	except WindowsError:
		pass
	
	if run(pyver, ["test"]) == 0:
		run(pyver, ["bdist_wheel", "upload"], target)