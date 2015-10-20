#!/usr/bin/env python
import sys
import subprocess
from microcli import MicroCLI, command, is_string

class Publisher(MicroCLI):

    @classmethod
    def shell_command(cls, cmd, cwd="."):
        lines = []
        popen = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, cwd=cwd)
        for line in iter(popen.stdout.readline, ""):
            line = line.strip()
            lines.append(line)
        popen.wait()
        return (popen.returncode, lines)

    @classmethod
    def get_git_branches(cls, dirname="."):
        cmd = "git branch --list"
        (code, output) = cls.shell_command(cmd, cwd=dirname)
        return [o.split()[-1] for o in output]

    @command()
    def push_branches(self):
        for branch in self.get_git_branches():
            cmd = "git checkout {}; git push".format(branch)
            (code, output) = self.shell_command(cmd)
            print code, output

if __name__ == "__main__":
    Publisher.main(sys.argv)
