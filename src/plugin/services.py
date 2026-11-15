from __future__ import annotations

from typing import List

from shell import Shell

CODE_PAGE_COMMAND = "chcp"
QUERY_COMMAND = "sc query type= service state= all"


class Service:

    def __init__(self, raw: str) -> None:
        self._raw = raw

    def __str__(self) -> str:
        return f"{self.name} ({self.display_name})"

    @property
    def name(self) -> str:
        return self._raw.split("\n")[0].split(":")[1].strip()

    @property
    def display_name(self) -> str:
        return self._raw.split("\n")[1].split(":")[1].strip()

    @property
    def status(self) -> str:
        return self._raw.split("\n")[3].split("  ")[-1].strip()


def code_page(shell: Shell) -> str:
    return shell.output(CODE_PAGE_COMMAND, text=True).split(":")[1].strip()


def decode(output: bytes, page: str) -> str:
    try:
        return output.decode(f"cp{page}")
    except (UnicodeDecodeError, LookupError):
        return output.decode("utf-8", errors="replace")


def parse_services(text: str) -> List[Service]:
    return [Service(block) for block in text.split("\r\n\r\n") if "SERVICE_NAME" in block.split("\n")[0]]


def get_services(shell: Shell) -> List[Service]:
    page = code_page(shell)
    return parse_services(decode(shell.output(QUERY_COMMAND), page))
