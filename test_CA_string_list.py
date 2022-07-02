from pdb import pm
from logging import debug,info,warn,error
import logging
logging.getLogger("caproto").level = logging.WARNING
logging.getLogger().level = logging.DEBUG

##server = "EPICS_CA"
server = "caproto"

long_string = "".join(["|___%d0____" % (i+1) for i in range(5)])
stringlist = ['abc',long_string]
prefix = "TEST:TEST."
varname = "STRINGLIST"
PV_name = prefix+varname

if server == "EPICS_CA":
    import EPICS_CA.CAServer_stringlist as CAServer
    CAServer.casput(PV_name,stringlist)

if server == "caproto":
    from caproto.server import PVGroup, pvproperty, run
    from caproto import ChannelType

    class IOC(PVGroup):
        STRINGLIST = pvproperty(
            value=stringlist,
            dtype=ChannelType.STRING,
        )

    ioc = IOC(prefix=prefix) 

    def run_server():
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        run(ioc.pvdb,module_name='caproto.asyncio.server')

    def start_server():
        from threading import Thread
        global server
        server = Thread(target=run_server,daemon=True)
        server.start()

    start_server()

import EPICS_CA.CA_stringlist as CA
##CA.DEBUG = True
result = CA.caget(PV_name,timeout=5.0)
print("%r" % result)
PV = CA.PVs['TEST:TEST.STRINGLIST']
data_type,data_count,payload = PV.data_type,PV.data_count,PV.data
value = CA.value(data_type,data_count,payload)
##print(PV.data[12:])
new_stringlist = stringlist[::-1]
CA.caput(PV_name,new_stringlist)
from time import sleep
sleep(2)
result = CA.caget(PV_name)
print("%r" % result)
