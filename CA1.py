"""EPICS Channel Access Protocol
Friedrich Schotte, 26 Apr 2009 - 8 Oct 2010

based on: 'Channel Access Protocol Specification', version 4.11
http://epics.cosylab.com/cosyjava/JCA-Common/Documentation/CAproto.html
"""

__version__ = "1.12"

import socket

timeout = 1.0 # s
DEBUG = False

class PV_info:
    "State information for each process variable"
    def __init__(self):
        self.connection_requested = 0 # first time a PV was asked for
        self.connection_initiated = 0 # time a CA connection for PV was initiated
        self.servers_queried = [] # for address resolution
        self.addr = None # IP address and port number of IOC
        self.channel_ID = None # client-provided reference number for PV
        self.channel_SID = None # server-provided reference number for PV
        self.data_type = None # DOUBLE,INT,STRING,...
        self.data_count = None # 1 if a scalar, >1 if an array
        self.access_bits = None # premissions bit map (bit 0: read, 1: write)
        self.IOID = 0 # last used read/write transaction reference number
        self.subscription_ID = None # locally assiged reference number for server updates
        self.response_time = 0 # timestamp of last reply from server
        self.data = None # value in CA representation (big-edian binary data)
        self.last_updated = 0 # timestamp of data, time update event received
        self.update_events = [] # for synchronization with client threads
        self.write_data = None # if put in progres, new value in CA representation
        self.write_requested = 0 # time WRITE_NOTIFY command sent
        self.write_confirmed = 0 # time WRITE_NOTIFY reply received
        self.write_event = None # for synchronization with client threads
    
PVs = {} # Unique list of active process variables

class connection_info:
    "Per CA server (IOC) state information"
    socket = None
    access_bits = None
    
connections = {} # list of known CA servers (IOCs)

# Used for IOC disocvery broadcasts
UDP_socket = None

# Protocol version 4.11:
major_version = 4
minor_version = 11
# CA server port = 5056 + major version * 2
# CA repeater port = 5056 + major version * 2 + 1
CA_port_number = 5056 + major_version * 2

# CA Message command codes:
VERSION = 0
EVENT_ADD = 1
WRITE = 4
SEARCH = 6
NOT_FOUND = 14
READ_NOTIFY = 15
WRITE_NOTIFY = 19
CLIENT_NAME = 20
HOST_NAME = 21
CREATE_CHAN = 18
ACCESS_RIGHTS = 22

commands = {
    "VERSION": 0,
    "EVENT_ADD": 1,
    "WRITE": 4,
    "SEARCH": 6,
    "NOT_FOUND": 14,
    "READ_NOTIFY": 15,
    "WRITE_NOTIFY": 19,
    "CLIENT_NAME": 20,
    "HOST_NAME": 21,
    "CREATE_CHAN": 18,
    "ACCESS_RIGHTS": 22,
}

# CA Message data type codes:
STRING = 0
INT = 1
SHORT = 1
FLOAT = 2
ENUM = 3
CHAR = 4
LONG = 5
DOUBLE = 6
NO_ACCESS = 7

types = {
    "STRING": 0,
    "INT": 1,
    "SHORT": 1,
    "FLOAT": 2,
    "ENUM": 3,
    "CHAR": 4,
    "LONG": 5,
    "DOUBLE": 6,
    "NO_ACCESS": 7,
}

# CA Message monitor mask bits
VALUE = 0x01 # Value change events are reported.
LOG   = 0x02 # Log events are reported (different dead band than VALUE)
ALARM = 0x04 # Alarm events are reported

class PV (object):
    """EPICS Process Variable"""
    def __init__(self,name):
        """name: PREFIX:Record.Field"""
        self.name = name

    def get_value(self): return caget(self.name)
    def set_value(self,value): caput(self.name,value)
    value = property(get_value,set_value)

    def get_info(self): return cainfo(self.name,printit=False)
    info = property(get_info)

    
