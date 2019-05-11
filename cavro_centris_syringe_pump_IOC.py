"""
Cavro Centris Syringe Pump driver
Friedrich Schotte, May 31, 2017 - May 10, 2018

RS-323 coummincation oparameters:
9600 baud, 8 bits, no parity, 1 stop bit

Command set:
Commands are single upper case ASCII characters, followed by one or more
comma separated parameters as ASCII-encoded decimal numbers.
Each commad character need to be preceded with "1" (indicating the the command
is destined for the first pump, in case mutiple pumps are connected via CAN).
Commands can be concatenated to a command string. A command string needs to
Start with "/" and end with "\r". Motion commands queue up until the "R" (Run) is
recieved.
Y7,0,0 Home plunger motor with speed 7, leaning it ay position 0.
       Then home valve motors clock-wisr mapping "O" (output) to port 2,
       leaving the value in position "O".
?18    Report the plunger absolute position in microliters
A100,1 move absolute 100 uL
?37    Report top speed in uL/s
V0.2,1 Set top speed to 0.2 uL/s
?20    Reports valve position ([i], [o], or [b])
I      Moves valve to input position via shortest path
O      Moves valve to output position via shortest path
B      Moves valve to bypass position via shortest path
W7     Initialize plunger drive, 7=speed code
w1,0   Initialize valve drive, 1=number of ports,0=clockwise
?43    Number of pump initializations since last device power up or reset. ([Z],[Y],[W])
?17    Report syringe volume

Documentation:
//femto/C/All Projects/drawings/LCP/Cavro Centris Syringe Pumps/
Cavro Centris Syringe Pumps.pages
Operation Manual Cavro Centris Pump, March 2012, 30038165 Rev B
//femto/C/All Projects/drawings/LCP/Cavro Centris Syringe Pumps/
30038165-B-MANUAL CENTRIS.pdf

Setup:
Assign each pump a unique ID. This ID is sttored innon-volatile memory.
These commands need to be executed only once, after identifying the port
name for each pump, using the Windows Device Manager.
set_id("COM29",1)
set_id("COM30",2)
set_id("COM31",3)
set_id("COM32",4)

Usage:

Continuous flow:
volume[1].speed = 1; volume[1].value = 250

Coordinated operation:
pump.SPMG = 0; volume[0].value,volume[1].value = 0,0; pump.SPMG = 3
"""
__version__ = "1.1.1" # port change via EPICS 

from logging import warn,debug,info

class Comm_Ports(object):
    """Cavro Centris Syringe Pumps"""
    ports = {}
    from numpy import inf
    max_time_between_replies = {0:inf,1:inf,2:inf,3:inf}

    def discover(self):
        """Find the serial ports for each pump controller"""        
        from serial import Serial
        for port_name in self.available_ports:
            debug("Trying self.ports %s..." % port_name)
            try: 
                port = Serial(port_name)
                port.timeout = 0.4
                port.write("/1?80\r")
                reply = port.readline()
                debug("self.ports %r: reply %r" % (port_name,reply))
                pid = int(reply[6])-1 # get pump id for new_pump
                self.ports[pid] = port
                info("self.ports %r: found pump %r" % (port_name,pid+1))
            except Exception,msg: debug("%s: %s" % (Exception,msg))
        for i in self.ports:
            debug("p.pump[%d].name = %r" % (i,self.ports[i].name))

    @property
    def available_ports_old(self):
        """List of device names"""
        from os.path import exists
        port_basename = "COM" if not exists("/dev") else "/dev/tty.usbserial"
        ports = []
        for i in range(0,64):
            port_name = port_basename+("%d" % i if i>0 else "")
            ports += [port_name]
        return ports
        
    @property
    def available_ports(self):
        """List of device names"""
        from serial.tools.list_ports import comports
        return [port.device for port in comports()]

    def ports_found(self,ids):
        """Are the serial ports known for each pump?
        ids: 0-based indices
        """
        ports_found = [id in self.ports for id in ids]
        return ports_found

    def names(self,ids):
        """Are the serial ports known for each pump?
        ids: 0-based indices
        """
        names = [self.ports[i].name if i in self.ports else "" for i in ids]
        return names

    def write_read(self,command_dict):
        """Writes commands to multiple pumps with pump ids and commands assembled
        in a dictionary.
        Returns a dictionary of pump ids and their respective responses."""
        if not all(self.ports_found(command_dict.keys())): self.discover() 
        for pid,command in command_dict.iteritems():
            if pid in self.ports:
                try: self.ports[pid].write(command)
                except Exception,msg:
                    warn("Pump %s: %s: %s" % (pid,self.ports[pid].name,msg))
                    del self.ports[pid]
        replies = {}
        for pid in command_dict:
            if pid in self.ports:
                reply = self.ports[pid].readline()
                if len(reply) > 3:
                    status = reply[3]
                    if status not in ["@", "`"]:
                        warn("command %r generated error %r" % (command_dict[pid], status))
            else: reply = ""
            replies[pid] = reply
        debug("Commands: %r" % command_dict)
        debug("Replies: %r" % replies)
        return replies

