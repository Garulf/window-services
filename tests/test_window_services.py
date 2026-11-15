import asyncio
import json
from pathlib import Path

import window_services
from window_services import context_menu, control_service, query, toggle_service

ROOT = Path(__file__).resolve().parents[1]


def run(coroutine):
    return asyncio.run(coroutine)


def as_json(results):
    return [result.to_json() for result in results]


def test_query_matches_name_and_display_name(shell):
    assert [r["Title"] for r in as_json(run(query("spool")))] == ["Spooler (Print Spooler)"]
    assert [r["Title"] for r in as_json(run(query("update")))] == ["wuauserv (Windows Update)"]
    assert len(run(query(""))) == 3


def test_query_result_toggles_service_and_has_context(shell):
    result = as_json(run(query("spooler")))[0]
    assert result["SubTitle"] == "RUNNING - Press ENTER to toggle service"
    assert result["IcoPath"] == str(window_services.SERVICE_RUNNING)
    assert result["ContextData"] == ["Spooler"]
    assert result["JsonRPCAction"] == {
        "Method": "toggle_service",
        "Parameters": ["Spooler", "RUNNING"],
        "DontHideAfterAction": False,
    }


def test_status_icons_and_subtitle(shell):
    results = {r["Title"]: r for r in as_json(run(query("")))}
    assert results["wuauserv (Windows Update)"]["IcoPath"] == str(window_services.SERVICE_STOPPED)
    pending = results["bthserv (Bluetooth Support Service)"]
    assert pending["IcoPath"] is None
    assert pending["SubTitle"] == "START PENDING - Press ENTER to toggle service"


def test_icons_exist():
    for icon in (window_services.SERVICE_RUNNING, window_services.SERVICE_STOPPED, window_services.SERVICE_START, window_services.SERVICE_STOP):
        assert icon.is_file()


def test_context_menu_offers_start_stop_and_restart():
    results = as_json(context_menu(["Acme Agent"]))
    assert [r["Title"] for r in results] == ["Start Service", "Stop Service", "Restart Service"]
    assert [r["JsonRPCAction"]["Parameters"] for r in results] == [
        ["Acme Agent", "start"],
        ["Acme Agent", "stop"],
        ["Acme Agent", "restart"],
    ]
    assert all(r["JsonRPCAction"]["Method"] == "control_service" for r in results)
    assert all(Path(r["IcoPath"]).is_file() for r in results)


def test_restart_runs_restart_service_elevated(shell):
    run(control_service("Acme's Agent", "restart"))
    assert shell.commands == [
        'Powershell -Command "Start-Process powershell -ArgumentList \\"Restart-Service -Name \'Acme\'\'s Agent\'\\" -Verb RunAs -WindowStyle Hidden"'
    ]


def test_control_service_elevates_sc_through_powershell(shell):
    run(control_service("Acme Agent", "start"))
    assert shell.commands == [
        'Powershell -Command "Start-Process sc -ArgumentList \\"start \\"\\"Acme Agent\\"\\"\\" -Verb RunAs -WindowStyle Hidden"'
    ]


def test_toggle_service_stops_running_and_starts_stopped(shell):
    run(toggle_service("Spooler", "RUNNING"))
    run(toggle_service("wuauserv", "STOPPED"))
    run(toggle_service("bthserv", "START_PENDING"))
    assert [command.split("-ArgumentList ")[1].split(" -Verb")[0] for command in shell.commands] == [
        '\\"stop \\"\\"Spooler\\"\\"\\"',
        '\\"start \\"\\"wuauserv\\"\\"\\"',
    ]


def test_failed_command_is_logged_but_cancelled_uac_is_not(shell, caplog):
    logger = window_services.plugin.logger
    logger.addHandler(caplog.handler)
    try:
        shell.result = (1, b"The operation was canceled by the user.")
        run(control_service("Spooler", "stop"))
        assert not caplog.records
        shell.result = (1, b"Access is denied.")
        run(control_service("Spooler", "stop"))
        assert [record.getMessage() for record in caplog.records] == ["Access is denied."]
    finally:
        logger.removeHandler(caplog.handler)


def test_manifest_keeps_plugin_identity():
    manifest = json.loads((ROOT / "data" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["ID"] == "C7E78C47FA5942E4B7972EAD844F5007"
    assert manifest["ActionKeyword"] == "ws"
    assert manifest["Language"] == "python_v2"
    assert manifest["ExecuteFileName"] == "run.py"
