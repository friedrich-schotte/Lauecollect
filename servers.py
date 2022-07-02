#!/usr/bin/env python
"""
Start servers automatically

Author: Friedrich Schotte
Date created: 2017-10-23
Date last modified: 2022-05-04
Revision comment: Fixed: Issue: local_machine_names default value
"""
__version__ = "2.5.1"

from logging import debug, warning, error, exception
from traceback import format_exc
from typing import Dict, Any

from cached_function import cached_function
from temporary_cached_function import temporary_cached_function


class Server(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "%r.%s" % (self.servers, self.mnemonic)

    @property
    def servers(self):
        return Servers(self.domain_name)

    @property
    def domain_name(self):
        domain_name = "BioCARS"
        if "." in self.name:
            domain_name = self.name.split(".", 1)[0]
        return domain_name

    @property
    def base_name(self):
        return self.name.split(".", 1)[-1]

    @property
    def db_name(self):
        return "servers/%s/servers/%s" % (self.domain_name, self.base_name)

    from db_property import db_property
    label = db_property("label", "")
    command = db_property("command", "")
    machine_name = db_property("machine_name", "INSTRUMENTATION")
    auto_start = db_property("auto_start", False)
    logfile_basename = db_property("logfile_basename", "new_server")
    enabled = db_property("enabled", True)
    value_code = db_property("value_code", "True")
    format_code = db_property("format_code", "str(value)")
    test_code = db_property("test_code", "value")
    log_level = db_property("log_level", "DEBUG")

    @property
    def logfile_name(self):
        return "%s.%s" % (self.domain_name, self.logfile_basename)

    @property
    def default_mnemonic(self):
        name = self.logfile_basename
        name = name.replace("-", "_")
        name = name.replace("_server", "")
        return name

    mnemonic = db_property("mnemonic", default_mnemonic)

    properties = {
        "label",
        "mnemonic",
        "command",
        "machine_name",
        "auto_start",
        "logfile_basename",
        "value_code",
        "format_code",
        "test_code",
        "log_level",
    }

    def get_machine_names(self):
        return Servers(self.domain_name).machine_names

    def set_machine_names(self, value):
        Servers(self.domain_name).machine_names = value

    machine_names = property(get_machine_names, set_machine_names)

    def get_running(self):
        if self.is_local:
            running = self.running_locally
        else:
            running = self.running_remotely
        return running

    def set_running(self, value):
        if self.is_local:
            self.running_locally = value
        else:
            self.running_remotely = value

    running = property(get_running, set_running)

    @property
    def runnable(self):
        if self.is_local:
            runnable = True
        else:
            runnable = self.runnable_remotely
        return runnable

    def get_running_locally(self):
        return process_running(self.running_command_line)

    def set_running_locally(self, value):
        if value != self.running:
            if value:
                self.running_command_line = self.command_line
                start_process(self.running_command_line)
            else:
                terminate_process(self.running_command_line)

    running_locally = property(get_running_locally, set_running_locally)

    def run(self):
        self.running_command_line = self.command_line
        run_process(self.running_command_line)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def get_running_remotely(self):
        from CA import caget
        running = (caget(self.running_PV_name) == 1)
        return running

    def set_running_remotely(self, value):
        from CA import caput
        caput(self.running_PV_name, value)

    running_remotely = property(get_running_remotely, set_running_remotely)

    @property
    def runnable_remotely(self):
        from CA import caget
        return caget(self.running_PV_name) is not None

    @property
    def is_local(self):
        machine_name = self.machine_name.upper()
        local_machine_names = [name.upper() for name in self.local_machine_names]
        is_local = machine_name in local_machine_names
        return is_local

    @property
    def local_machine_names(self):
        return Servers(self.domain_name).local_machine_names

    @property
    def running_PV_name(self):
        return self.PV_name("running")

    def PV_name(self, name):
        """name: property name, e.g. 'running','log' """
        from startup_server import Startup_Server
        prefix = Startup_Server(self.domain_name).prefix
        name = "%s%s.%s.%s" % (prefix, self.machine_name, self.name, name)
        name = name.upper()
        return name

    def get_command_line(self):
        from sys import executable as python
        command = "from redirect import *; redirect(%r,level=%r); %s" % \
                  (self.logfile_name, self.log_level, self.command)
        command_line = [python, "-c", command]
        return command_line

    command_line = property(get_command_line)

    @property
    def python_executable(self):
        """Python interpreter"""
        from sys import executable
        return executable

    running_command_line = db_property("running_command_line", command_line, local=True)

    def get_log(self):
        return self.log_local if self.is_local else self.log_remote

    def set_log(self, value):
        if self.is_local:
            self.log_local = value
        else:
            self.running_remotely = value

    log = property(get_log, set_log)

    def get_log_remote(self):
        from CA import caget
        value = caget(self.PV_name("log"))
        if value is None:
            value = ""
        return value

    def set_log_remote(self, value):
        from CA import caput
        caput(self.PV_name("log"), value)

    log_remote = property(get_log_remote, set_log_remote)

    def get_log_local(self):
        value = ""
        from os.path import exists
        filename = self.log_filename
        if exists(filename):
            try:
                from os.path import getsize
                file_size = getsize(self.log_filename)
                start_index = max(file_size - 65000, 0)
                length = file_size - start_index
                with open(self.log_filename) as file:
                    file.seek(start_index)
                    value = file.read(length)
            except Exception as x:
                warning("%s: %s" % (filename, x))
        return value

    def set_log_local(self, value):
        open(self.log_filename, "wb").write(value)

    log_local = property(get_log_local, set_log_local)

    @property
    def log_filename(self):
        from redirect import log_filename
        return log_filename(self.logfile_name)

    @property
    def test_code_OK(self):
        """Is the code for this test executable?"""
        value = self.value  # -> locals()
        try:
            eval(self.test_code, instrumentation(), locals())
            OK = True
        except Exception as msg:
            warning("value: %s: %s\n%s" % (self.test_code, msg, format_exc()))
            OK = False
        return OK

    @property
    def value(self):
        """Current value of diagnostic"""
        try:
            value = eval(self.value_code, instrumentation())
        except Exception as msg:
            warning("value: %s: %s\n%s" % (self.value_code, msg, format_exc()))
            value = ""
        return value

    @property
    def formatted_value(self):
        """Current value of diagnostic as string"""
        value = self.value  # -> locals()
        try:
            text = eval(self.format_code, instrumentation(), locals())
        except Exception as msg:
            warning("value: %s with value=%r: %s\n%s" % (self.format_code, value, msg,
                                                         format_exc()))
            text = str(value)
        return text

    @property
    def OK(self):
        """Did this test pass OK?"""
        value = self.value  # -> locals()
        # noinspection PyBroadException
        try:
            passed = eval(self.test_code, instrumentation(), locals())
        except Exception:
            passed = True
        return passed

    def get_dict(self):
        return dict([(key, getattr(self, key)) for key in self.properties])

    def set_dict(self, values):
        # noinspection PyBroadException
        try:
            items = values.items()
        except Exception:
            error("%r: items(): %s" % (values, format_exc()))
        else:
            for key, value in items:
                # noinspection PyBroadException
                try:
                    debug("%r.%s = %r" % (self, key, value))
                    setattr(self, key, value)
                except Exception:
                    error("%r.%s = %r: %s" % (self, key, value, format_exc()))

    dict = property(get_dict, set_dict)


class Servers(object):
    """Collection of Server objects"""
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    @property
    def db_name(self):
        return "servers/%s" % self.domain_name

    from db_property import db_property

    N = db_property("N", 0)
    machine_names = db_property("machine_names", [])

    @property
    def default_local_machine_name(self): return hostname().upper()

    old_local_machine_name = db_property("machine_name", default_local_machine_name, local=True)

    @property
    def default_local_machine_names(self): return [self.old_local_machine_name]

    local_machine_names = db_property("local_machine_names", default_local_machine_names, local=True)

    servers = {}

    def __getitem__(self, i):
        if i not in self.servers:
            self.servers[i] = Server("%s.%s" % (self.domain_name, i + 1))
        return self.servers[i]

    def __len__(self):
        return self.N

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def __getattr__(self, property_name):
        if property_name == "__members__":
            return self.names
        if property_name.startswith("__") and property_name.endswith("__"):
            raise AttributeError("%r has no attribute %r" % (self, property_name))
        return self.server(mnemonic=property_name)

    def server(self, mnemonic):
        for server in self:
            if server.mnemonic == mnemonic:
                return server
        raise AttributeError("%r has no attribute %r" % (self, mnemonic))

    @property
    def mnemonics(self):
        return [server.mnemonic for server in self]

    names = mnemonics

    def get_running(self):
        return all([server.running for server in self if server.enabled])

    def set_running(self, value):
        for server in self:
            if server.enabled:
                if value != server.running:
                    server.running = value

    running = property(get_running, set_running)

    def set_N_running(self, count):
        N_running = self.N_running
        for server in self:
            if N_running > count and server.running:
                server.running = False
                N_running -= 1
            if N_running < count and not server.running:
                server.running = True
                N_running += 1

    def get_N_running(self):
        return sum([server.running for server in self if server.enabled])

    N_running = property(get_N_running, set_N_running)

    def auto_start_local_servers(self):
        """Make sure all local servers are running that have auto_start == True """
        for server in self:
            if server.auto_start and server.machine_name in self.local_machine_names:
                server.running = True

    def start_server(self, name):
        self.server(name).start()

    start = start_server

    def run_server(self, name):
        self.server(name).run()

    run = run_server

    def save(self, filename):
        from os.path import dirname, exists
        from os import makedirs
        directory = dirname(filename)
        if directory and not exists(directory):
            makedirs(directory)
        open(filename, "w").write(self.str)

    def load(self, filename):
        try:
            value = open(filename).read()
        except OSError:
            error("%s: %s" % (filename, format_exc()))
        else:
            self.str = value

    @property
    def default_filename(self):
        from module_dir import module_dir
        filename = "%s/settings/servers/%s/servers.txt" % (module_dir(self), self.domain_name)
        return filename

    def get_str(self):
        from pprint import pformat
        return pformat(self.list)

    def set_str(self, value):
        # noinspection PyBroadException
        try:
            self.list = eval(value)
        except Exception:
            error("%.80r: %s" % (value, format_exc()))

    str = property(get_str, set_str)

    def get_list(self):
        return [server.dict for server in self]

    def set_list(self, values):
        try:
            N = len(values)
        except TypeError:
            error("len(%.80r): %s" % (values, format_exc()))
        else:
            self.N = N
            for i in range(0, N):
                self[i].dict = values[i]

    list = property(get_list, set_list)


class Local_Startup_Server(object):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    @property
    def servers(self):
        return Servers(self.domain_name)

    @property
    def local_machine_names(self):
        return self.servers.local_machine_names

    @local_machine_names.setter
    def local_machine_names(self, value):
        self.servers.local_machine_names = value

    @property
    def command_line(self):
        from sys import executable as python
        command = "from redirect import *; redirect(%r); %s" % \
                  (self.logfile_name, self.command)
        command_line = [python, "-c", command]
        return command_line

    db_name = "local_startup_server"
    from db_property import db_property
    running_command_line = db_property("running_command_line", command_line, local=True)

    @property
    def command(self):
        return "from startup_server import *; run(%r)" % self.domain_name

    @property
    def logfile_basename(self):
        suffix = ",".join(self.local_machine_names)
        return f"startup_server_{suffix}"

    @property
    def logfile_name(self):
        return "%s.%s" % (self.domain_name, self.logfile_basename)

    def get_running(self):
        return process_running(self.running_command_line)

    def set_running(self, value):
        if value != self.running:
            if value:
                self.running_command_line = self.command_line
                start_process(self.running_command_line)
            else:
                terminate_process(self.running_command_line)

    running = property(get_running, set_running)

    @property
    def operational(self):
        from CA import caget
        PV_names = self.running_PV_names
        operational = [caget(PV_name) is not None for PV_name in PV_names]
        all_operational = len(operational) > 0 and all(operational)
        return all_operational

    @operational.setter
    def operational(self, value):
        from CA import caput
        for PV_name in self.running_PV_names:
            caput(PV_name, value)

    @property
    def running_PV_names(self):
        from startup_server import Startup_Server
        return Startup_Server(self.domain_name).status_PV_names


class Startup_Servers(object):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    @property
    def servers(self):
        return Servers(self.domain_name)

    def __len__(self):
        return len(self.servers.machine_names)

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def __getitem__(self, i):
        return Startup_Server(self.domain_name, i)


class Startup_Server(object):
    def __init__(self, domain_name, i):
        self.domain_name = domain_name
        self.i = i

    def __repr__(self):
        return "Startup_Servers(%r)[%r]" % (self.domain_name, self.i)

    @property
    def machine_name(self): return self.servers.machine_names[self.i]

    @property
    def servers(self): return Servers(self.domain_name)

    @property
    def operational(self):
        from CA import caget
        PV_value = caget(self.running_PV_name)
        value = PV_value is not None
        return value

    @operational.setter
    def operational(self, value):
        from CA import caput
        caput(self.running_PV_name, value)

    running = operational

    @property
    def running_PV_name(self):
        from startup_server import Startup_Server
        startup_server = Startup_Server(self.domain_name)
        PV_name = "%s%s.RUNNING" % (startup_server.prefix, self.machine_name)
        PV_name = PV_name.upper()
        return PV_name


@cached_function()
def instrumentation() -> Dict[str, Any]:
    exec("from numpy import nan, isnan")  # -> locals()
    exec("from instrumentation import *")  # -> locals()
    return locals()


def process_running(command_line):
    """Is there at least one process running matching command_line somewhere in
    the pathname or command line arguments?
    command_line: list of strings
    """
    running = False
    for a_command_line in processes_running():
        if command_lines_match(command_line, a_command_line):
            running = True
            break
    return running


def command_lines_match(command_line1, command_line2):
    """
    command_line1: list of strings
    command_line2: list of strings
    """
    # Example:
    # ['/usr/bin/python2.7', '-c', "from redirect import *; redirect('startup_server_ID14B4'); from startup_server
    # import *; startup_server.run()"]
    # ['/usr/bin/python', '-c', "from redirect import *; redirect('startup_server_ID14B4'); from startup_server
    # import *; startup_server.run()"]
    match = command_line1[1:] == command_line2[1:]
    return match


@temporary_cached_function(timeout=1.0)
def processes_running():
    from psutil import process_iter
    process_list = []
    N_attempts = 3
    for attempt in range(0, N_attempts):
        # noinspection PyBroadException
        try:
            process_list = list(process_iter())
            break
        except Exception:
            if attempt == N_attempts-1:
                exception("process_iter")
    processes = []
    for process in process_list:
        # noinspection PyBroadException
        try:
            command_line = process.cmdline()
        except Exception:
            command_line = []
        processes.append(command_line)
    return processes


def run_process(command_line):
    """Execute the command in a subprocess waiting for it to finish."""
    from subprocess import call
    call(command_line)


def start_process(command_line):
    """Execute the command in a subprocess without waiting."""
    from subprocess import Popen
    Popen(command_line, stdin=None, stdout=None, stderr=None,
          close_fds=True)


def terminate_process(command_line):
    """Terminate all running processes, matching command_line somewhere in
    the pathname or command line arguments
    command_line: list of strings
    """
    import psutil
    for proc in psutil.process_iter():
        # noinspection PyBroadException
        try:
            a_command_line = proc.cmdline()
        except Exception:
            a_command_line = []
        if command_lines_match(command_line, a_command_line):
            proc.kill()


def hostname():
    from platform import node
    name = node()
    name = name.split(".")[0]
    return name


def server_status(servers):
    s = ""
    s += 'servers.local_machine_names = %r\n' % servers.local_machine_names
    # s += 'servers.N = %r\n' % servers.N
    for name in servers.names:
        server = getattr(servers, name)
        # s += 'servers.%s.machine_name = %r\n' % (name,server.machine_name)
        # s += 'servers.%s.test_code_OK = %r\n' % (name,server.test_code_OK)
        # s += 'servers.%s.OK = %r\n' % (name,server.OK)
        # s += 'servers.%s.command = %r\n' % (name,server.command)
        # s += 'servers.%s.command_line = %r\n' % (name,server.command_line)
        # s += 'servers.%s.running = %r\n' % (name,server.running)
        s += 'servers.%s.running_locally = %r\n' % (name, server.running_locally)
    return s


def startup_server_status(domain_name=None):
    local_startup_server = Local_Startup_Server(domain_name)
    startup_servers = Startup_Servers(domain_name)
    s = ""
    s += '%r.local_machine_names = %r\n' % (local_startup_server, local_startup_server.local_machine_names)
    s += '%r.running = %r\n' % (local_startup_server, local_startup_server.running)
    for startup_server in startup_servers:
        s += '%r.machine_name = %r\n' % (startup_server, startup_server.machine_name)
        s += '%r.running = %r\n' % (startup_server, startup_server.running)
    return s


if __name__ == "__main__":
    """"for testing"""
    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    # domain_name = "WetLab"
    # domain_name = "TestBench"

    # Usage
    from sys import argv

    if len(argv) > 1 and "start" in argv[1]:
        if len(argv) > 2:
            domain_name = argv[2]
        servers = Servers(domain_name)
        servers.auto_start_local_servers()
    else:
        # from pdb import pm
        import logging

        msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=msg_format)

        servers = Servers(domain_name)
        print("servers.domain_name = %r" % servers.domain_name)
        print("print(server_status(servers))")
        print("print(startup_server_status(%r))" % domain_name)
        print("")
        print("servers.save(%r)" % servers.default_filename)
        print("servers.load(%r)" % servers.default_filename)