comm_ports = Comm_Ports()    

class Volumes(object):
    """Cavro Centris Syringe Pumps"""
    def values(self,ids):
        """Volumes of pumps
        ids: list of 0-based indices
        """
        from numpy import nan
        reply = comm_ports.write_read({id: "/1?18\r" for id in ids})
        values = []
        for id in reply:
            try: values += [float(reply[id][4:-3])]
            except: values += [nan]
        return values
    def set_values(self,ids,values):
        """Volumes in uL
        ids: list of 0-based indices
        value: list of volumes in uL
        """
        self.set_moving(ids,[0]*len(ids)) # stop active motion
        comm_ports.write_read(
            {id: "".join(["/1A%s,1R\r"%value]) for (id,value) in zip(ids,values)})

    def speeds(self,ids):
        """Pumping speeds in uL/s
        ids: list of 0-based indices
        """
        from numpy import nan
        reply = comm_ports.write_read({id: "/1?37\r" for id in ids})
        values = []
        for id in reply:
            try: values += [float(reply[id][4:-3])]
            except: values += [nan]
        return values
    def set_speeds(self,ids,values):
        """Pumping speeds in uL/s
        ids: list of 0-based indices
        value: list of speeds in uL/s 
        """
        comm_ports.write_read(
            {id: "".join(["/1V%.3f,1F\r"%value]) for (id,value) in zip(ids,values)})

    def moving(self,ids):
        """Motion active?
        ids: list of 0-based indices
        """
        from numpy import nan
        # The query (?29) returns  the pump status, whose 4th byte is 1 or 0
        # (1 is busy)
        reply = comm_ports.write_read({id: "/1?29\r" for id in ids})        
        values = []
        for id in reply:
            try: values += [int(reply[id][4])]
            except: values += [nan]
        return values
    def set_moving(self,ids,values):
        """Stop motors
        ids: list of 0-based indices
        value: 0 to stop, 1 to ignore 
        """
        comm_ports.write_read({id: "/1TR\r" for (id,value) in zip(ids,values)
            if not value})

    def homed(self,ids):
        """Motor initialized?
        ids: list of 0-based indices
        """
        homed = [n>0 for n in self.homed_count(ids)]
        return homed
    def homed_count(self,ids):
        """Motor initialized?
        ids: list of 0-based indices
        """
        from numpy import nan
        reply = comm_ports.write_read({id: "/1?43\r" for id in ids})
        values = []
        for id in reply:
            try: values += [int(reply[id][4:-3])]
            except: values += [nan]
        return values
    def set_homed(self,ids,values):
        """Execute inialization sequence for motors
        ids: list of 0-based indices
        value: 0 to ignore, 1 to execute home sequence 
        """
        comm_ports.write_read({id: "/1W7R\r" for (id,value) \
            in zip(ids,values) if value})

    def low_limits(self,ids):
        """Low limits in uL
        ids: list of 0-based indices
        """
        return [0]*len(ids)
    def high_limits(self,ids):
        """High limits in uL
        ids: list of 0-based indices
        """
        from numpy import nan
        reply = comm_ports.write_read({id: "/1?17\r" for id in ids})
        values = []
        for id in reply:
            try: value = float(reply[id][4:-3])
            except: value = nan
            values += [value]
        return values

    def stepsizes(self,ids):
        """Motor increment in uL
        ids: list of 0-based indices
        """
        high_limits = self.high_limits(ids)
        max_counts = self.max_counts(ids)
        stepsizes = [V/n for (V,n) in zip(high_limits,max_counts)]
        return stepsizes
    def max_counts(self,ids):
        """High limits in motor steps
        ids: list of 0-based indices
        """
        from numpy import nan
        reply = comm_ports.write_read({id: "/1?16\r" for id in ids})
        values = []
        for id in reply:
            try: value = int(reply[id][4:-3])
            except: value = nan
            values += [value]
        return values

