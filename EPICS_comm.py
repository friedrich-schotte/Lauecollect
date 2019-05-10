"""
EPICS based asynchroneous commincations: RS-323, GPIB, TCP/IP

Friedrich Schotte, NIH 4 Oct 2008 - 28 Mar 2013
"""
# Serial record fields:
# TMOD: Transfor mode: 0 = write/read, 1 = write, 2 = read, 3 = flush
# AOUT: Output buffer. Data is send as soon as AOUT is changed. Limited to
#       40 characters.
# TMOT: Timeout in seconds (floating point value)
# OEOS: Output terminator
# IFMT: Input format: 0 = ASCII, 1 = hybrid, 2 = binary
# IEOS: Input terminator
# BINP: Binary Input: This variable contains the received data.
# TINP: Translated input: This variable contains the received data, with control
#       characters replaced by escape codes, e.g. ASCII 13 -> "\r".
#       Limited to 40 bytes.
#       TINP retains its old value if no data is received and a timeout occurs.
#       If NORD=0, TINP is not valid.
# NRRD: Number of requested read bytes.
# NORD: Number of read bytes.
# EOMR: End of Media? Reason: 0 = none (timeout), 1 = count, 2 = EOS
# SCAN: 0 = passive: changing AOUT triggers sending.
#       1 = event (meaning?)
#       2 = I/O Intr: PROC=1 triggers sending, received data updates TINP
#       3-9: periodic scan rates. Automatically resend AOUT at intervals of 10s,
#       5s,2s,1s,0.5s,0.2s,0.1s
# PROC: If set to 1: If TMOD = 1, send data in AOUT. If TMOD = 2, receive data
#       until either an input terminator is received or NRRD bytes are
#       received, or a timeout occurs.
# BAUD: Baud rate: 0 = unkonwn, 1 = 300, 2 = 600, 3 = 1200, 4 = 2400, 5 = 4800,
#       6 = 9600, 7 = 19200, 8 = 38400, 9 = 57600, 10 = 115200, 11 = 230400
# DBIT: Data bits: 0 = unknown, 1 = 5, 2 = 6, 3 = 7, 4 = 8
# SBIT: Stop bits: 0 = unknown, 1 = 1, 2 = 2
# PRTY: Parity: 0 = unknown, 1 = none, 2 = even, 3 = odd
# FCTL: Flow control: 0 = unknown, 1 = none, 2 = hardware

# based on aps.anl.gov/epics/modules/soft/asyn/R3-1/asynRecord.html

from CA import caput,caget
from time import sleep,time

__version__ = "1.5.1"

# For compatibility for "serial" module.
PARITY_NONE = "N"
PARITY_EVEN = "E"
PARITY_ODD = "O"
SEVENBITS = 7
EIGHTBITS = 8
STOPBITS_ONE = 1
STOPBITS_TWO = 2

