from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path
from typing import Iterable, List, Optional

from pyflowlauncher import FlowLauncherV2, Plugin, Result
from services import Service, get_services
from shell import Shell

ICON_DIR = Path(__file__).resolve().parent / "icons"
SERVICE_RUNNING = ICON_DIR / "cog-play.png"
SERVICE_STOPPED = ICON_DIR / "cog-stop.png"
SERVICE_START = ICON_DIR / "play.png"
SERVICE_STOP = ICON_DIR / "stop.png"
SERVICE_RESTART = ICON_DIR / "restart.png"

plugin = Plugin(launcher=FlowLauncherV2())
shell = Shell()


async def run_blocking(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))


def service_icon(status: str) -> Optional[Path]:
    if status.lower() == "running":
        return SERVICE_RUNNING
    if status.lower() == "stopped":
        return SERVICE_STOPPED
    return None


def matches(query: str, service: Service) -> bool:
    return query.lower() in service.name.lower() or query.lower() in service.display_name.lower()


def service_results(services: Iterable[Service], query: str) -> List[Result]:
    results = []
    for service in services:
        if not matches(query, service):
            continue
        status = service.status
        results.append(
            Result(
                title=str(service),
                subtitle=f'{status.upper().replace("_", " ")} - Press ENTER to toggle service',
                icon=service_icon(status),
                context_data=[service.name],
            ).add_action(toggle_service, [service.name, status])
        )
    return results


def context_results(service_name: str) -> List[Result]:
    return [
        Result(
            title="Start Service",
            subtitle=f"Start {service_name} service",
            icon=SERVICE_START,
        ).add_action(control_service, [service_name, "start"]),
        Result(
            title="Stop Service",
            subtitle=f"Stop {service_name} service",
            icon=SERVICE_STOP,
        ).add_action(control_service, [service_name, "stop"]),
        Result(
            title="Restart Service",
            subtitle=f"Restart {service_name} service",
            icon=SERVICE_RESTART,
        ).add_action(control_service, [service_name, "restart"]),
    ]


def control_command(service_name: str, state: str) -> str:
    if state == "restart":
        return restart_command(service_name)
    return f'Powershell -Command "Start-Process sc -ArgumentList \\\"{state} \\\"\\\"{service_name}\\\"\\\"\\\" -Verb RunAs -WindowStyle Hidden"'


def restart_command(service_name: str) -> str:
    quoted = service_name.replace("'", "''")
    return f'Powershell -Command "Start-Process powershell -ArgumentList \\\"Restart-Service -Name \'{quoted}\'\\\" -Verb RunAs -WindowStyle Hidden"'


def run_elevated(command: str) -> None:
    exit_code, err = shell.run(command)
    if exit_code != 0 and "canceled" not in str(err):
        plugin.logger.error(err.decode("utf-8", errors="replace"))


@plugin.on_method
async def query(query: str) -> List[Result]:
    services = await run_blocking(get_services, shell)
    return service_results(services, query)


@plugin.on_method
def context_menu(data) -> List[Result]:
    return context_results(data[0])


@plugin.on_method
async def control_service(service_name: str, state: str) -> None:
    await run_blocking(run_elevated, control_command(service_name, state))


@plugin.on_method
async def toggle_service(service_name: str, status: str) -> None:
    if status.lower() == "running":
        await control_service(service_name, "stop")
    elif status.lower() == "stopped":
        await control_service(service_name, "start")