volumes = Volumes()

class Ports(object):
    """Cavro Centris Syringe Pump Ports"""
    numbers = {'o':0,'i':1,'b':2}
    
    def number(self,letter):
        from numpy import nan
        if letter in self.numbers: number = self.numbers[letter]
        else: number = nan
        return number
    def letter(self,number):
        if number in self.numbers.values():
            letter = self.numbers.keys()[self.numbers.values().index(number)]
        else: letter = 'o'
        return letter
        
    def values(self,ids):
        """Status of pump valves as dictionary of one-letter codes
        n = ?
        ids: list of 0-based indices
        """
        replies = comm_ports.write_read({id:"/1?20\r" for id in ids})
        values = []
        for id in replies:
            # 'o'=out,'i'=in,'b'=bypass,'n'=not initialized
            try: letter = replies[id][4:-3] 
            except: letter = ""
            value = self.number(letter)
            debug("port.value[%r] = %r (%r)" % (id,value,letter))
            values += [value]
        return values
    def set_values(self,ids,values):
        """Volumes in uL
        ids: list of 0-based indices
        value: list of volumes in uL
        """
        ##self.set_moving(ids,[0]*len(ids)) # stop active motion
        letters = [self.letter(value) for value in values]
        comm_ports.write_read(
            {id: "".join(["/1%sR\r"%letter.upper()]) for (id,letter) in zip(ids,letters)})

    def moving(self,ids): return volumes.moving(ids)
    def set_moving(self,ids,values): volumes.set_moving(ids,values)

    def homed(self,ids):
        """Motor initialized?
        ids: list of 0-based indices
        """
        # If the command "?20" (valve position0 returns "n", rather than "i",
        # "o" or "b" the valve have not been initialized yet.
        from numpy import nan
        replies = comm_ports.write_read({id: "/1?20\r" for id in ids})
        values = []
        for id in replies:
            try: value = reply[id][4:-3] != "n"
            except: value = nan
            values += [value]
        return values
    def set_homed(self,ids,values):
        """Execute inialization sequence for motor
        ids: list of 0-based indices
        value: 0 to ignore, 1 to execute home sequence 
        """
        comm_ports.write_read({id: "/1w1,0R\r" for (id,value) \
            in zip(ids,values) if not value})

ports = Ports()

def set_id(port_name,id):
    """Assign a unique ID to a pump controller.
    Thsi ID will be stord in non-volatile memory
    port_name: e.g. "COM29"
    id: 1-based index
    """
    write_port(port_name,"/1s0ZA%sR\r" % i)

def write_port(port_name,command):
    """Send a connad to a specific comm port
    port_name: e.g. "COM29"
    """
    from serial import Serial
    port = Serial(port_name)
    port.write(command)


