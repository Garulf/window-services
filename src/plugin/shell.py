from __future__ import annotations

import subprocess
from typing import Tuple


class Shell:
    """Runs commands through the Windows command shell (cmd.exe)."""

    def output(self, command: str, text: bool = False):
        return subprocess.check_output(command, shell=True, text=text)

    def run(self, command: str) -> Tuple[int, bytes]:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        _, err = process.communicate()
        return process.returncode, err
