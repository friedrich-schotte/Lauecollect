from EPICS_serial_CA import Serial
port = Serial("14IDB:serial3") # loop back connector

string = "SET:TEMP 4.000\n"
port.query(string)
# generates reply 'SET:TEMP 4.000\nUT'

from CA import caput
encoded_string = repr(string)[1:-1]
##caput("14IDB:serial3.AOUT",encoded_string,wait=True)
caput('14IDB:serial3.AOUT','SET:TEMP 4.000\\n',wait=True)
