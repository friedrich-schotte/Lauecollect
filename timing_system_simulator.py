#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2020-05-21
Date last modified: 2021-09-20
Revision comment: Fixed: Stop(name)
"""
__version__ = "1.10.9"

from cached_function import cached_function


@cached_function()
def timing_system_simulator(name):
    return Timing_System_Simulator(name)


class Timing_System_Simulator(object):
    from cached import cached

    def __init__(self, name):
        self.name = name
        self.monitors = []

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.name)

    def reset(self):
        self.sequencer.reset()
        self.file_system.reset()

    @cached
    @property
    def sequencer(self):
        from timing_system_simulator_sequencer import Timing_System_Simulator_Sequencer
        return Timing_System_Simulator_Sequencer(self)

    @cached
    @property
    def IOC(self):
        from timing_system_simulator_IOC import Timing_System_Simulator_IOC
        return Timing_System_Simulator_IOC(self)

    @cached
    @property
    def file_server(self):
        from timing_system_simulator_file_server import File_Server
        return File_Server(self.overlay_file_system)

    @cached
    @property
    def file_system(self):
        from timing_system_simulator_file_system import Timing_System_Simulator_File_System
        return Timing_System_Simulator_File_System(self)

    @cached
    @property
    def overlay_file_system(self):
        from timing_system_simulator_overlay_file_system import Timing_System_Simulator_Overlay_File_System
        return Timing_System_Simulator_Overlay_File_System(self)

    @property
    def registers(self):
        from timing_system_simulator_registers import timing_system_simulator_registers
        return timing_system_simulator_registers(self.name)

    def load_parameters(self, filename):
        self.parameters = open(filename).read()

    def save_parameters(self, filename):
        open(filename, "w").write(self.parameters)

    def get_parameters(self):
        text = ""
        for name in self.parameter_names:
            text += "%s=%s\n" % (name, self.get_parameter(name))
        return text

    def set_parameters(self, text):
        for line in text.splitlines():
            if "=" in line:
                name, value = line.split("=", 1)
                self.set_parameter(name, value)

    parameters = property(get_parameters, set_parameters)

    def get_parameter(self, name):
        from DB import dbget
        return dbget(self.parameter_db_name(name))

    def set_parameter(self, name, value):
        from DB import dbput
        return dbput(self.parameter_db_name(name), value)

    @property
    def parameter_names(self):
        from DB import dbdir
        keys = []
        for key in dbdir(self.parameter_db_basename):
            subkeys = dbdir(self.parameter_db_basename + "." + key)
            if not subkeys:
                keys.append(key)
            for subkey in subkeys:
                keys.append(key + "." + subkey)
        return keys

    def parameter_db_name(self, name):
        return self.parameter_db_basename + "." + name

    @property
    def parameter_db_basename(self):
        return self.db_basename + "/parameters"

    def get_sequencer_value(self, name):
        value = self.get_file(self.get_sequencer_filename(name))
        value = value.decode("utf-8")
        value = value.strip("\n")
        return value

    def set_sequencer_value(self, name, value):
        value = value.encode("utf-8")
        self.put_file(self.get_sequencer_filename(name), value)

    def get_sequencer_filename(self, name):
        if name.startswith("fs."):
            filename = name.replace("fs.", self.sequencer.sequencer_fs_path + "/", 1)
        elif name == "fs":
            filename = self.sequencer.sequencer_fs_path
        else:
            filename = "/proc/sys/dev/sequencer/" + name
        return filename

    def get_file(self, filename):
        return self.overlay_file_system.get_file(filename)

    def put_file(self, filename, content):
        self.overlay_file_system.put_file(filename, content)

    def handle_report(self, report):
        # debug("%.60s" % report)
        for handler in self.monitors:
            handler(report)

    def monitor(self, handler):
        if handler not in self.monitors:
            self.monitors += [handler]

    def monitor_clear(self, handler):
        while handler in self.monitors:
            self.monitors.remove(handler)

    @property
    def db_basename(self):
        return "timing_system_simulator/%s" % self.name

    @property
    def directory(self):
        return self.toplevel_directory + "/" + self.name

    @property
    def toplevel_directory(self):
        from module_dir import module_dir
        return module_dir(self.__class__) + "/timing_system_simulator"


def run(name, reset=True):
    start(name, reset)
    wait()
    stop(name)


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


def stop(name):
    timing_system_simulator(name).IOC.stop()
    timing_system_simulator(name).file_server.stop()


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    # logging.getLogger("timing_system_simulator_IOC").level = logging.DEBUG
    # logging.getLogger("timing_system_simulator_file_server").level = logging.DEBUG
    # logging.getLogger("timing_system_simulator_sequencer").level = logging.DEBUG

    name = "BioCARS"
    # name = "LaserLab"
    reset = True

    self = timing_system_simulator(name)
    print(f"self = {self}")
    print("")
    filename = self.directory + "/register-values.txt"
    print(f"self.registers.load_values({filename!r})")
    print(f"self.registers.save_values({filename!r})")
    filename = self.directory + "/parameters.txt"
    print(f"self.load_parameters({filename!r})")
    print(f"self.save_parameters({filename!r})")
    print('')
    # print('self.get_sequencer_filename("fs.queue1_repeat_count")')
    # print('self.get_sequencer_value("fs.queue1_repeat_count")')
    # print('')
    print(f'start({name!r}, reset={reset})')
    print(f'stop({name!r})')
