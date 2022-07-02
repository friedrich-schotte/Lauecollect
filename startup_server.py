#!/usr/bin/env python
"""
Main server to start up other servers

Author: Friedrich Schotte
Date created: 2019-09-24
Date last modified: 2022-05-01
Revision comment: Handle dynamic change of local_machine_names
"""
__version__ = "2.1.1"

import logging
from thread_property_2 import thread_property, cancelled


class Startup_Server(object):
    domain_name = "BioCARS"
    name = "startup_server"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        self.running = False

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def servers(self):
        from servers import Servers
        return Servers(self.domain_name)

    @property
    def prefix(self):
        prefix = f"{self.domain_name}:SERVERS."
        prefix = prefix.upper()
        return prefix

    def run(self):
        self.running = True
        from time import sleep
        try:
            while self.running:
                sleep(0.25)
        except KeyboardInterrupt:
            pass
        self.running = False

    @thread_property
    def running(self):
        logging.info(f"Starting IOC: {self.status_PV_names} ...")
        from CAServer import casput
        for PV_name in self.status_PV_names:
            casput(PV_name, 1)

        while not cancelled():
            self.update()
            from sleep import sleep
            if not cancelled():
                sleep(1.0)

        self.cleanup()
        logging.info(f"Stopped IOC: {self.status_PV_names} ...")

    def update(self):
        from CAServer import casput, casmonitor, casdel
        for machine_name in self.machine_names:
            if machine_name in self.local_machine_names:
                for server in self.servers:
                    casput(self.PV_name(machine_name, server, "running"), server.running_locally)
                for server in self.servers:
                    casmonitor(self.PV_name(machine_name, server, "running"), callback=self.handle_PV_change)
                casput(self.status_PV_name(machine_name), 1)
                casmonitor(self.status_PV_name(machine_name), callback=self.handle_PV_change)
            else:
                for server in self.servers:
                    casdel(self.PV_name(machine_name, server, "running"))
                casdel(self.status_PV_name(machine_name))

    def cleanup(self):
        logging.info("Cleaning up...")
        from CAServer import casdel
        for machine_name in self.local_machine_names:
            for server in self.servers:
                casdel(self.PV_name(machine_name, server, "running"))
            casdel(self.status_PV_name(machine_name))
            logging.info("Cleaning up... done.")

    def handle_PV_change(self, PV_name, value, _formatted_value):
        logging.info("Got request %s = %r" % (PV_name, value))
        for machine_name in self.local_machine_names:
            for server in self.servers:
                if PV_name == self.PV_name(machine_name, server, "running"):
                    logging.info("%r.running_locally = %r" % (server, value))
                    server.running_locally = value
            if PV_name == self.status_PV_name(machine_name):
                logging.info("self.running = %r" % value)
                self.running = value

    def PV_name(self, machine_name, server, name):
        """name: server property name 'running' """
        name = f"{self.prefix}{machine_name}.{server.name}.{name}"
        name = name.upper()
        return name

    def status_PV_name(self, machine_name):
        name = f"{self.prefix}{machine_name}.RUNNING"
        name = name.upper()
        return name

    @property
    def status_PV_names(self):
        return [self.status_PV_name(name) for name in self.local_machine_names]

    @property
    def local_machine_names(self):
        return self.servers.local_machine_names

    @local_machine_names.setter
    def local_machine_names(self, value):
        self.servers.local_machine_names = value

    @property
    def machine_names(self):
        return self.servers.machine_names

    @machine_names.setter
    def machine_names(self, value):
        self.servers.machine_names = value


def run(domain_name=None):
    startup_server = Startup_Server(domain_name)
    startup_server.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    # domain_name = "WetLab"
    # domain_name = "TestBench"

    self = Startup_Server(domain_name)
    print('self.local_machine_names = %r' % self.local_machine_names)
    print('self.running = True')
    print('self.running = False')
    print('self.run()')
