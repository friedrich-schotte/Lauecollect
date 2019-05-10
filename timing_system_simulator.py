#!/usr/bin/env python
"""
Timing System Simulator

Author: Friedrich Schotte
Date created: Oct 18, 2016
Date last modified: Oct 19, 2017
"""
__version__ = "1.0"

from tcp_server import tcp_server

class Timing_System_Simulator(tcp_server):
    """Timing System  Simulator"""
    name = "timing_system_simulator"

    def reply(self,query):
        """Return a reply to a client process
        command: string (without newline termination)
        return value: string (without newline termination)"""
        if query == "?": reply = "supported commands: ?, registers, parameters"
        elif query == "registers": reply = "xosct,losct"
        else: reply = "command %r not implemented" % query
        return reply

timing_system_simulator = Timing_System_Simulator()
    

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = timing_system_simulator # for debugging
    from tcp_client import query
    print('self.port = %r' % self.port)
    print('self.server_running = True')
    print('query("localhost:%s","registers")' % self.port)
