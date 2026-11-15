from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from shell import Shell

CODE_PAGE_COMMAND = "chcp"
QUERY_COMMAND = "sc query type= service state= all"

BLOCK_SEPARATOR = re.compile(r"\r?\n\s*\r?\n")
STATE_LINE = re.compile(r":\s*(\d+)\s+(\S+)")
STATES = {
    1: "STOPPED",
    2: "START_PENDING",
    3: "STOP_PENDING",
    4: "RUNNING",
    5: "CONTINUE_PENDING",
    6: "PAUSE_PENDING",
    7: "PAUSED",
}


@dataclass
class Service:
    name: str
    display_name: str
    status: str

    def __str__(self) -> str:
        return f"{self.name} ({self.display_name})"


def field_value(line: str) -> str:
    return line.split(":")[1].strip()


def parse_block(block: str) -> Optional[Service]:
    # sc translates the field names but not their order: name, display name, type, state.
    lines = block.strip().splitlines()
    if len(lines) < 4 or ":" not in lines[0] or ":" not in lines[1]:
        return None
    state = STATE_LINE.search(lines[3])
    if state is None:
        return None
    code, word = state.groups()
    return Service(field_value(lines[0]), field_value(lines[1]), STATES.get(int(code), word))


def code_page(shell: Shell) -> str:
    return shell.output(CODE_PAGE_COMMAND, text=True).split(":")[1].strip()


def decode(output: bytes, page: str) -> str:
    try:
        return output.decode(f"cp{page}")
    except (UnicodeDecodeError, LookupError):
        return output.decode("utf-8", errors="replace")


def parse_services(text: str) -> List[Service]:
    services = (parse_block(block) for block in BLOCK_SEPARATOR.split(text))
    return [service for service in services if service is not None]


def get_services(shell: Shell) -> List[Service]:
    page = code_page(shell)
    return parse_services(decode(shell.output(QUERY_COMMAND), page))