def caget(PV_name):
    "Retreive the current value of a process variable"
    from time import time
    from threading import Event

    if not PV_name in PVs: PVs[PV_name] = PV_info()
    pv = PVs[PV_name]

    # If a PV is not yet connected wait for it to connect for the number
    # of seconds specified by the variable timeout.
    if not pv.connection_requested: wait = True
    elif pv.connection_requested+timeout > time(): wait = True
    else: wait = False

    if not pv.subscription_ID:
        if not pv.connection_requested: pv.connection_requested = time()
        request_sockets[0].send("get "+PV_name) # Wake up server thread.

    if pv.data == None and wait:
        event = Event()
        pv.update_events += [event]
        event.wait(timeout)
        pv.update_events.remove(event)

    if pv.data == None: return
    return value(pv.data_type,pv.data_count,pv.data)
    
def caput(PV_name,value,wait=False,timeout=60):
    """Modify the value of a process variable
    If wait=True the call returns only after the server has confirmed
    that is has finished processing the write request or the timeout
    has expired."""
    from time import time
    from threading import Event

    if not PV_name in PVs: PVs[PV_name] = PV_info()
    pv = PVs[PV_name]

    if not pv.subscription_ID and not pv.connection_requested:
        pv.connection_requested = time()
    pv.write_data = value
    pv.write_requested = time()
    pv.write_confirmed = 0
    if pv.write_event == None: pv.write_event = Event()
    pv.write_event.clear()

    request_sockets[0].send("put "+PV_name) # Wake up server thread.
    
    if wait: pv.write_event.wait(timeout)

def camonitor(PV_name,timeout=None):
    """Wait for the server to send an update event for the PV."""
    from time import time
    from threading import Event

    if timeout == None: timeout = globals()["timeout"]

    if not PV_name in PVs: PVs[PV_name] = PV_info()
    pv = PVs[PV_name]

    ##if pv.last_updated:
    ##    print "%s changed to %r %.4f s ago" % (PV_name,
    ##        pv.data,time()-pv.last_updated)

    if not pv.subscription_ID:
        if not pv.connection_requested: pv.connection_requested = time()
        request_sockets[0].send("monitor "+PV_name) # Wake up server thread.

    # If the PV has changed in the past 70 ms, let it count as 'changed now'.
    if pv.last_updated - time() > -0.070: return

    event = Event()
    pv.update_events += [event]
    event.wait(timeout)
    pv.update_events.remove(event)

    ##if pv.last_updated:
    ##    print "%s changed to %r %.4f s ago" % (PV_name,
    ##        pv.data,time()-pv.last_updated)


