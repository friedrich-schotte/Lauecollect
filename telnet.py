"""Execute commands remotely via telnet protocol.
Friedrich Schotte, May 1, 2015 - Oct 26, 2015
"""
__version__ = "1.0.1"
from logging import error,warn,debug

def telnet(ip_address,command):
    """Execute a shell command remotely"""
    from telnetlib import Telnet

    # For performance reasons, keep the connection open across repeated calls.
    # Also allow connections to multiple servers be open at the same time.
    if not ip_address in telnet_connections: telnet_connections[ip_address] = None
    connection = telnet_connections[ip_address]
        
    while True:
        if connection is None:
            try:
                connection = Telnet(ip_address)
                connection.read_until("login: ")
                connection.write("root\n")
                connection.read_until("Password: ")
                connection.write("root\n")
                connection.read_until("# ")
            except Exception,msg:
                error("Telnet %r: %s" % (ip_address,msg))
                connection = None
                reply = ""
                break
        try:
            connection.write(command+"\n")
            reply = connection.read_until("# ")
            break
        except Exception,msg:
            warn("telnet %r,%r: %s" % (ip_address,command,msg))
            connection = None
            continue
    telnet_connections[ip_address] = connection
    
    reply = reply.replace("\r\n","\n")
    reply = reply.replace(command+"\n","")
    reply = reply.rstrip("# ")
    reply = reply.rstrip("\n")
    return reply

telnet_connections = {}

if __name__ == "__main__":
    print 'telnet("id14timing3.cars.aps.anl.gov","date")'
