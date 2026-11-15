from conftest import SC_OUTPUT, FakeShell, sc_block, sc_output
from services import decode, get_services, parse_services

RUSSIAN_KEYS = ("Имя_службы", "Выводимое_имя", "Тип", "Состояние")


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


def test_services_with_localized_field_names_are_listed():
    shell = FakeShell(
        sc=sc_output(
            sc_block("fdPHost", "Хост поставщика функции обнаружения", "RUNNING", keys=RUSSIAN_KEYS),
            sc_block("fhsvc", "Служба истории файлов", "STOPPED"),
            sc_block("FontCache", "Служба кэша шрифтов Windows", "RUNNING", keys=RUSSIAN_KEYS),
        ),
        chcp="Текущая кодовая страница: 866\r\n",
        encoding="cp866",
    )
    assert describe(get_services(shell)) == [
        ("fdPHost", "Хост поставщика функции обнаружения", "RUNNING"),
        ("fhsvc", "Служба истории файлов", "STOPPED"),
        ("FontCache", "Служба кэша шрифтов Windows", "RUNNING"),
    ]


def test_leading_blank_line_does_not_drop_the_first_service():
    assert describe(parse_services("\r\n" + SC_OUTPUT)) == describe(parse_services(SC_OUTPUT))


def test_display_names_containing_a_colon_are_kept_whole():
    services = parse_services(sc_output(sc_block("AcmeSync", "Acme Sync: File Watcher", "STOPPED")))
    assert describe(services) == [("AcmeSync", "Acme Sync: File Watcher", "STOPPED")]


def test_code_page_ignores_trailing_punctuation():
    shell = FakeShell(
        sc=sc_output(sc_block("Spooler", "Druckwarteschlange für Aufträge", "RUNNING")),
        chcp="Aktive Codepage: 850.\r\n",
        encoding="cp850",
    )
    assert describe(get_services(shell)) == [("Spooler", "Druckwarteschlange für Aufträge", "RUNNING")]