def connect_PV (PV_name):
    """Establish a connection the the server for the process variable
    and request update events"""
    from os import environ
    from socket import socket,gethostname,error,timeout as socket_timeout
    from getpass import getuser
    from struct import pack
    from time import time

    request_time = time()

    if not PV_name in PVs: PVs[PV_name] = PV_info()

    pv = PVs[PV_name]

    if "EPICS_CA_ADDR_LIST" not in environ: addr_list = []
    else: addr_list = environ["EPICS_CA_ADDR_LIST"].split()

    global UDP_socket
    if UDP_socket == None:
        from socket import SOCK_DGRAM,SOL_SOCKET,SO_BROADCAST
        UDP_socket = socket(type=SOCK_DGRAM)
        UDP_socket.setsockopt(SOL_SOCKET,SO_BROADCAST,1)

    for addr in addr_list:
        for port in range(CA_port_number,CA_port_number+3):
            # Establish a TCP/IP connection to a known server if there is
            # not one already.
            if not (addr,port) in connections:
                s = socket()
                s.settimeout(timeout)
                try: s.connect((addr,port))
                except error,msg: debug("%s:%r: %r\n" % (addr,port,msg)); continue
                except socket_timeout: debug("%s: timeout\n" % (addr)); continue
                debug("Connected to %s:%r\n" % (addr,port))
                connections[addr,port] = connection_info()
                connections[addr,port].socket = s
                send(s,message(VERSION,0,10,minor_version,0,0)) # 10 = priority
                send(s,message(CLIENT_NAME,0,0,0,0,0,getuser()))
                send(s,message(HOST_NAME,0,0,0,0,0,gethostname()))
                process_replies()
    if len(addr_list) > 0 and len(connections) == 0: return
        
    if pv.addr == None and not addr_list:
        # Use UDP broadcast to find the server.
        reply_flag = 5 # Do not reply
        if pv.channel_ID == None: pv.channel_ID = new_channel_ID()
        request = message(SEARCH,0,reply_flag,minor_version,pv.channel_ID,
            pv.channel_ID,PV_name+"\0")
        for addr in broadcast_addresses():
            sendto(UDP_socket,(addr,CA_port_number),request)
            pv.servers_queried += [addr]
        process_replies()
        while pv.addr == None and time() - request_time < timeout:
            process_replies()
        if pv.addr == None:
            debug("UDP broadcast: %r not found\n" % PV_name); return

        if not pv.addr in connections:
            addr,cport = pv.addr
            s = socket()
            s.settimeout(timeout)
            try: s.connect((addr,cport))
            except error,msg: debug("%s:%r: %r\n" % (addr,cport,msg)); return
            except socket_timeout: debug("%s: timeout\n" % (addr)); return
            connections[addr,cport] = connection_info()
            connections[addr,cport].socket = s
            send(s,message(VERSION,0,10,minor_version,0,0)) # 10 = priority
            send(s,message(CLIENT_NAME,0,0,0,0,0,getuser()))
            send(s,message(HOST_NAME,0,0,0,0,0,gethostname()))
            process_replies()

    if pv.addr == None and pv.channel_SID == None:
        # Use the list of known servers to find the server hosting the PV.
        for connection in connections.values():
            s = connection.socket
            if pv.channel_ID == None: pv.channel_ID = new_channel_ID()
            send(s,message(CREATE_CHAN,0,0,0,pv.channel_ID,minor_version,
                PV_name+"\0"))
            pv.servers_queried += [s.getpeername()[0]]
        process_replies()
        while (pv.channel_SID == None or pv.addr == None) and \
            time() - request_time < timeout:
            process_replies()
        if pv.channel_SID == None or pv.addr == None:
            debug("%r not found in %r\n" % (PV_name,addr_list))
            return

    if pv.addr and pv.channel_SID == None and pv.addr in connections:
        # Directly connect to the server hosting the PV.
        s = connections[pv.addr].socket
        if pv.channel_ID == None: pv.channel_ID = new_channel_ID()
        send(s,message(CREATE_CHAN,0,0,0,pv.channel_ID,minor_version,
            PV_name+"\0"))
        process_replies()
        while pv.channel_SID == None and time() - request_time < timeout:
            process_replies()
        if pv.channel_SID == None:
            debug("request for %r timed out at %r\n" % (PV_name,pv.addr))
            return

    if pv.subscription_ID == None and pv.addr in connections:
        s = connections[pv.addr].socket
        pv.subscription_ID = new_subscription_ID()
        send(s,message(EVENT_ADD,16,pv.data_type,pv.data_count,pv.channel_SID,
            pv.subscription_ID,pack(">fffHxx",0.0,0.0,0.0,VALUE|LOG|ALARM))) 
        process_replies()
        while pv.data == None and time() - request_time < timeout:
            process_replies()
        if pv.data == None:
            debug("Update of %r timed out at %r\n" % (PV_name,pv.addr))

