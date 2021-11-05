import subprocess as sp


class Service(object):

    def __init__(self, service):
        self._raw = service
        self._name = None
        self._display_name = None
        self._status = None

    def __str__(self):
        return f"{self.name} ({self.display_name})"

    @property
    def name(self):
        if self._name is None:
            self._name = self._raw.split("\n")[0].split(":")[1].strip()
        return self._name

    @property
    def display_name(self):
        if self._display_name is None:
            self._display_name = self._raw.split("\n")[1].split(":")[1].strip()
        return self._display_name

    @property
    def status(self):
        if self._status is None:
            self._status = self._raw.split("\n")[3].split("  ")[-1].strip()
        return self._status


def get_services():
    services_list = []

    services = sp.check_output("sc query type= service state= all", shell=True).decode("utf-8").split("\r\n\r\n")
    for service in services:
        if "SERVICE_NAME" in service.split("\n")[0]:
            service = Service(service)
            services_list.append(service)

    return services_list

