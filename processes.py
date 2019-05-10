"""
List active processes
Author: Friedrich Schotte
Date created: Nov 10, 2017
"""
__version__ = "1.0"
from logging import debug,info,warn,error

def PIDs():
    """Process IDs of all running processes, as list of integers"""
    from ctypes import windll,c_ulong,byref,sizeof
    PIDs = (c_ulong*512)()
    size_of_PIDs = c_ulong()
    windll.psapi.EnumProcesses(byref(PIDs),sizeof(PIDs),byref(size_of_PIDs))
    nPIDs = size_of_PIDs.value/sizeof(c_ulong())
    pidProcess = sorted([int(i) for i in PIDs][:nPIDs])
    return pidProcess

def processes():
    from process_information import ProcessInformation
    processes = {}
    for PID in PIDs():
        command_line = ""
        try: command_line = ProcessInformation(PID).command_line
        except Exception,msg: warn("PID %s: %s" % (PID,msg))
        processes[PID] = command_line
    return processes


if __name__ == '__main__':
    from pdb import pm
    from time import time
    print('t=time(); x=PIDs(); time()-t')
    print('t=time(); x=processes(); time()-t')
    print(r'print "\n".join(processes().values())')