class Syringe_Pump_IOC(object):
    name = "cavro_centris_syringe_pump_IOC"
    from persistent_property import persistent_property
    prefix = persistent_property("prefix","NIH:PUMP")
    scan_time = persistent_property("scan_time",3.0)
    N = persistent_property("N",4) # number of pumps
    running = False
    from thread import allocate_lock
    lock = allocate_lock()

    class queue: # command queue
        commands = {}
        replies = {}
        volume_values = {}
        volume_speeds = {}
        volume_moving = {}
        ports_values = {}
        port_moving = {}

    def get_EPICS_enabled(self):
        return self.running
    def set_EPICS_enabled(self,value):
        from thread import start_new_thread
        if value:
            if not self.running: start_new_thread(self.run,())
        else: self.running = False
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def run(self):
        """Run EPICS IOC"""
        from CAServer import casput,casmonitor,casdel
        from numpy import isfinite
        from time import time
        self.running = True
        # Initialization
        casput(self.prefix+".SCAN",self.scan_time)
        casput(self.prefix+".SPMG",3) # 0:Stop,1:Pause,2:Move,3:Go
        for i in range(0,self.N):
            casput(self.prefix+"%d.AOUT"%(i+1),"") # ASCII output string to device
            casput(self.prefix+"%d.AINP"%(i+1),"") # ASCII input string from device
        # Static PVs
        for i in range(0,self.N):
            casput(self.prefix+"%d:VOLUME.DESC"%(i+1),"Pump%d"%(i+1))
            casput(self.prefix+"%d:VOLUME.EGU"%(i+1),"uL")
            casput(self.prefix+"%d:PORT.DESC"%(i+1),"Valve%d"%(i+1))
            casput(self.prefix+"%d:PORT.EGU"%(i+1),"OIB")
            casput(self.prefix+"%d:VOLUME.CNEN"%(i+1),1)
            casput(self.prefix+"%d:PORT.CNEN"%(i+1),1)
        # Monitor client-writable PVs
        casmonitor(self.prefix+".SCAN",callback=self.monitor)
        casmonitor(self.prefix+".SPMG",callback=self.monitor)
        for i in range(0,self.N):
            casmonitor(self.prefix+"%d.AOUT"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d.AINP"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d:VOLUME.VAL"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d:VOLUME.VELO"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d:PORT.VAL"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d:VOLUME.STOP"%(i+1),callback=self.monitor)
            casmonitor(self.prefix+"%d:PORT.STOP"%(i+1),callback=self.monitor)
        while self.running:
            if self.scan_time > 0 and isfinite(self.scan_time):
                for i in range(0,self.N):
                    if comm_ports.max_time_between_replies[i] > 10:
                        comm_ports.max_time_between_replies[i] = 0
                        debug("Reading pump %d configuration"%(i+1))
                        casput(self.prefix+"%d:VOLUME.VAL"%(i+1),volumes.values([i])[0])
                        casput(self.prefix+"%d:VOLUME.LLM"%(i+1),volumes.low_limits([i])[0])
                        casput(self.prefix+"%d:VOLUME.HLM"%(i+1),volumes.high_limits([i])[0])
                        casput(self.prefix+"%d:PORT.VAL"%(i+1),ports.values([i])[0])
                t = time()
                values = volumes.values(range(0,self.N))
                for i in range(0,self.N):
                    casput(self.prefix+"%d:VOLUME.RBV"%(i+1),values[i])
                self.process_command_queue()
                values = ports.values(range(0,self.N))
                for i in range(0,self.N):
                    casput(self.prefix+"%d:PORT.RBV"%(i+1),values[i])
                self.process_command_queue()
                moving = volumes.moving(range(0,self.N))
                for i in range(0,self.N):
                    casput(self.prefix+"%d:VOLUME.DMOV"%(i+1),not moving[i])
                    casput(self.prefix+"%d:PORT.DMOV"%(i+1),not moving[i])
                self.process_command_queue()
                speeds = volumes.speeds(range(0,self.N))
                for i in range(0,self.N):
                    casput(self.prefix+"%d:VOLUME.VELO"%(i+1),speeds[i])
                self.process_command_queue()
                sleep(t+1*self.scan_time-time())
                casput(self.prefix+".SCANT",time()-t) # post actual scan time for diagnostics
            else:
                casput(self.prefix+".SCANT",nan)
                sleep(0.1)
        casdel(self.prefix)

    def monitor(self,PV_name,value,char_value):
        """Handle client changes to PVs"""
        with self.lock: # Allow only one thread at a time inside this function.
            info("Received request %s=%r" % (PV_name,value))
            # Delay execution of client requests storing them in a command queue.
            from CAServer import casput
            if PV_name == self.prefix+".SCAN":
                self.scan_time = value
                casput(self.prefix+".SCAN",self.scan_time)
            for i in range(0,self.N):
                if PV_name == self.prefix+"%d.AOUT"%(i+1):
                    self.queue.commands[i] = value # queue for execution
                elif PV_name == self.prefix+"%d:VOLUME.VAL"%(i+1):
                    self.queue.volume_values[i] = value # queue for execution
                elif PV_name == self.prefix+"%d:VOLUME.VELO"%(i+1):
                    self.queue.volume_speeds[i] = value # queue for execution
                elif PV_name == self.prefix+"%d:VOLUME.STOP"%(i+1):
                    self.queue.volume_moving[i] = not value # queue for execution
                elif PV_name == self.prefix+"%d:PORT.VAL"%(i+1):
                    self.queue.ports_values[i] = value # queue for execution
                elif PV_name == self.prefix+"%d:PORT.STOP"%(i+1):
                    self.queue.ports_values_moving[i] = not value # queue for execution
            info("Command count: %r" % len(self.queue.commands))

    def process_command_queue(self):
        """Handle client changes to PVs that where queued up by 'monitor'
        in a synchronous ways."""
        with self.lock: # Allow only one thread at a time inside this function.
            if not self.queue_halted:
                from CAServer import casput
                if self.queue.commands:
                    info("Sending commands %r" % self.queue.commands)
                    replies = comm_ports.write_read(self.queue.commands)
                    self.analyze_commands(self.queue.commands)
                    info("Got replies %r" % replies)
                    for i in replies:
                        info("Updating %s=%r" % (self.prefix+"%d.AINP"%(i+1),replies[i]))
                        casput(self.prefix+"%d.AINP"%(i+1),replies[i],update=True)
                    self.queue.commands = {}
                if self.queue.volume_values:
                    volumes.set_values(self.queue.volume_values.keys(),self.queue.volume_values.values())
                    V = self.queue.volume_values
                    for i in V: casput(self.prefix+"%d:VOLUME.VAL"%(i+1),V[i])            
                    self.queue.volume_values = {}
                if self.queue.volume_speeds:
                    volumes.set_speeds(self.queue.volume_speeds.keys(),self.queue.volume_speeds.values())
                    indices = self.queue.volume_speeds.keys()
                    speeds = volumes.speeds(indices) # read back values
                    for i in indices: casput(self.prefix+"%d:VOLUME.VELO"%(i+1),speeds[i])            
                    self.queue.volume_speeds = {}
                if self.queue.ports_values:
                    ports.set_values(self.queue.ports_values.keys(),self.queue.ports_values.values())
                    p = self.queue.ports_values
                    for i in p: casput(self.prefix+"%d:PORT.VAL"%(i+1),p[i])            
                    self.queue.ports_values = {}
                if self.queue.volume_moving:
                    volumes.set_moving(self.queue.volume_moving.keys(),self.queue.volume_moving.values())
                    self.queue.volume_moving = {}

    def analyze_commands(self,command_dict):
        """Updaste state info base on serial commands snet directly to the
        pump onctroller"""
        from CAServer import casput
        from parse import parse
        for i,command in command_dict.iteritems():
            values = parse("/{}A{value:g},1{}",command) # Absolute volume
            if values: casput(self.prefix+"%d:VOLUME.VAL"%(i+1),values["value"]) 
        
    def get_queue_halted(self):
        """Is the execution queue in the IOC currently halteded?"""
        from CAServer import casget
        return casget(self.prefix+".SPMG") <=1 # 0:Stop,1:Pause,2:Move,3:Go
    def set_queue_halted(self,value):
        from CAServer import casput
        return casput(self.prefix+".SPMG",0 if value else 3)
    queue_halted = property(get_queue_halted,set_queue_halted)

syringe_pump_IOC = Syringe_Pump_IOC()


class PumpController(object):
    name = "cavro_centris_syringe_pump"
    from persistent_property import persistent_property
    prefix = persistent_property("prefix","NIH:PUMP")
    timeout = 3.0
    
    def write_read(self,command_dict):
        """Writes commands to multiple pumps with pump ids and commands
        assembled in a dictionary. (with 1-based indices for the pumps)
        Returns a dictionary of pump ids and their respective responses."""
        from CA import caput,camonitor
        from time import time,sleep

        self.replies = {}
        self.monitor_ids = command_dict.keys()
        for i in command_dict:
            camonitor(self.prefix+"%s.AINP"%i,callback=self.monitor)
        if len(command_dict) > 1: caput(self.prefix+".SPMG",0) # halt queue
        self.replies = {}
        for i,command in command_dict.iteritems():
            caput(self.prefix+"%s.AOUT"%i,command)
        if len(command_dict) > 1: caput(self.prefix+".SPMG",3) # resume queue
        t0 = time()
        while not all([i in self.replies for i in command_dict]):
            if time()-t0 > self.timeout: break
            sleep(0.010)
        return self.replies
    
    def monitor(self,PV_name,value,char_value):
        """Handle client changes to PVs"""
        debug("Got PV update %s=%r",PV_name,value)
        for i in self.monitor_ids:
            if PV_name == self.prefix+"%s.AINP"%i: self.replies[i] = value

    def get_queue_halted(self):
        """Is the execution queue in the IOC currently halteded?"""
        from CA import caget
        return caget(self.prefix+".SPMG") <=1
    def set_queue_halted(self,value):
        from CA import caput
        return caput(self.prefix+".SPMG",0 if value else 3)
    queue_halted = property(get_queue_halted,set_queue_halted)

pump_controller = PumpController()


def alias(name):
    """Make property given by name be known under a different name"""
    def get(self): return getattr(self,name)
    def set(self,value): setattr(self,name,value)
    return property(get,set)

from EPICS_motor import EPICS_motor
class Syringe_Pump(EPICS_motor):
    command_value = alias("VAL") # EPICS_motor.command_value not changable

volume = [
    EPICS_motor(prefix="NIH:PUMP%d:VOLUME"%(i+1),name="syringe_pump%d"%(i+1)) \
    for i in range(0,4)]
port = [
    EPICS_motor(prefix="NIH:PUMP%d:PORT"%(i+1),name="syringe_pump%d"%(i+1)) \
    for i in range(0,4)]

from CA import Record
pump = Record(prefix="NIH:PUMP")

def sleep(seconds):
    """Delay execution by the given number of seconds"""
    # This version of "sleep" does not throw an excpetion if passed a negative
    # waiting time, but instead returns immediately.
    from time import sleep
    if seconds > 0: sleep(seconds)

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging;
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    ##import CAServer; CAServer.LOG = True; CAServer.verbose = True
    self = ports # for debugging
    from sys import argv
    if "run_IOC" in argv: syringe_pump_IOC.run()
    else:
        print('syringe_pump_IOC.EPICS_enabled = True')
        ##print('comm_ports.available_ports')
        ##print('comm_ports.discover()')
        ##print('pump_controller.write_read({i: "/1?18\\r" for i in [0,1]})')
        ##print('ports.values([0])')
        ##print('ports.set_values([0],[0])')
