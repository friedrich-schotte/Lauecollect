"""Test communication timing
Friedrich Schotte Nov 2, 2015 - Nov 3, 2015"""
from temperature_controller_driver import temperature_controller as T
from time import time,sleep

def double_command():
    """"""
    T.port.write('MEAS:T?\n')
    T.port.write('MEAS:T?\n')

def double_command_OK(delay):
    """delay: delay between two commands in seconds"""
    T.port.write('MEAS:T?\n')
    sleep(delay)
    T.port.write('MEAS:T?\n')
    T.port.timeout=0.1
    reply=T.port.read(100)
    passed = reply.count("\n") == 2
    return passed

def delay_OK(delay):
    """delay: delay between two commands in seconds"""
    T.port.write('MEAS:T?\n')
    reply = T.port.readline()
    sleep(delay)
    passed = "\n" in reply and "Ready" not in reply
    return passed

def test(procedure,delay):
    """delay: delay between two commands in seconds"""
    from sys import stderr
    OK = 0; attempts = 0
    try:
        while True:
            attempts += 1
            OK += procedure(delay)
            if attempts % 20 == 0: stderr.write("%d/%d OK\n" % (OK,attempts))
    except KeyboardInterrupt: return

print('test(double_command_OK,0.1)')
print('test(delay_OK,0)')
print('double_command();test(delay_OK,0)')
