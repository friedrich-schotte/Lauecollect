#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Authors: Valentyn Stadnytskyi, Philip Anfinrud, Brian Mahon, Friedrich Schotte
Date created: 12/8/2016 (original)
Date last modified: 05/25/2018


"""
__version__ = "1.3"

from time import sleep,time
from logging import debug,info,warn,error
from thread import start_new_thread
from pdb import pm
# Assign default parameters.
Vol = {1:250,2:250,3:250,4:250}     # Volumes of syringes.
Backlash = 100                      # Backlash in increments.
V_prime = 25                       # Volume needed to purge 2.3 m tubing (49 uL/m).
V_purge = 115                       # Volume needed to purge 2.3 m tubing (49 uL/m).
V_inflate = 2                       # Volume used to inflate tubing.
V_deflate = 2                       # Volume used to deflate tubing.
V_clean = 4.0                    # Volume used to advance dlivered xtal droplet
V_flush = 4.0                         # Volume used to flush collapsible tubing.
V_injectX = 0.2                    # Volume used to advance dlivered xtal droplet 
V_injectM = 0.3                    #Volume of mother liqour during inject
V_injectR = 0.2                   # Volume desired for xtal delivery 
V_droplet = 1                      #Volume used to load droplets into cappilary 
V_plug = 5                          #Volume of fluorinert to remove protein from channels 
S_pressure = 250                    # Speed used to change pressure.
S_load = 50                         # Speed used to load syringes.
S_prime = 20                         # Speed used to prime capillaries.
S_flush = 68                        # Speed used to flush collapsible tubing.
S_flow = 0.07                       # Speed used to flow through collapsible tubing.
S_min = 0.002                       # Minimum Speed available.
S_flowIX = 1.0                      # Speed used for injection of xtals
S_flowIM = 0.5                      #Speed of flow for injection cycle
S_flowRV = 0.75                      #Speed of flow for reverse part of injection cycle 
S_flowS1 = 0.05                     #Speed used for small droplet generation 

port = [1,2,3,4]

class Cavro_centris_syringe_pump_LL(object):
    """Cavro Centris Syringe Pumps"""
    ports = {}
    abort_flag = [False,False,False,False]
    from numpy import inf
    max_time_between_replies = {0:inf,1:inf,2:inf,3:inf}

    def discover(self):
        """Find the serial ports for each pump controller"""
        self.wait_time = 0.015
        from serial import Serial
        for port_name in self.available_ports:
            debug("Trying self.ports %s..." % port_name)
            try: 
                port = Serial(port_name)
                port.baudrate = 9600
                port.timeout = 0.4
                port.write("/1?80\r")
                reply = port.readline()
                debug("self.ports %r: reply %r" % (port_name,reply))
                pid = int(reply[6]) # get pump id for new_pump
                self.ports[pid] = port
                info("self.ports %r: found pump %r" % (port_name,pid))
            except Exception,msg: debug("%s: %s" % (Exception,msg))
        for i in self.ports:
            debug("p.pump[%d].name = %r" % (i,self.ports[i].name))
            
    def init(self):
        """Initializes pumps, sets Backlash, loads syringes, and leaves valves set to "O"."""
        self.busy_flag = {}
        for i in range(1,5):
            self.busy_flag[i] = False
        t0 = time()
        self.write_read({pid: "/1TR\r" for pid in port})
        info("Executing init...")
        info("   emptying syringes...")
        self.write_dic({1: "".join(["/1Y7,0,0IV",str(S_load),",1K",str(Backlash),"A0,1R\r"]),
                         2: "".join(["/1Z7,0,0IV",str(S_load),",1K",str(Backlash),"A0,1R\r"]),
                         3: "".join(["/1Y7,0,0IV",str(S_load),",1K",str(Backlash),"A0,1R\r"]),
                         4: "".join(["/1Z7,0,0IV",str(S_load),",1K",str(Backlash),"A0,1R\r"])})
        while self.busy(1,2,3,4): sleep(0.1)
        info("   filling syringes...")
        self.write_read({1: "".join(["/1A",str(Vol[1]),",1R\r"]),
                         2: "".join(["/1A",str(Vol[2]),",1R\r"]),
                         3: "".join(["/1A",str(Vol[3]),",1R\r"]),
                         4: "".join(["/1A",str(Vol[4]),",1R\r"])})
        while self.busy(1,2,3,4): sleep(0.1)
        info("   emptying syringes...")
        self.write_read({1: "".join(["/1A0,1R\r"]),
                         2: "".join(["/1A0,1R\r"]),
                         3: "".join(["/1A0,1R\r"]),
                         4: "".join(["/1A0,1R\r"])})
        while self.busy(1,2,3,4): sleep(0.1)        
        info("   syringes are initialized, primed, and ready to load.")
        info("      time to init (s): %r" % (time()-t0))

    def close(self,pids = [1,2,3,4]):
        for pid in pids:
            try:
                self.ports[pid].close()
            except  Exception as e:
                error(e)
        
    @property
    def available_ports(self):
        """List of device names"""
        from serial.tools.list_ports import comports
        return [port.device for port in comports()]
    
    def write(self,pids = [],command = ''):
        for pid in pids:
            self.ports[pid].flushInput()
            debug('write(): pids %r and command = %r' %(pid,command))
            self.ports[pid].write(command)
            
    def write_dic(self,dic):
        reply = []
        for pid in dic:
            self.write(pids = [pid], command = dic[pid][0])
            info(self.read(pids = [pid], N = dic[pid][1]))
            reply.append(True)
        return reply

    def inquire_dic(self,dic):
        """
        """
        from thread import start_new_thread
        reply = {}
        def inquire_once(reply,pid,dic):
            self.write(pids = [pid], command = dic[pid][0])
            reply.update(self.read_pid(pid, N = dic[pid][1]))
        for pid in dic:           
            start_new_thread(inquire_once,(reply,pid,dic))
        while len(reply) != len(dic):
            sleep(self.wait_time)    
        info(reply)
        return reply

    def inWaiting(self, pids = []):
        reply = {}
        if len(pids) ==0:
            pids = [1,2,3,4]
        for pid in pids:
            reply.update({pid: (self.ports[pid].inWaiting())})
        return reply
    
    def read_pid(self,pid,N):
        from time import time
        from thread import start_new_thread
        reply = {}
        t = time()
        while self.inWaiting([pid])[pid] < N:
            #info(self.inWaiting()[pid] < N)
            sleep(self.wait_time/3.)
            #info('READ while: inWaiting: %r with pid = %r' % (self.inWaiting(),pid))
            if time() > t + 10:
                error('serial port read timeout: time to read = %r' % (time() - t))
                break
        reply[pid] = self.ports[pid].read(N)

        return reply
    
    def read(self,pids = [], N = 0):
        from time import time
        from thread import start_new_thread
        reply = {}
        def read_once(reply,pid):
            t = time()
            while self.inWaiting()[pid] < N:
                #info(self.inWaiting()[pid] < N)
                sleep(self.wait_time/3.)
                #info('READ while: inWaiting: %r with pid = %r' % (self.inWaiting(),pid))
                if time() > t + 10:
                    error('serial port read timeout: time to read = %r' % (time() - t))
                    break
            reply[pid] = self.ports[pid].read(N)
        for pid in pids:
            start_new_thread(read_once,(reply,pid))
        while len(reply) != len(pids):
            #print(len(reply),time() - t)
            sleep(self.wait_time)
        return reply

    def readline(self,pids = [], N = 0):
        from time import time
        reply = {}
        sleep(0.05)
        for pid in pids:
            reply[pid] = self.ports[pid].readline()
        return reply


    def assign_pids(self):
        """Assigns pump id to each syringe pump according to dictionary; since 
        pump ids are written to non-volatile memory, need only execute once."""
        self.write(pids = [1], command ="/1s0ZA1R\r")
        self.write(pids = [2], command = "/1s0ZA2R\r")
        self.write(pids = [3], command = "/1s0ZA3R\r")
        self.write(pids = [4], command = "/1s0ZA4R\r")

    def syringe_setup(self):
        """Specifies the syringe volumes for each pump in the dictionary of 
        pumps. The command takes effect after power cycling the pumps, and 
        need only be executed once."""
        # U93, U94, U90, U95 -> 50, 100, 250, 500 uL
        reply = self.write_dic({1: ["/1U90R\r",7],
                         2: ["/1U90R\r",7],
                         3: ["/1U90R\r",7],
                         4: ["/1U90R\r",7]})
        return reply
    
    def busy(self, pids = [1,2,3,4]):
        reply = {}
        self.write(pids = pids, command = '/1?29R\r')
        reply = self.readline(pids) #N = 8
        debug('busy(): reply = %r' %reply)
        
        for pid in pids:
            if len(reply[pid]) != 8:
                debug('len = %r , reply %r' % (len(reply),reply))
            try:
                if reply[pid][4] == '1':
                    reply[pid] = True
                else:
                    reply[pid] = False
            except Exception as e:
                error(e)
                debug('reply = %r' % reply)
                N = self.ports[pid].inWaiting()
                debug('buffer in: %r' % N)
                debug('rest of the buffer %r' % self.ports[pid].read(N))
                reply[pid] = True
        return reply
        


    def abort(self, pids = [1,2,3,4]):
        reply = {}
        reply = self.inquire_dic({pid: ['/1TR\r',7] for pid in pids})
        for pid in pids:
            if reply[pid] == '\xff/0`\x03\r\n':
                reply[pid] = True
            elif reply[pid] == '\xff/0`\x03\r\n':
                reply[pid] = False
            
        return reply
    
    def valve_get(self,pids = [1,2,3,4]):
        reply = {}
        self.write(pids = pids, command = '/1?20R\r')
        reply = self.read(pids, N = 8)
        for idx in reply:
            reply[idx] = reply[idx][4]   
        return reply
    
    def valve_set(self,dic = {}):
        try:
            if len(dic) != 0:
                for idx in dic:
                    if dic[idx] == 'i':
                        dic[idx] = 'I'
                    elif dic[idx] == 'o':
                        dic[idx] = 'O'
                    elif dic[idx] == 'b':
                        dic[idx] = 'B'
                    for pid in dic:    
                        self.write(pids = [pid], command = "".join(["/1",str(dic[pid]),"R\r"]))
                        self.read(pids = [pid], N = 4)
                reply = True
            else:
                 reply = False
        except Exception as e:
            error(e)
            reply = False
        return reply
    
    def positions(self,pids = [1,2,3,4]):
        """
        return positions of syringe pumps in dictionary format
        """
        self.write(pids = pids, command = "/1?18R\r")
        from time import clock
        from numpy import nan
        reply = self.readline(pids)
        for idx in reply:
            number = reply[idx][4:-3]
            info('number = %r, clock = %r' % (number, clock()))
            try:
                reply[idx] = float(number)
            except Exception as e:
                reply[idx] = nan
                error(e)
        return reply

    def positions_dic(self,dic = {1:0,2:0,3:0,4:0}):
        """
        return positions of syringe pumps in dictionary format
        """
        reply_dic = {}
        
        return reply

    def move_abs(self,pid = 1, position = 0, speed = 25):
        """Move plunger of pump[pid] to absolute position."""
        self.abort(pids = [pid])
        
        from time import sleep
        self.pos_error = 0.002
        position = round(position,3)
        if pid == 0:
            reply = False
        else:
            if 0 <= position <= Vol[pid]:
                self.write(pids = [pid], command = "".join(["/1J2V",str(speed),",1A",str(position),",1J0R\r"]))
                if self.read(pids = [pid], N = 7)[pid][3] == '@':
                    reply = True
                else:
                    reply = False
            else:
                info('Position outside of absolute usable range: 0 <= position <= %r' % Vol[pid])  
            #while not position - self.pos_error <= self.position(pids = [pid])[pid]  <= position + self.pos_error:
                #sleep(0.1)
                reply = False
        return reply    

    def move_rel(self,pid,position,speed=25):
        """Move plunger of pump[pid] to relative position."""
        self.abort(pids = [pid])
        current = self.position(pids = [pid])[pid]
        if 0 <= current + position <= Vol[pid]:
            if position < 0:
                position = abs(position)
                self.write_dic({pid: ["".join(["/1J2V",str(speed),",1D",str(position),",1J0R\r"]),7]})
            else:
                self.write_dic({pid: ["".join(["/1J2V",str(speed),",1P",str(position),",1J0R\r"]),7]})
        else:
             info('Position outside of absolute usable range: 0 <= position <= %r' % Vol[pid])
             
    def flow(self,dic = {}):
        """
        """
        from thread import start_new_thread
        pids = []
        for pid in dic:
            pids.append(pid)
        self.abort(pids)
        reply = {}
        def flow_pid(reply,pid,dic):
            if dic[pid] > 0:
                reply.update(self.inquire_dic({pid: ["".join(["/1OV",str(dic[pid]),",1A0,1R\r"]),7]}))
                if reply[pid][3] == '@':
                    reply[pid] = True
                else:
                    reply[pid] = False
            elif dic[pid] <0:
                reply.update(self.inquire_dic({pid: ["".join(["/1OV",str(abs(dic[pid])),",1A250,1R\r"]),7]}))
                if reply[pid][3] == '@':
                    reply[pid] = True
                else:
                    reply[pid] = False
            else:
                reply[pid] = self.abort(pids = [pid])[pid]
        for pid in dic:
            start_new_thread(flow_pid,(reply,pid,dic))
        while len(reply) != len(dic):
            sleep(self.wait_time)
        return reply    
        
    def reset(self, pid = [1,2,3,4]):
        """Performs a soft reset on pumps by passing pid number. if left blank, all pumps will soft reset."""
        self.inquire_dic({pid: ["/1!R\r",7] for pid in port})

    def fill(self,pid,speed = 25):
        self.abort(pids=[pid])
        self.valve_set({pid: 'i'})
        self.move_abs(pid, 0,speed)
        while self.busy(pids = [pid])[pid]:
            sleep(0.3)
        self.move_abs(pid, 250,speed)
        while self.busy(pids = [pid])[pid]:
            sleep(0.3)
        self.valve_set({pid: 'o'})

        

    def prime(self,pid, N = 5, speed = 25):
        """
        primes a syringe pump with pid = pid and does it N times
        1) aborts execution of any task.
        2)
        """
        def wait(self,pid):
            while self.busy(pids = [pid])[pid]:
                sleep(0.3)
            sleep(0.1)    
        self.abort(pids=[pid])
        for i in range(N):
            self.fill(pid,speed)
            wait(self,pid)
         

    def create_low_pressure(self, N = 0, speed = 75):
        from time import sleep
        from thread import start_new_thread
        def run(self,N):
            def wait(self):
                while self.busy([2])[2]:
                    sleep(0.2)
            for i in range(N):
                self.valve_set({2:'o'})
                wait(self)
                self.move_abs(2,0)
                wait(self)
                self.valve_set({2:'i'})
                wait(self)
                self.move_abs(2,250, speed)
                wait(self)
            self.valve_set({2:'o'})
            wait(self)
            self.move_abs(2,0)
            wait(self)     
        start_new_thread(run,(self,N))

    def create_high_pressure(self, N = 0, speed = 25):
        from time import sleep
        from thread import start_new_thread
        def run(self,N):
            from time import sleep
            def wait(self, t = 0.5):
                while self.busy([2])[2]:
                    sleep(t)
            for i in range(N):
                self.valve_set({2:'i'})
                wait(self)
                self.move_abs(2,0, speed)
                wait(self)
                self.valve_set({2:'o'})
                wait(self)
                self.move_abs(2,250)
                wait(self)
            self.valve_set({2:'i'})
            wait(self)
            self.move_abs(2,250)
            wait(self)     
        start_new_thread(run,(self,N))    

    def release_low_pressure(self):
        self.valve_set({2:'b'})
        
            
    def shutdown(self):
        self.abort(pids = [1,2,3,4])
        self.release_low_pressure()
        
    
    def flush(self, end_flow = 0.25,speed = 100, t = 0.3):
        from time import sleep
        self.flow({1:speed*0.1})
        sleep(t)
        self.flow({1:-0.8*speed*0.1})
        sleep(t)
        self.flow({1:end_flow})

    def inject_crystals(self, liquor_flow = 0.25, crystal_flow = 0.25, t = 2.0):
        """
        injects crystals(slowly) from the middle capillary together with flow from two side capillaries.
        input parameters:
            liquor_flow = 0.25
            crystal_flow = 0.25
            t = 1.0
        sequence:
            flows 1 and 3 with liquor_flow and crystal_flow
            sleep(t)
            flow 1 and 3 with liquor_flow+crystal_flow and -crystal_flow
            sleep(1)
            abort(3)
            flow 1 with liquor_flow speed
        """
        from time import sleep
        self.flow({1:liquor_flow,3:crystal_flow})
        sleep(t)
        self.flow({1:liquor_flow+crystal_flow,3:-crystal_flow})
        sleep(1)
        self.abort([3])
        self.flow({1:liquor_flow})

    def collapse_crease(self, speed = 10, t = 0.3, end_flow = 0.25,):
        """
        """
        from time import sleep
        self.flow({1:-speed})
        sleep(t)
        self.flow({1:speed})
        sleep(t)
        self.flow({1:end_flow})

    def inject(self, end_flow = 0.25):
        """
        the inject function does:
        1) flush
        2) collapse_crease
        3) inject_crystals
        4) resume flow and end_flow speed
        """
        self.flush(end_flow = end_flow)
        self.collapse_crease(end_flow = end_flow)
        self.inject_crystals()
        self.flow({1:end_flow})
        

        
driver = Cavro_centris_syringe_pump_LL()
    
if __name__ == "__main__":
    from tempfile import gettempdir

    import logging;
    logging.basicConfig(#filename=gettempdir()+'/suringe_pump_LL.log',
                                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

    
    
    self = driver # for debugging
    print("driver.discover()")
    print("start_new_thread(driver.prime,(3,2));start_new_thread(driver.prime,(4,2));start_new_thread(driver.prime,(1,2));")

    
    # p.write_read({4:"/1?20R\r"}) # query valve position
    # p.write_read({1: "/1IR\r"}) # Move pump1 valve to Input
    # p.write_read({2: "/1V0.3,1F\r"}) # Change speed to 0.3 uL/s
    # sum(p.positions().values()[:2])  # Returns sum of first two values
