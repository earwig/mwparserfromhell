# Build requirements:
#
# Python 2.6-3.2: Visual C++ Express Edition 2008:
#                 http://go.microsoft.com/?linkid=7729279
#
# Python 3.3+: Visual C++ Express Edition 2010:
#              http://go.microsoft.com/?linkid=9709949
#
# x64 builds: Microsoft Windows SDK for Windows 7 and .NET Framework 3.5 SP1:
#             http://www.microsoft.com/en-us/download/details.aspx?id=3138
#
# Python interpreter, 2.6, 2.7, 3.2-3.4:
# https://www.python.org/downloads/
#
# Pip, setuptools, wheel:
# https://bootstrap.pypa.io/get-pip.py
# and run *for each* Python version:
# c:\pythonXX\python get-pip.py
# c:\pythonXX\scripts\pip install wheel
#
# Afterwards, run this script with any of the python interpreters (2.7 suggested)

from __future__ import print_function
import os
from subprocess import call, STDOUT

ENVIRONMENTS = ["26", "27", "32", "33", "34"]

def run(pyver, cmds):
    cmd = [r"C:\Python%s\Python.exe" % pyver, "setup.py"] + cmds
    print(" ".join(cmd), end=" ")

    with open("%s%s.log" % (cmds[0], pyver), "w") as logfile:
        retval = call(cmd, stdout=logfile, stderr=STDOUT, cwd="..")
    if not retval:
        print("[OK]")
    else:
        print("[FAILED (%i)]" % retval)
    return retval

def main():
    path = os.path.split(__file__)[0]
    if path:
        os.chdir(path)

    print("Building Windows wheels for Python %s:" % ", ".join(ENVIRONMENTS))
    for pyver in ENVIRONMENTS:
        print()
        try:
            os.unlink("mwparserfromhell/parser/_tokenizer.pyd")
        except OSError:
            pass

        if run(pyver, ["test"]) == 0:
            run(pyver, ["bdist_wheel", "upload"])  # TODO: add "-s" to GPG sign

if __name__ == "__main__":
    main()
