"""
Remote control of thermoelectric chiller by Solid State Cooling Systems,
www.sscooling.com, via RS-323 interface
Model: Oasis 160

Setup to run IOC:
Windows 7 > Control Panel > Windows Firewall > Advanced Settings > Inbound Rules
> New Rule... > Port > TCP > Specific local ports > 5064-5070
> Allow the connection > When does the rule apply? Domain, Private, Public
> Name: EPICS CA IOC
Inbound Rules > python > General > Allow the connection
Inbound Rules > pythonw > General > Allow the connection

Authors: Friedrich Schotte, Nara Dashdorj, Valentyn Stadnytskyi
Date created: 2009-05-28
Date last modified: 2021-12-03
Revision comment: Added: timeout
"""
__version__ = "3.1"

import os
import platform
from logging import info

from oasis_chiller_driver import oasis_chiller_driver

computer_name = platform.node()


class Oasis_Chiller_IOC(object):
    from thread_property_2 import thread_property
    from persistent_property import persistent_property

    name = "oasis_chiller_IOC"
    prefix = persistent_property("prefix", "NIH:CHILLER")
    was_online = False

    def run(self):
        """Run EPICS IOC"""
        from thread_property_2 import cancelled
        self.startup()
        while not cancelled():
            self.update_once()
        self.shutdown()

    running = thread_property(run)

    def start(self):
        """Run EPICS IOC in background"""
        self.running = True

    def stop(self):
        self.running = False

    EPICS_enabled = running

    def startup(self):
        from CAServer import casput, casmonitor
        from numpy import nan
        casput(self.prefix + ".SCAN", oasis_chiller_driver.wait_time)
        casput(self.prefix + ".timeout", oasis_chiller_driver.timeout)
        casput(self.prefix + ".DESC", "Temp")
        casput(self.prefix + ".EGU", "C")
        casput(self.prefix + ".PREC", value=3)
        # Set defaults
        casput(self.prefix + ".VAL", nan)
        casput(self.prefix + ".RBV", nan)

        casput(self.prefix + ".LLM", nan)
        casput(self.prefix + ".HLM", nan)
        casput(self.prefix + ".P1", nan)
        casput(self.prefix + ".I1", nan)
        casput(self.prefix + ".D1", nan)
        casput(self.prefix + ".P2", nan)
        casput(self.prefix + ".I2", nan)
        casput(self.prefix + ".D2", nan)
        casput(self.prefix + ".faults", " ")
        casput(self.prefix + ".fault_code", 0)
        casput(self.prefix + ".COMM", " ")
        casput(self.prefix + ".SCANT", nan)
        # Monitor client-writable PVs.
        casmonitor(self.prefix + ".SCAN", callback=self.monitor)
        casmonitor(self.prefix + ".VAL", callback=self.monitor)
        casmonitor(self.prefix + ".LLM", callback=self.monitor)
        casmonitor(self.prefix + ".HLM", callback=self.monitor)

        casmonitor(self.prefix + ".P1", callback=self.monitor)
        casmonitor(self.prefix + ".I1", callback=self.monitor)
        casmonitor(self.prefix + ".D1", callback=self.monitor)
        casmonitor(self.prefix + ".P2", callback=self.monitor)
        casmonitor(self.prefix + ".I2", callback=self.monitor)
        casmonitor(self.prefix + ".D2", callback=self.monitor)

    def shutdown(self):
        from CAServer import casdel
        casdel(self.prefix)

    def update_once(self):
        from CAServer import casput
        from numpy import nan
        from time import time
        from sleep import sleep
        t = time()
        online = oasis_chiller_driver.online
        if online:
            if online and not self.was_online:
                info("Reading configuration...")
                casput(self.prefix + ".COMM", oasis_chiller_driver.COMM)
                casput(self.prefix + ".VAL", oasis_chiller_driver.VAL)
                casput(self.prefix + ".RBV", oasis_chiller_driver.RBV)
                casput(self.prefix + ".fault_code", oasis_chiller_driver.fault_code)
                casput(self.prefix + ".faults", oasis_chiller_driver.faults)
                casput(self.prefix + ".LLM", oasis_chiller_driver.LLM)
                casput(self.prefix + ".HLM", oasis_chiller_driver.HLM)
                casput(self.prefix + ".P1", oasis_chiller_driver.P1)
                casput(self.prefix + ".I1", oasis_chiller_driver.I1)
                casput(self.prefix + ".D1", oasis_chiller_driver.D1)
                casput(self.prefix + ".P2", oasis_chiller_driver.P2)
                casput(self.prefix + ".I2", oasis_chiller_driver.I2)
                casput(self.prefix + ".D2", oasis_chiller_driver.D2)
                casput(self.prefix + ".SCANT", nan)
                casput(self.prefix + ".processID", value=os.getpid(), update=False)
                casput(self.prefix + ".computer_name", value=computer_name, update=False)
            if len(self.command_queue) > 0:
                attr, value = self.command_queue.popleft()
                setattr(oasis_chiller_driver, attr, value)
                value = getattr(oasis_chiller_driver, attr)
                casput(self.prefix + "." + attr, value)
            else:
                attr = self.next_poll_property
                value = getattr(oasis_chiller_driver, attr)
                casput(self.prefix + "." + attr, value)
                casput(self.prefix + ".SCANT", time() - t)  # post actual scan time for diagnostics
        else:
            sleep(1)
        self.was_online = online

    from collections import deque
    command_queue = deque()

    @property
    def next_poll_property(self):
        name = self.poll_properties[self.poll_count % len(self.poll_properties)]
        self.poll_count += 1
        return name

    poll_properties = ["RBV", "VAL", "fault_code", "faults"]
    poll_count = 0

    def monitor(self, PV_name, value, _char_value):
        """Process PV change requests"""
        from CAServer import casput
        info("%s = %r" % (PV_name, value))
        if PV_name == self.prefix + ".SCAN":
            oasis_chiller_driver.wait_time = float(value)
            casput(self.prefix + ".SCAN", oasis_chiller_driver.wait_time)
        elif PV_name == self.prefix + ".timeout":
            oasis_chiller_driver.timeout = float(value)
            casput(self.prefix + ".timeout", oasis_chiller_driver.timeout)
        else:
            attr = PV_name.replace(self.prefix + ".", "")
            self.command_queue.append([attr, float(value)])