def process_replies(timeout = 0.001):
    """Interpret any packets comming from the IOC waiting in the system's
    receive queue.
    If timeout > 0 wait for more packets to arrive for the specified number
    of seconds."""
    import socket
    from select import select,error as select_error
    from struct import unpack

    process_pending_connection_requests()
    process_pending_write_requests()

    while True:
        # Use 'select' to check which sockets have data pending in the input
        # queue.
        sockets = []
        if request_sockets[1]: sockets += [request_sockets[1]]
        if UDP_socket: sockets += [UDP_socket]
        for connection in connections.values(): sockets += [connection.socket]
        try: ready_to_read,x,in_error = select(sockets,[],sockets,timeout)
        except select_error: continue # 'Interrupted system call'

        # This indicates that main thread has been terminated.
        if request_sockets == None: break

        if request_sockets[1] in ready_to_read:
            # This indicates that a connected to new PV has been requested.
            request = request_sockets[1].recv(2048)
            debug("Got request: %r\n" % request)
            process_pending_connection_requests()
            process_pending_write_requests()
            
        if UDP_socket in ready_to_read:
            try: messages,addr = UDP_socket.recvfrom(2048)
            except socket.error: messages = ""
            # Several replies may be concantenated. Break them up.
            while len(messages) > 0:
                # The minimum message size is 16 bytes. If the 'payload size'
                # field has value > 0, the total size if 16+'payload size'.
                payload_size, = unpack(">H",messages[2:4])
                message = messages[0:16+payload_size]
                messages = messages[16+payload_size:]
                debug ("Recv upd:%s:%s %s\n" % (addr[0],addr[1],message_info
                    (message)))
                process_message(addr,message)
        if UDP_socket in in_error: debug("UDP error\n")

        for addr in connections.keys():
            connection = connections[addr]
            s = connection.socket
            if s in in_error:
                debug("Lost connection to server %s:%s\n" % addr)
                reset_PVs(addr)
                del connections[addr]
                continue
            if s in ready_to_read:
                # Several replies may be concatenated. Read one at a time.
                # The minimum message size is 16 bytes.
                try: message = s.recv(16)
                except socket.error:
                    debug("Recv: lost connection to server %s:%s\n" % addr)
                    reset_PVs(addr)
                    del connections[addr]
                    continue
                if len(message) == 0:
                    debug("Server %s:%s closed connection\n" % addr)
                    reset_PVs(addr)
                    del connections[addr]
                    break
                # If the 'payload size' field has value > 0, 'payload size'
                # more bytes are part of the message.
                payload_size, = unpack(">H",message[2:4])
                if payload_size > 0: message += s.recv(payload_size)
                debug ("Recv %s:%s %s\n" % (addr[0],addr[1],
                    message_info(message)))
                process_message(addr,message)
            
        process_pending_connection_requests()
        process_pending_write_requests()
        
        if len(ready_to_read) == 0 and len(in_error) == 0: break # select timed out

def process_pending_connection_requests():
    """Check list of PVs unconnected PVs and conntect them."""
    from time import time
    for name in PVs.keys():
        pv = PVs[name]
        if not pv.connection_requested: continue # nothing to do
        if pv.connection_initiated: continue # already in progress...
        debug ("Processing connection request for PV %r\n" % name)
        pv.connection_initiated = time()
        connect_PV(name)

def process_pending_write_requests():
    """Check list of PVs for pending write requests and execute them when possible."""
    for name in PVs.keys():
        pv = PVs[name]
        if pv.write_data == None: continue # nothing to do
        if pv.addr == None: continue # need to postpone
        if pv.channel_SID == None: continue # need to postpone
        if pv.data_type == None: continue # need to postpone

        debug("Processing write request for PV %r\n" % name)
        s = connections[pv.addr].socket
        pv.IOID = pv.IOID + 1
        pv.write_confirmed = 0
        
        data = network_data(pv.write_data,pv.data_type)
        count = data_count(pv.write_data,pv.data_type)
        send(s,message(WRITE_NOTIFY,0,pv.data_type,count,
            pv.channel_SID,pv.IOID,data))
        pv.write_data = None

