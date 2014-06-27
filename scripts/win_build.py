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
            run(pyver, ["bdist_wheel", "upload"])

if __name__ == "__main__":
    main()
