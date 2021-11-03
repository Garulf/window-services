import os
import subprocess
from flox import Flox

try:
    import psutil
except ImportError:
    pass

FILE_DIR = os.path.abspath(os.path.dirname(__file__))
PLUGIN_ROOT = os.path.dirname(FILE_DIR)
ICON_DIR = os.path.join(PLUGIN_ROOT, "icons")
SERVICE_RUNNING = os.path.join(ICON_DIR, "cog-play.png")
SERVICE_STOPPED = os.path.join(ICON_DIR, "cog-stop.png")
SERVICE_START = os.path.join(ICON_DIR, "play.png")
SERVICE_STOP = os.path.join(ICON_DIR, "stop.png")
BAT_FILE = "toggle_service.bat"

class WindowServices(Flox):

    def service_icon(self, service_state):
        if service_state.lower() == "running":
            return SERVICE_RUNNING
        elif service_state.lower() == "stopped":
            return SERVICE_RUNNING



    def query(self, query):
        services = psutil.win_service_iter()
        for service in services:
            if query.lower() in service.name().lower() or query.lower() in service.display_name().lower():
                title = f'{service.name()} ({service.display_name()})'
                # self.logger.info(dir(service))
                self.add_item(
                    title=title,
                    subtitle=service.status().upper().replace("_", " "),
                    icon=self.service_icon(service.status()),
                    context=[service.name()]
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
        subprocess.check_output(f'Powershell -Command "Start-Process "{bat_path}" -ArgumentList "{state}","{service_name}" -Verb RunAs -WindowStyle Hidden', shell=True)

if __name__ == "__main__":
    WindowServices()