def process_message(addr,message):
    "Interpret a CA protocol datagram"
    from struct import unpack
    from time import time
    
    header = message[0:16]
    payload = message[16:]
    command,payload_size,data_type,data_count,parameter1,parameter2 = \
        unpack(">HHHHII",header)

    if command == SEARCH: # Reply to a SEARCH request.
        debug ("SEARCH ")
        port_number = data_type
        channel_SID = parameter1 # 'temporary server ID': 0xFFFFFFFF
        channel_ID = parameter2
        debug ("port_number=%r, " % port_number)
        debug ("channel_ID=%r, channel_SID=%r\n" % (channel_ID,channel_SID))
        for name in PVs:
            if PVs[name].channel_ID == channel_ID:
                # Ignore duplicate replies.
                if PVs[name].addr != None:
                    debug ("Ignoring duplicate SEARCH reply for %r from "
                        "%r:%r\n" % (name,addr[0],addr[1]))
                    continue
                PVs[name].addr = (addr[0],port_number)
                debug ("PVs[%r].addr = %r\n" % (name,addr))
                PVs[name].response_time = time()
    elif command == CREATE_CHAN: # Reply to a 'Create Channel' request.
        debug ("CREATE_CHAN ")
        channel_ID = parameter1
        channel_SID = parameter2
        debug ("channel_ID=%r, channel_SID=%r\n" % (channel_ID,channel_SID))
        for name in PVs:
            if PVs[name].channel_ID == channel_ID:
                if PVs[name].channel_SID != None:
                    debug ("Ignoring duplicate CREATE_CHAN reply for %r from "
                        "%r:%r\n" % (name,addr[0],addr[1]))
                    continue
                PVs[name].addr = addr
                debug ("PVs[%r].addr = %r\n" % (name,addr))
                PVs[name].channel_SID = channel_SID
                debug ("PVs[%r].channel_SID = %r\n" % (name,channel_SID))
                PVs[name].data_type = data_type
                debug ("PVs[%r].data_type = %r\n" % (name,data_type))
                PVs[name].data_count = data_count
                debug ("PVs[%r].data_count = %r\n" % (name,data_count))
                PVs[name].response_time = time()
    elif command == ACCESS_RIGHTS:
        # Reply to the CLIENT_NAME/HOST_NAME greeting.
        debug ("ACCESS_RIGHTS ")
        channel_ID = parameter1
        access_bits = parameter2
        debug ("channel_ID %r, %s\n" % (channel_ID,access_bits))
        for name in PVs:
            if PVs[name].channel_ID == channel_ID:
                PVs[name].access_bits = access_bits
                debug ("PVs[%r].access_bits = %r\n" % (name,access_bits))
                PVs[name].response_time = time()
    elif command == READ_NOTIFY:
        # Reply to a synchronous read request (never used).
        debug ("READ_NOTIFY ")
        # Channel Access Protocol Specification, section 6.15.2, says: 
        # parameter 1: channel_SID, parameter 2: IOID
        # However, I always get: parameter 1 = 1, parameter 2 = 1.
        channel_SID = parameter1
        IOID = parameter2
        debug ("channel_SID=%r, IOID=%r, " % (channel_SID,IOID))
        val = value(data_type,data_count,payload)
        debug ("value=%r\n" % val)
        for name in PVs:
            if PVs[name].channel_SID == channel_SID:
                debug ("PVs[%r].data = %r\n" % (name,payload))
                PVs[name].data = payload
                PVs[name].data_type = data_type
                PVs[name].data_count = data_count
                PVs[name].response_time = time()
    elif command == EVENT_ADD: # Asynchronous notification that PV changed.
        debug ("EVENT_ADD ")
        status_code = parameter1
        subscription_ID = parameter2
        debug ("status_code=%r, subscription_ID=%r, " % (status_code,subscription_ID))
        val = value(data_type,data_count,payload)
        debug ("value=%r\n" % val)
        for name in PVs:
            if PVs[name].subscription_ID == subscription_ID and \
                PVs[name].addr == addr:
                PVs[name].data_type = data_type
                PVs[name].data_count = data_count
                debug ("PVs[%r].data = %r\n" % (name,payload))
                t = time()
                if PVs[name].data != None: PVs[name].last_updated = t
                PVs[name].data = payload
                PVs[name].response_time = t
                # Notify client threads waiting for this PV to update.
                for event in PVs[name].update_events: event.set()
    elif command == WRITE_NOTIFY: # Confirmation of a sucessful write.
        debug ("WRITE_NOTIFY ")
        status = parameter1
        IOID = parameter2
        debug ("status_code=%r, IOID=%r\n" % (status,IOID))
        for name in PVs:
            if PVs[name].IOID == IOID and \
                PVs[name].addr == addr:
                t = time()
                debug ("PVs[%r].write_confirmed = %r\n" % (name,t))
                PVs[name].write_confirmed = t
                PVs[name].response_time = t
                # Notfiy client threads waiting for a put operation to complete.
                if PVs[name].write_event: PVs[name].write_event.set()
    elif command == NOT_FOUND:
        channel_ID = parameter1
        PV_name = "unknown"
        for name in PVs:
            if PVs[name].channel_ID == channel_ID: PV_name = name
        debug ("NOT_FOUND: %r\n" % PV_name)
    else: debug ("%r: unknown command code\n" % command)