oasis_chiller_IOC = Oasis_Chiller_IOC()


def run():
    """Serve instrument on the network as EPICS IOC"""
    oasis_chiller_IOC.run()


if __name__ == "__main__":
    import logging

    # CAServer.DEBUG = True
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)
    self = oasis_chiller_IOC  # for debugging
    PV_name = "NIH:CHILLER.VAL"
    # print('oasis_chiller_driver.init_communications()')
    # print("oasis_chiller_driver.port_name")
    print("oasis_chiller_driver.nominal_temperature = 40")
    print("oasis_chiller_driver.nominal_temperature = 5")
    # print("oasis_chiller_driver.actual_temperature")
    # print("oasis_chiller_driver.low_limit")
    # print("oasis_chiller_driver.high_limit")
    print("oasis_chiller_driver.fault_code")
    print("oasis_chiller_driver.faults")
    # print('CAServer.DEBUG = %r' % CAServer.DEBUG)
    print('oasis_chiller_IOC.run()')
    print('oasis_chiller_IOC.start()')
    print("oasis_chiller.fault_code")
    print("oasis_chiller.faults")
    # print('oasis_chiller_IOC.startup()')
    # print('oasis_chiller_IOC.update_once()')
    # print('casmonitor(self.prefix+".VAL",callback=self.monitor)')
    # print('CAServer.start_server()')
    # print('CAServer.PVs[PV_name] = CAServer.PV_info()')
    # print('CAServer.PVs')
    # print("run_IOC()")
