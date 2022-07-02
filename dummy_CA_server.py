#!/usr/bin/env python
"""
CA Strip Chart Test Server
by Valentyn Stadnytskyi
25 May 2018 - July 1 2018
"""

__version__ = "1.0.0"
from logging import info,debug,warn, error
from time import time, sleep
from CAServer import casput, casget

class CA_Test_Server(object):
    def init(self,PV = 'NIH:TEST_SERVER.VAL'):
        self.flag = True
        self.PV = PV
    def run(self):
        from thread import start_new_thread
        start_new_thread(self.run_once, ())

    def run_once(self):
        from numpy import random, sin
        while self.flag:
            value = random.randint(1024)*0.5/1024.+ sin(time()/5)
            casput(self.PV, value)
            sleep(1)
            
    
# Run the main program
if __name__ == "__main__":
    server = []
    server.append(CA_Test_Server())
    
    server.append(CA_Test_Server())
    
    for idx in server:
        idx.init()
        server[1].PV = 'NIH:TEST_SERVER.VAL2'
        idx.run()

    
    import logging
    from tempfile import gettempdir
   
    logging.basicConfig(filename=gettempdir()+'/CA_strip_chart_test_server.log',
                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
    #Create an instance with a ring buffer