def new_channel_ID():
    """Return a unique integer to be used as 'Channel ID' for a PV.
    A Channel ID is a client-provided integer number, which the CA server (IOC)
    includes as reference when replying to 'create channel' requests."""
    IDs = [pv.channel_ID for pv in PVs.values()]
    ID = 1
    while ID in IDs: ID += 1
    return ID
 
def new_subscription_ID():
    """Return a unique integer to be used as 'Subscription ID' for a PV.
    A subscription ID is a client-provided integer number, which  the CA server
    (IOC) includes as reference number when sending update events."""
    IDs = [pv.subscription_ID for pv in PVs.values()]
    ID = 1
    while ID in IDs: ID += 1
    return ID

def reset_PVs(addr):
    """If the connection to the server 'addr' is lost, clear outdate PV state
    info."""
    for name in PVs: PVs[name] = PV_info()

def message(command=0,payload_size=0,data_type=0,data_count=0,
        parameter1=0,parameter2=0,payload=""):
    """Assemble a Channel Access message datagram for network transmission"""
    assert data_type is not None
    assert data_count is not None
    assert parameter1 is not None
    assert parameter2 is not None
    
    from math import ceil
    from struct import pack

    if payload_size == 0 and len(payload) > 0:
        # Pad to multiple of 8.
        payload_size = int(ceil(len(payload)/8.)*8)
        
    while len(payload) < payload_size: payload += "\0"

    # 16-byte header consisting of four 16-bit integers
    # and two 32-bit integers in big-edian byte order.
    header = pack(">HHHHII",command,payload_size,data_type,data_count,
        parameter1,parameter2)    
    message = header + payload
    return message

def message_info(message):
    "Text representation of the CA message datagram"
    from struct import unpack
    header = message[0:16]
    payload = message[16:]
    command,payload_size,data_type,data_count,parameter1,parameter2 = \
        unpack(">HHHHII",header)
    s = str(command)
    if command in commands.values():
        s += "("+commands.keys()[commands.values().index(command)]+")"
    s += ","+str(payload_size)
    s += ","+str(data_type)
    if data_type in types.values():
        s += "("+types.keys()[types.values().index(data_type)]+")"
    s += ","+str(data_count)
    s += ", %r, %r" % (parameter1,parameter2)
    if payload:
        s += ", %r" % payload
        if command in (EVENT_ADD,WRITE,READ_NOTIFY,WRITE_NOTIFY):
            s += "(%r)" % value(data_type,data_count,payload)
    return s     

def send(socket,message):
    "Transmit a Channel Access message to an IOC via TCP"
    from socket import error as socket_error
    addr,port = socket.getpeername()
    debug ("Send %s:%s %s\n" % (addr,port,message_info(message)))
    try: socket.sendall(message)
    except socket_error,error: debug ("Send failed: %r\n" % error)

def sendto(socket,addr,message):
    "Transmit a Channel Access message to an IOC via UDP"
    debug ("Send UDP %s:%s %s\n" % (addr[0],addr[1],message_info(message)))
    socket.sendto(message,addr)

def value(data_type,data_count,payload):
    "Convert received network binary data to a Python data type"
    if payload == None: return None
    from struct import unpack
    if data_type == STRING:
        # Null-terminated string.
        # data_count is the number of null-terminated strings (characters)
        value = payload.split("\0")[0:data_count]
        if len(value) == 1: value = value[0]
    elif data_type == SHORT:
        value = unpack(">%dH"%data_count,payload[0:2*data_count])
        if len(value) == 1: value = value[0]
    elif data_type == FLOAT:
        value = unpack(">%df"%data_count,payload[0:4*data_count])
        if len(value) == 1: value = value[0]
    elif data_type == ENUM:
        value = unpack(">%dH"%data_count,payload[0:2*data_count])
        if len(value) == 1: value = value[0]
    elif data_type == CHAR: value = payload[0:data_count]
    elif data_type == LONG:
        value = unpack(">%dI"%data_count,payload[0:4*data_count])
        if len(value) == 1: value = value[0]
    elif data_type == DOUBLE:
        value = unpack(">%dd"%data_count,payload[0:8*data_count])
        if len(value) == 1: value = value[0]
    elif data_type == None: value = payload
    else:
        debug ("unsupported data type %r\n" % data_type)
        value = payload
    return value

