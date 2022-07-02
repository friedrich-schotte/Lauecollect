"""
Date created: 2020-02-03
Date last modified: 2020-10-24
Revision comment: Cleanup
"""
__version__ = "1.1.1"

import logging
from logging import error
from traceback import format_exc

logging.basicConfig(format="%(levelname)s: %(message)s")
# logging.getLogger().level = logging.ERROR
logging.getLogger().level = logging.FATAL

try:
    import EPICS_CA.CA
except ImportError:
    error("%s" % format_exc())
try:
    import EPICS_CA.CAServer
except ImportError:
    error("%s" % format_exc())
try:
    import EPICS_CA.CAServer_single_threaded
except ImportError:
    error("%s" % format_exc())
try:
    import epics
except ImportError:
    error("%s" % format_exc())
try:
    import caproto.sync.client
    from caproto.server import PVGroup, pvproperty, run
    from caproto import ChannelType
except ImportError:
    error("%s" % format_exc())

servers = ["EPICS_CA", "EPICS_CA_st", "caproto"]
clients = ["EPICS_CA", "pyepics", "caproto"]

long_string = "".join(["|___%d0____" % (i + 1) for i in range(5)])[0:]
string_list = ['abc', long_string]


def prefix(server): return "TEST:%s." % server


var_name = "STRING_LIST"


def PV_name(server): return prefix(server) + var_name


def check(result, expected_result):
    check = "fail"
    result = bytes_list(result)
    expected_result = bytes_list(expected_result)
    if result == expected_result:
        check = "pass"
    elif truncate(result, 39) == truncate(expected_result, 39):
        check = "pass-"
    return check


def bytes_list(string_list):
    try:
        return [to_bytes(s) for s in string_list]
    except:
        return []


def to_string_list(bytes_list):
    try:
        return [to_str(s) for s in bytes_list]
    except:
        return []


def to_bytes(s): return s.encode('utf-8') if not type(s) == bytes else s


def to_str(b): return b.decode('latin-1') if hasattr(b, "decode") else b


def truncate(string_list, length): return [s[:length] for s in string_list]


from platform import python_version

print("Python %s" % python_version())
print("")

servers_running = []
for server in servers:
    try:
        if server == "EPICS_CA":
            EPICS_CA.CAServer.casput(PV_name(server), string_list)
        if server == "EPICS_CA_st":
            EPICS_CA.CAServer_single_threaded.casput(PV_name(server), string_list)
            EPICS_CA.CAServer_single_threaded.start()
        if server == "caproto":
            class IOC(caproto.server.PVGroup):
                STRING_LIST = caproto.server.pvproperty(
                    value=string_list,
                    dtype=caproto.ChannelType.STRING,
                )


            ioc = IOC(prefix=prefix(server))


            def run_server():
                import asyncio
                asyncio.set_event_loop(asyncio.new_event_loop())
                caproto.server.run(ioc.pvdb, module_name='caproto.asyncio.server')


            def start_server():
                from threading import Thread
                global ioc_task
                ioc_task = Thread(target=run_server, daemon=True)
                ioc_task.start()


            start_server()
        servers_running.append(server)
    except Exception:
        error("%s" % format_exc())

format = "%-12s > %-12s %-5s %s"
print(format % ("Server", "Client", "", ""))
for server in servers:
    if server in servers_running:
        for client in clients:
            result = None
            try:
                if client == "EPICS_CA":
                    result = EPICS_CA.CA.caget(PV_name(server))
                if client == "pyepics":
                    result = epics.caget(PV_name(server), timeout=1.0)
                if client == "caproto":
                    result = caproto.sync.client.read(PV_name(server)).data
            except Exception:
                error("%s" % format_exc())
            print(format % (server, client, check(result, string_list),
                            repr(to_string_list(result)).replace("\n", "")))

print("")
print(format % ("Client", "Server", "", ""))
new_string_list = string_list[::-1]
for server in servers:
    if server in servers_running:
        initial_value = ["", ""]
        for client in clients:
            try:
                if server == "EPICS_CA":
                    EPICS_CA.CAServer.casput(PV_name(server), initial_value)
                if server == "EPICS_CA_st":
                    EPICS_CA.CAServer_single_threaded.casput(PV_name(server), initial_value)
                if server == "caproto":
                    ioc.STRING_LIST.value = initial_value
            except Exception:
                error("%s" % format_exc())

            try:
                if client == "EPICS_CA":
                    EPICS_CA.CA.caput(PV_name(server), new_string_list)
                if client == "pyepics":
                    epics.caput(PV_name(server), truncate(new_string_list, 39), timeout=1.0)
                if client == "caproto":
                    caproto.sync.client.write(PV_name(server), new_string_list)
            except Exception:
                error("%s" % format_exc())

            from time import sleep

            sleep(1)
            result = None
            try:
                if server == "EPICS_CA":
                    result = EPICS_CA.CAServer.casget(PV_name(server))
                if server == "EPICS_CA_st":
                    result = EPICS_CA.CAServer_single_threaded.casget(PV_name(server))
                if server == "caproto":
                    result = ioc.STRING_LIST.value
            except Exception:
                error("%s" % format_exc())

            print(format % (client, server, check(result, new_string_list),
                            repr(to_string_list(result)).replace("\n", "")))

