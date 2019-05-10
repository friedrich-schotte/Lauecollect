import linac
lcls_linac = linac.Linac()
import daq
import socket
daq_hostname = socket.gethostname()
xppdaq = daq.Daq(host=daq_hostname,platform=1,lcls=lcls_linac)