def data_count(value,data_type):
    """If value is an array return the number of elements, else return 1.
    In CA, a string counts as a single element."""
    # If the data type is STRING the data count is the number of NULL-
    # terminated strings, if the data type if CHAR the data count is the
    # number is characters in the string, including any NULL characters
    # inside and at the end.
    if issubclass(type(value),basestring) and data_type != CHAR: return 1
    if hasattr(value,"__len__"): return len(value)
    return 1

def network_data(value,data_type):
    "Convert a Python data type to binary data for network transmission"
    from struct import pack
    
    payload = ""
    if data_type == STRING:
        payload = str(value)
        # EPICS requires that strings are NULL-terminated.
        if not payload.endswith("\0"): payload += "\0"
    elif data_type == SHORT:
        if hasattr(value,"__len__"):
            for v in value: payload += pack(">H",v)
        else: payload = pack(">H",value)
    elif data_type == FLOAT:
        if hasattr(value,"__len__"):
            for v in value: payload += pack(">f",v)
        else: payload = pack(">f",value)
    elif data_type == ENUM:
        if hasattr(value,"__len__"):
            for v in value: payload += pack(">H",v)
        else: payload = pack(">H",value)
    elif data_type == CHAR: payload = str(value)
    elif data_type == LONG:
        if hasattr(value,"__len__"):
            for v in value: payload += pack(">I",v)
        else: payload = pack(">I",value)
    elif data_type == DOUBLE:
        if hasattr(value,"__len__"):
            for v in value: payload += pack(">d",v)
        else: payload = pack(">d",value)
    else:
        debug ("network_data: unsupported data type %r\n" % data_type)
        payload = str(value)

    return payload

def broadcast_addresses():
    "A list if IP adresses to use for name resolution broadcasts"
    from os import environ
    if "EPICS_CA_AUTO_ADDR_LIST" in environ and \
       environ["EPICS_CA_AUTO_ADDR_LIST"] == "NO": return []

    # You can override the automatic selection of broadcast
    # addresses by setting the variable 'broadcast_address'.
    if "broadcast_address" in globals() and broadcast_address:
        return [broadcast_address]

    from socket import inet_aton,inet_ntoa,error
    from struct import pack,unpack
    addresses = []
    for address in network_interfaces():
        try: num_address = inet_aton(address)
        except: continue # E.g. IPv6 address
        if not address in addresses: addresses += [address]
        ipaddr, = unpack(">I",num_address)
        ipaddr |= 0x000000FF
        address = inet_ntoa(pack(">I",ipaddr))
        if not address in addresses: addresses += [address]
    return addresses

def network_interfaces():
    """A list of IP adresses of the local network interfaces,
    as strings in numerical dot notation"""
    from socket import getaddrinfo,gethostname
    addresses = [local_ip_address()]
    for addrinfo in getaddrinfo(None,0)+getaddrinfo(gethostname(),0):
        address = addrinfo[4][0]
        if not address in addresses: addresses += [address]
    return addresses

def local_ip_address():
    "IP address of the local network interface as string in dot notation"
    # Unfortunately, Python has no platform-indepdent function to find
    # the IP address of the local machine.
    # As a work-around let us pretend we want to send a UDP datagram to a
    # non existing external IP address.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("129.166.233.186",1024))
    # This code does not geneate any network traffic, because UDP is not
    # a connection-orientation protocol.
    # Now, Python can tell us what would be thet "source address" of the packets
    # if we would sent a packet (but we won't actally sent a packet).
    address,port = s.getsockname()
    return address

