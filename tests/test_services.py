from conftest import SC_OUTPUT, FakeShell, sc_block, sc_output
from services import decode, get_services, parse_services


def describe(services):
    return [(service.name, service.display_name, service.status) for service in services]


def test_parses_sc_query_output():
    assert describe(parse_services(SC_OUTPUT)) == [
        ("Spooler", "Print Spooler", "RUNNING"),
        ("wuauserv", "Windows Update", "STOPPED"),
        ("bthserv", "Bluetooth Support Service", "START_PENDING"),
    ]


def test_service_names_with_spaces_are_kept():
    services = parse_services(sc_output(sc_block("Acme Agent", "Acme Backup Agent", "RUNNING")))
    assert str(services[0]) == "Acme Agent (Acme Backup Agent)"


def test_get_services_decodes_with_the_console_code_page():
    shell = FakeShell(
        sc=sc_output(sc_block("WSearch", "Windows-Suche", "RUNNING")),
        chcp="Active code page: 850\r\n",
        encoding="cp850",
    )
    assert describe(get_services(shell)) == [("WSearch", "Windows-Suche", "RUNNING")]
    assert shell.commands == ["chcp", "sc query type= service state= all"]


def test_decode_falls_back_to_utf8_for_unknown_code_pages():
    assert decode("Druckwarteschlange ü".encode("utf-8"), "99999") == "Druckwarteschlange ü"
