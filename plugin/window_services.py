import os
import subprocess
from flox import Flox


import services as s


FILE_DIR = os.path.abspath(os.path.dirname(__file__))
PLUGIN_ROOT = os.path.dirname(FILE_DIR)
ICON_DIR = os.path.join(PLUGIN_ROOT, "icons")
SERVICE_RUNNING = os.path.join(ICON_DIR, "cog-play.png")
SERVICE_STOPPED = os.path.join(ICON_DIR, "cog-stop.png")
SERVICE_START = os.path.join(ICON_DIR, "play.png")
SERVICE_STOP = os.path.join(ICON_DIR, "stop.png")
BAT_FILE = "toggle_service.bat"

class CannotFindFile(Exception):
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
class WindowServices(Flox):

    def service_icon(self, service_state):
        if service_state.lower() == "running":
            return SERVICE_RUNNING
        elif service_state.lower() == "stopped":
            return SERVICE_STOPPED

    def query(self, query):
        services = s.get_services()
        for service in services:
            if query.lower() in service.name.lower() or query.lower() in service.display_name.lower():
                # self.logger.info(dir(service))
                subtitle = f'{service.status.upper().replace("_", " ")} - Press ENTER to toggle service'
                self.add_item(
                    title=str(service),
                    subtitle=subtitle,
                    icon=self.service_icon(service.status),
                    context=[service.name],
                    method='toggle_service',
                    parameters=[service.name, service.status]
                )

    def context_menu(self, data): 
        self.add_item(
            title='Start Service',
            subtitle=f'Start {data[0]} service',
            icon=SERVICE_START,
            method='control_service',
            parameters=[data[0], 'start']
        )
        self.add_item(
            title='Stop Service',
            subtitle=f'Stop {data[0]} service',
            icon=SERVICE_STOP,
            method='control_service',
            parameters=[data[0], 'stop']
        )
        return self._results

    def control_service(self, service_name, state):
        bat_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), BAT_FILE)
        p = subprocess.Popen(f'Powershell -Command "Start-Process "sc" -ArgumentList "{state}","{service_name}" -Verb RunAs -WindowStyle Hidden"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        exit_code = p.wait()
        if exit_code != 0:
            out, err = p.communicate()
            if "canceled" not in str(err):
                self.logger.error(err.decode("utf-8"))

    def toggle_service(self, service_name, status):
        if status.lower() == "running":
            self.control_service(service_name, 'stop')
        elif status.lower() == "stopped":
            self.control_service(service_name, 'start')


if __name__ == "__main__":
    WindowServices()