def cainfo(PV_name="all",printit=True):
    "Print status info string"
    from socket import gethostbyaddr,herror
    from datetime import datetime
    from time import time

    if PV_name == "all":
        for name in PVs: cainfo(name)
        return

    caget(PV_name)

    s = PV_name+"\n"
    if PV_name in PVs: pv = PVs[PV_name]
    else: pv = PV_info()

    fmt = "    %-14s %.60s\n"

    if pv.channel_SID: val = "connected"
    else: val = "not connected"
    if pv.subscription_ID: val += ", receiving notifications"
    if pv.connection_requested and not pv.subscription_ID:
        val += ", pending for %.0f s" % (time() - pv.connection_requested)
    s += fmt % ("State:",val)
    
    if pv.addr:
        val = pv.addr[0]
        # Try to translate numeric IP address to host name.
        try: val = gethostbyaddr(val)[0]
        except herror: pass
        val += ":%s" % pv.addr[1]
    else: val = "N/A"
    s += fmt % ("Host:",val)

    if pv.access_bits != None:
        val = ""
        if pv.access_bits & 1: val += "read/"
        if pv.access_bits & 2: val += "write/"
        val = val.strip("/")
        if val == "": val = "none"
    else: val = "N/A"
    s += fmt % ("Access:",val)
    
    if pv.data_type != None:
        val = repr(pv.data_type)
        for t in types:
            if types[t] == pv.data_type: val = t
    else: val = "N/A"
    s += fmt % ("Data type:",val)

    if pv.data_count != None: val = str(pv.data_count)
    else: val = "N/A"
    s += fmt % ("Element count:",val)

    if pv.data != None: val = repr(value(pv.data_type,pv.data_count,pv.data))
    else: val = "N/A"
    s += fmt % ("Value:",val)

    if pv.last_updated != 0:
        t = pv.last_updated
        val = "%s (%s)" % (t,datetime.fromtimestamp(t))
        s += fmt % ("Last changed:",val)

    if pv.response_time != 0:
        t = pv.response_time
        val = "%s (%s)" % (t,datetime.fromtimestamp(t))
        s += fmt % ("Time stamp:",val)

    if printit: print s
    else: return s

def PV_status():
    "print status info"
    for name in PVs:
        s = "%s: " % name
        pv = PVs[name]
        for attr in dir(pv):
            if not "__" in attr: s += "%s = %r, " % (attr,getattr(pv,attr))
        s = s.strip(", ")
        print s

def debug(message):
    "Print diagnsotics message, if DEBUG is set to True."
    global debug_t0, debug_last, debug_messages
    if not DEBUG: return
    from time import time
    if not "debug_t0" in globals(): debug_t0 = time()
    if not "debug_last" in globals() or debug_last.endswith("\n"):
        message = ("%.3f " % (time() - debug_t0)) + message
    debug_last = message
    if DEBUG == "silent":
        if not "debug_messages" in globals(): debug_messages = ""
        debug_messages += message
    else:
        from sys import stderr
        stderr.write(message)

debug_messages = ""

def socketpair(family=socket.AF_INET,type=socket.SOCK_STREAM,proto=0):
    """Create a pair of connected socket objects using TCP/IP protocol.
    This is a replacement for the socket library's 'socketpair' function,
    which is not portalbe to Windows.
    """
    from socket import socket,error
    global listen_socket
    listen_socket = socket(family,type,proto)
    port = 1024
    while port < 16535:
        try: listen_socket.bind(("127.0.0.1",port)); break
        except error: port += 1
    listen_socket.listen(1)
    s1 = socket(family,type,proto)
    s1.connect(("127.0.0.1",port))
    s2,addr = listen_socket.accept()
    return s1,s2

# Used to wake up the CA background (server) thread
request_sockets = socketpair()

def background_thread():
    """Server thread.
    Handle CA network communication in background."""
    while True:
        process_replies(1)
        ##except Exception,message: print message
    
from thread import start_new_thread

background_thread_id = start_new_thread (background_thread,())


if __name__ == "__main__": # for testing
    from time import sleep
    from os import environ

    print('DEBUG = "verbose"')
    print('environ["EPICS_CA_ADDR_LIST"] = "128.231.5.169"')
    print('caget("NIH:TEMP.VAL")') 
