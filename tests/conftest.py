from __future__ import annotations

from typing import Dict, List, Tuple

import pytest
import window_services


def sc_block(name: str, display_name: str, state: str, keys=("SERVICE_NAME", "DISPLAY_NAME", "TYPE", "STATE")) -> str:
    code = {"STOPPED": 1, "START_PENDING": 2, "STOP_PENDING": 3, "RUNNING": 4}[state]
    lines = [
        f"{keys[0]}: {name}",
        f"{keys[1]}: {display_name}",
        f"        {keys[2]:<19}: 30  WIN32",
        f"        {keys[3]:<19}: {code}  {state} ",
    ]
    if state == "RUNNING":
        lines.append("                                (STOPPABLE, NOT_PAUSABLE, ACCEPTS_SHUTDOWN)")
    lines += [
        "        WIN32_EXIT_CODE    : 0  (0x0)",
        "        SERVICE_EXIT_CODE  : 0  (0x0)",
        "        CHECKPOINT         : 0x0",
        "        WAIT_HINT          : 0x0",
    ]
    return "\r\n".join(lines)


def sc_output(*blocks: str) -> str:
    return "\r\n\r\n".join(blocks) + "\r\n"


SC_OUTPUT = sc_output(
    sc_block("Spooler", "Print Spooler", "RUNNING"),
    sc_block("wuauserv", "Windows Update", "STOPPED"),
    sc_block("bthserv", "Bluetooth Support Service", "START_PENDING"),
)


class FakeShell:
    def __init__(self, sc: str = SC_OUTPUT, chcp: str = "Active code page: 437\r\n", encoding: str = "cp437") -> None:
        self.outputs: Dict[str, object] = {"chcp": chcp, "sc query type= service state= all": sc.encode(encoding)}
        self.result: Tuple[int, bytes] = (0, b"")
        self.commands: List[str] = []

    def output(self, command: str, text: bool = False):
        self.commands.append(command)
        return self.outputs[command]

    def run(self, command: str) -> Tuple[int, bytes]:
        self.commands.append(command)
        return self.result


@pytest.fixture
def shell(monkeypatch):
    fake = FakeShell()
    monkeypatch.setattr(window_services, "shell", fake)
    return fake