class CommPort(object):
    """EPICS-controlled communications port"""
    
    def __init__(self,port):
        """port: EPICS record name, e.g. ID14B:serial16"""
        self.port = port

    def write(self,string):
        """Send data"""
        caput(self.port+".TMOD",1,wait=True) # 1 = write
        caput(self.port+".OEOS","\0") # no output terminator
        caput(self.port+".SCAN",0) # 0 = passive
        # If case string contains binary data, EpicsCA would strip away trailing
        # null characters. Seding non-ASCII chacters as except codes
        # makes sure that null characters are sent, too.
        encoded_string = repr(string)[1:-1]
        caput(self.port+".AOUT",encoded_string)

    def read(self,nchar=1):
        """Receive data, until either nchar bytes have received or a timeout has
        occurred"""
        caput(self.port+".TMOD",2) # 2 = read
        caput(self.port+".IEOS","\0",wait=True) # no input terminator
        caput(self.port+".NRRD",nchar,wait=True)
        # For unknown reason, following fails at the first try, but succeed at
        # the second try.
        try: caput(self.port+".PROC","1",wait=True) # this will cause it to wait for data
        except: caput(self.port+".PROC","1",wait=True)
        try: return caget(self.port+".TINP")
        except: return caget(self.port+".TINP")

    def query(self,string,terminator="\n",count=0):
        """Receive data, until either the terminator character was received,
        the number of bytes given by 'count' have have received or
        a timeout has occurred."""
        # The first 'caget' after python statup always fails. As a work-around, use a
        # dummy caget just in case.
        if caget(self.port+".TMOD") != 0:
            caput(self.port+".TMOD",0,wait=True) # 0 = write/read
        if string.endswith("\n"):
            caput(self.port+".OEOS","\n",wait=True)
            string = string[0:-1]
        elif caget(self.port+".OEOS") != "":
            caput(self.port+".OEOS","\0",wait=True) # not output terminator
        if count:
            if caget(self.port+".IEOS") != "":
                caput(self.port+".IEOS","\0",wait=True) # "\0" = none
        elif terminator: 
            if caget(self.port+".IEOS") != terminator:
                caput(self.port+".IEOS",terminator,wait=True) # input terminator
        if caget(self.port+".IFMT") != 1:
            caput(self.port+".IFMT",1,wait=True) # 1 = hybrid
        if caget(self.port+".SCAN") != 0:
            caput(self.port+".SCAN",0,wait=True) # 0 = passive
        if caget(self.port+".NRRD") != count:
            caput(self.port+".NRRD",count,wait=True) # number of chars (0 = unlimited) 
        # If case string contains binary data, EpicsCA would strip away trailing
        # null characters. Sending non-ASCII chacters as except codes
        # makes sure that null characters are sent, too.
        encoded_string = repr(string)[1:-1]
        caput(self.port+".AOUT",encoded_string,wait=True)
        n = caget(self.port+".NORD")
        if n == None: n = 0
        if n == 0: return "" # nothing read
        # With EpicsCA it is (as of June 2009) not possible to reliably retreive
        # special characters from the BINP (binary input) variable, because
        # EpicsCA strips off trailing  carriage return and null characters
        # before passing back a string. Thus, I read the TINP (Text input)
        # variable instead.
        reply = caget(self.port+".TINP")
        if not reply: reply = ""
        # Special characters in the TINP field are encoded as octal
        # escape sequences. Decode them.
        ##print "reply",repr(reply)
        reply = eval("'"+reply+"'")
        if caget(self.port+".EOMR") == 2: # 2 = EOS 
            return reply+terminator # terminator was stripped off, add it back
        return reply

    def get_timeout(self): return caget(self.port+".TMOT")
    def set_timeout(self,value): caput(self.port+".TMOT",value)
    timeout = property(get_timeout,set_timeout,
        doc="maxmimum read time in seconds")

    # The following prperties are only used for serial ports.

    baudrates = ["unknown",300,600,1200,2400,4800,9600,19200,38400,57600,115200,
        230400]
    def get_baudrate(self): return self.baudrates[caget(self.port+".BAUD")]
    def set_baudrate(self,value):
        caput(self.port+".BAUD",self.baudrates.index(value))
    baudrate = property(get_baudrate,set_baudrate,
        doc="speed of serial line")
    
    bytesizes = ["unknown",5,6,7,8]
    def get_bytesize(self): return self.bytesizes[caget(self.port+".DBIT")]
    def set_bytesize(self,value):
        caput(self.port+".DBIT",self.bytesizes.index(value))
    bytesize = property(get_bytesize,set_bytesize,
        doc="number of data bits (7 or 8)")

    parities = ["unknown","N","E","O"]
    def get_parity(self): return self.parities[caget(self.port+".PRTY")]
    def set_parity(self,value):
        caput(self.port+".PRTY",self.parities.index(value))
    parity = property(get_parity,set_parity,
        doc="checkum bit: N = none, E = even, O = odd")

    def get_stopbits(self): return caget(self.port+".SBIT")
    def set_stopbits(self,value): caput(self.port+".SBIT",value)
    stopbits = property(get_stopbits,set_stopbits,
        doc="checkum bit: N = none, E = even, O = odd")

    use_rtscts = ["unknown",False,True]
    def get_rtscts(self): return self.use_rtscts[caget(self.port+".FCTL")]
    def set_rtscts(self,value):
        caput(self.port+".FCTL",self.use_rtscts.index(value))
    rtscts = property(get_rtscts,set_rtscts,
        doc="Hardware handshake: use 'Ready To Send' / 'Clear To Send' lines")

    # Software flow control is not supported by EPICS
    xonxoff = property(lambda self: False,lambda self,v: None)

    # Modem handshake is not supported by EPICS
    dsrdtr = property(lambda self: False,lambda self,v: None)

def wait_for_change(pvname):
    "This return only when the named process variable changes."
    global changed
    pv = PV(pvname,callback=on_change)
    pend_event (0.05)
    changed = False
    while not changed: pend_event (0.05)

def on_change(pv):
    global changed
    changed = True
    print pv.pvname,"changed to",pv.value

if __name__ == "__main__": # for testing
    port = CommPort("14IDB:SAMPLECOM")
    print "%r" % port.query ("PFBKPROG(@1)\n")
