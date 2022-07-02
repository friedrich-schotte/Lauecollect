#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2020-05-21
Date last modified: 2021-09-13
Revision comment: Cleanup: start, stop
"""
__version__ = "1.4.12"

import logging
from timing_system_simulator import timing_system_simulator


logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error


class Timing_System_Simulator_IOC(object):

    def __init__(self, timing_system):
        self.timing_system = timing_system
        self.timing_system.monitor(self.process_report)
        self.timing_system.file_system.monitor_file(
            self.timing_system.sequencer.sequencer_fs_path, self.update_sequencer_fs)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.timing_system)

    from alias_property import alias_property
    name = alias_property("timing_system.name")

    def run(self):
        self.init()
        self.cas.run()

    def start(self):
        self.init()
        self.cas.start()

    def stop(self):
        self.cas.stop()

    def init(self):
        self.publish_register_list()
        self.publish_registers()
        self.publish_parameters()
        self.publish_sequencer()

    def publish_register_list(self):
        register_list = ";".join(self.timing_system.registers.names)
        self.casput(self.prefix + "registers", register_list)

    def publish_registers(self):
        for register in self.timing_system.registers:
            prefix = self.prefix + "registers." + register.name + "."

            self.casput(prefix + "count", register.count)
            self.casput(prefix + "description", register.description)
            self.casput(prefix + "address", register.address)
            self.casput(prefix + "bit_offset", register.bit_offset)
            self.casput(prefix + "bits", register.bits)

            self.casmonitor(prefix + "count", callback=self.handle_update, new_thread=False)

    def publish_parameters(self):
        self.casmonitor_record(self.prefix + "parameters.",
                               self.handle_parameters_get, self.handle_parameters_put)

    def handle_parameters_get(self, PV_name):
        # debug("Got request for %r" % PV_name)
        if PV_name.startswith(self.prefix + "parameters."):
            name = PV_name[len(self.prefix + "parameters."):]
            value = self.timing_system.get_parameter(name)
            # debug("%s = %r" % (PV_name,value))
            return value

    def handle_parameters_put(self, PV_name, value):
        debug("Got request %s = %r" % (PV_name, value))
        if PV_name.startswith(self.prefix + "parameters."):
            name = PV_name[len(self.prefix + "parameters."):]
            debug("setting parameters.%s = %r" % (name, value))
            self.timing_system.set_parameter(name, value)
            value = self.timing_system.get_parameter(name)
            debug("read-back parameters.%s = %r" % (name, value))
            self.casput(PV_name, value)

    def publish_sequencer(self):
        self.casmonitor_record(self.prefix + "sequencer.",
                               self.handle_sequencer_get, self.handle_sequencer_put)

    def handle_sequencer_get(self, PV_name):
        debug("Got request for %r" % PV_name)
        if PV_name.startswith(self.prefix + "sequencer."):
            name = PV_name[len(self.prefix + "sequencer."):]
            value = self.timing_system.get_sequencer_value(name)
            debug("%s = %r" % (PV_name, value))
            return value

    def handle_sequencer_put(self, PV_name, value):
        debug("Got request %s = %r" % (PV_name, value))
        if PV_name.startswith(self.prefix + "sequencer."):
            name = PV_name[len(self.prefix + "sequencer."):]
            debug("setting sequencer.%s = %r" % (name, value))
            self.timing_system.set_sequencer_value(name, value)
            value = self.timing_system.get_sequencer_value(name)
            debug("read-back sequencer.%s = %r" % (name, value))
            self.casput(PV_name, value)
        if PV_name.startswith(self.prefix + "sequencer.fs."):
            self.update_sequencer_fs()

    def update_sequencer_fs(self):
        value = self.timing_system.get_sequencer_value("fs")
        self.casput(self.prefix + "sequencer.fs", value)

    def handle_update(self, PV_name, value, _char_value):
        debug("Got request %s = %r" % (PV_name, value))
        if PV_name.startswith(self.prefix + "registers."):
            name_attr = PV_name[len(self.prefix + "registers."):]
            if "." in name_attr:
                name, attr = name_attr.split(".", 1)
                register = self.timing_system.registers.register(name)
                if hasattr(register, attr):
                    debug("setting registers.%s.%s = %r" % (name, attr, value))
                    setattr(register, attr, value)
                    value = getattr(register, attr)
                    debug("read-back registers.%s.%s = %r" % (name, attr, value))
                    self.casput(PV_name, value)

    def process_report(self, report):
        if not report.endswith(".count=0"):
            debug("%.60s" % report)
        if " " in report:
            timestamp, command = report.split(" ", 1)
            try:
                timestamp = float(timestamp)
            except ValueError:
                error("%s: %r: expecting float" % (command, timestamp))
            if "=" in command:
                name, value = command.split("=", 1)
                PV_name = self.prefix + name
                if name.endswith(".count"):
                    try:
                        value = int(value)
                    except ValueError:
                        error("%s: %r: expecting integer" % (command, value))
                if value:
                    debug("%s=%.60r" % (PV_name, value))
                self.casput(PV_name, value, timestamp=timestamp)

    def get_prefix(self):
        prefix = self.timing_system.get_parameter("prefix")
        # Strip quotes if quoted: "'NIH:TIMING.'" > "NIH:TIMING."
        try:
            prefix = eval(prefix)
        except Exception:
            pass
        if prefix == "":
            prefix = self.default_prefix
        return prefix

    def set_prefix(self, value):
        self.timing_system.set_parameter("prefix", repr(value))

    prefix = property(get_prefix, set_prefix)

    @property
    def default_prefix(self):
        prefix = self.name.upper() + ":TIMING."
        prefix = prefix.replace("BIOCARS", "NIH")
        return prefix

    import EPICS_CA.CAServer_single_threaded as cas

    def casput(self, PV_name, value, timestamp=None, update=False):
        self.cas.casput(PV_name, value, timestamp=timestamp, update=update)

    def casmonitor(self, PV_name, callback, new_thread=False):
        self.cas.casmonitor(PV_name, callback=callback, new_thread=new_thread)

    def casmonitor_record(self, name, get_handler, put_handler):
        self.cas.casmonitor_record(name, get_handler, put_handler)


def run(name=None):
    start(name)
    wait()
    stop()


def start(name, reset=True):
    if reset:
        timing_system_simulator(name).reset()
    timing_system_simulator(name).IOC.start()
    timing_system_simulator(name).file_server.start()


def wait():
    from time import sleep
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass


def stop():
    timing_system_simulator(name).IOC.stop()
    timing_system_simulator(name).file_server.stop()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    # logging.getLogger("EPICS_CA").level = logging.DEBUG

    name = "BioCARS"
    # name = "LaserLab"
    reset = True

    self = timing_system_simulator(name).IOC
    print(f"self = {self}")
    print("")
    print(f'start({name!r}, reset={reset})')
    print(f'stop({name!r})')

    # print('')
    # print('caget(f"{self.prefix}registers")')
    # print('caget(f"{self.prefix}registers.ver.count")')
    # print('caput(f"{self.prefix}registers.ver.count",655)')
    # print('caget(f"{self.prefix}parameters")')
    # print('caget(f"{self.prefix}parameters.ch1.PP_enabled")')
    # print('caput(f"{self.prefix}parameters.ch1.PP_enabled","True")')
    # print('caget(f"{self.prefix}sequencer.descriptor")')
    # print('caput(f"{self.prefix}sequencer.descriptor","")')
