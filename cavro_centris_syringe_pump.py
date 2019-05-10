# -*- coding: utf-8 -*-
"""
Author: Philip Anfinrud, Brian Mahon, Friedrich Schotte
Date created: 12/8/2016
Date last modified: 10/17/2017

2017-06-02 1.5 Adapted for 3-way injection port
2017-10-06 1.6 Friedrich, Using IOC
2017-10-17 1.7 Brian, Friedrich, refill_1, refill_3

Setup:
Start desktop shortcut "Centris Syringe IOC"
(Target: python cavro_centris_syringe_pump_IOC.py run_IOC
Start in: %LAUECOLLECT%)
"""
__version__ = "1.7"

from time import sleep,time
from logging import debug,info,warn,error
from thread import start_new_thread
from pdb import pm
from tempfile import gettempdir

from cavro_centris_syringe_pump_IOC import volume,port as valve
volume1,volume2,volume3,volume4 = volume
valve1,valve2,valve3,valve4 = valve

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
V_plug = 5                          #Volume of fluorinert to remove protien from channels 
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

class PumpController(object):
    
    def write_read(self, command_dict):
        """Writes commands to multiple pumps with pump ids and commands assembled in a dictionary. 
        Returns a dictionary of pump ids and their respective responses."""
        from cavro_centris_syringe_pump_IOC import pump_controller
        return pump_controller.write_read(command_dict)
        
    def assign_pids(self):
        """Assigns pump id to each syringe pump according to dictionary; since 
        pump ids are written to non-volatile memory, need only execute once."""
        self.write_read({1: "/1s0ZA1R\r",
                         2: "/1s0ZA2R\r",
                         3: "/1s0ZA3R\r",
                         4: "/1s0ZA4R\r"})
                         
    def syringe_setup(self):
        """Specifies the syringe volumes for each pump in the dictionary of 
        pumps. The command takes effect after power cycling the pumps, and 
        need only be executed once."""
        # U93, U94, U90, U95 -> 50, 100, 250, 500 uL
        self.write_read({1: "/1U90R\r",
                         2: "/1U90R\r",
                         3: "/1U90R\r",
                         4: "/1U90R\r"})

    def move_abs(self,pid,position,speed=25):
        """Move plunger of pump[pid] to absolute position."""
        if 0 <= position <= Vol[pid]:
            self.write_read({pid: "".join(["/1J2V",str(speed),",1A",str(position),",1J0R\r"])})
        else:
            info('Position outside of absolute usable range: 0 <= position <= %r' % Vol[pid])

    def move_rel(self,pid,position,speed=25):
        """Move plunger of pump[pid] to relative position."""
        current = self.positions()[pid]
        if 0 <= current + position <= Vol[pid]:
            if position < 0:
                position = abs(position)
                self.write_read({pid: "".join(["/1J2V",str(speed),",1D",str(position),",1J0R\r"])})
            else:
                self.write_read({pid: "".join(["/1J2V",str(speed),",1P",str(position),",1J0R\r"])})
        else:
             info('Position outside of absolute usable range: 0 <= position <= %r' % Vol[pid])

    def reset(self, *pid):
        """Performs a soft reset on pumps by passing pid number. if left blank, all pumps will soft reset."""
        if len(pid) == 0:
            pid = (1,2,3,4)
        for i in pid:
            self.write_read({pid: "/1!R\r" for pid in port})
        
    def abort(self):
        """Terminates all pump motion and resets J to 0."""
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({pid: "/1J0R\r" for pid in port})           
                         
    def init(self):
        """Initializes pumps, sets Backlash, loads syringes, and leaves valves set to "O"."""
        t0 = time()
        self.write_read({pid: "/1TR\r" for pid in port})
        info("Executing init...")
        info("   emptying syringes...")
        self.write_read({1: "".join(["/1Y7,0,0IV",str(S_load),",1K",str(Backlash),"A0,1R\r"]),
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

    def prime(self):
        """Fills capillaries 1 with fluorinert and 3 with oil."""        
        t0 = time()
        self.write_read({pid: "/1TR\r" for pid in port})
        info("Executing purge...")
        info("   filling capillary 1 with oil and 3 with mother liquor...")
        self.write_read({1: "".join(["/1IV",str(S_load),",1A",str(Vol[1]),",1R\r"]),
                         3: "".join(["/1IV",str(S_load),",1A",str(Vol[3]),",1R\r"])})
        while self.busy(1,3): sleep(0.1)
        info("   purging lines...")
        self.write_read({2: "/1BR\r"}) #Set pump2 valve to "B".
        while self.busy(2): sleep(0.1)
        self.write_read({1: "".join(["/1OV",str(S_prime),",1D",str(V_prime),",1R\r"]),
                         3: "".join(["/1OV",str(S_prime),",1D",str(V_prime),",1R\r"])})
        i = -1
        while self.busy(1,3):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        
        info("      time to purge (s): %r" % (time()-t0))
        self.refill()

   
    def test_inject(self):
       self.move_rel(3,-0.25,1)
       self.move_rel(1,-0.25,1)
    
    def pressure(self):
        self.valve(2,port='O')
        while self.busy(2): sleep(0.02)
        self.write_read({2: "".join(["/1V",str(S_prime),",1P",str(V_prime),",1R\r"])})
        while self.busy(2): sleep(0.1)
        self.valve(2,port='B')
        info("pressure down, valve 2 set to B...")
        
    def pressure_old(self,strokes=-1):
        """Changes pressure using pump4."""        
        t0 = time()
        info("Changing pressure...")
        if strokes < 0:
            for i in range(abs(strokes)):
                self.write_read({2: "".join(["/1IV",str(S_pressure),",1A",str(Vol[4]),",1R\r"])})
                while self.busy(2): sleep(0.1)       
                self.write_read({2: "".join(["/1OV",str(S_pressure),",1A",str(0),",1R\r"])})
                while self.busy(2): sleep(0.1)        
        else:
            for i in range(abs(strokes)):
                self.write_read({2: "".join(["/1OV",str(S_pressure),",1A",str(Vol[4]),",1R\r"])})
                while self.busy(2): sleep(0.1)       
                self.write_read({2: "".join(["/1IV",str(S_pressure),",1A",str(0),",1R\r"])})
                while self.busy(2): sleep(0.1)  
        info("      time to change pressure (s): %r" % (time()-t0))
        
    def flow(self,S = S_flow, pid = 1):
        """Starts flow."""
        info("Executing flow...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({pid: "".join(["/1OV",str(S),",1A0,1R\r"])})
    def run_flow(self,Speed = 0.25, pid = 1,N = 5):
        for i in range(N):
            self.flow(S = Speed, pid= pid)
            while self.busy(pid): sleep(0.1)
            self.fill(pid)
            while self.busy(pid): sleep(0.1)
        
         
    def injecttestN(self):
        """Assumes flow is active; increase flow from [1], while inject xtals using [4], Then increase flow speed
        again, while retracting volume from inject. finish when resume normal flow [1]."""        
        t0 = time()
        #info("Executing inject...")
        self.write_read({1: "".join(["/1V",str(S_flowIX),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIX),",1D",str(V_injectX+0.25),",1R\r"])})
        while self.busy(3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flowIX),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1P",str(V_injectM),",1R\r"])})
        while self.busy(1,3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flow*5),",1F\r"])})
        sleep (0.05)
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"])})
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to inject (s): %r" % (time()-t0))
        info("%r" % self.positions())
        
        
    def injecttest(self):
        """Assumes flow is active; increase flow from [1], while inject xtals using [4], Then increase flow speed
        again, while retracting volume from inject. finish when resume normal flow [1]."""        
        t0 = time()
        #info("Executing inject...")
        self.flush()
        sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flowIX),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIX),",1D",str(V_injectM),",1R\r"])})
        while self.busy(1,3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flowIX),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1P",str(V_injectM/2),",1R\r"])})
        while self.busy(1,3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"])})
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to inject (s): %r" % (time()-t0))
        info("%r" % self.positions())
        
      

    def inject(self):
        """Assumes flow is active; increase flow from [1], while inject xtals using [4], Then increase flow speed
        again, while retracting volume from inject. finish when resume normal flow [1]."""        
        t0 = time()
        #info("Executing inject...")
        self.flush()
        sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flowIM+0.5),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1D",str(V_injectM+0.2),",1R\r"])})
        while self.busy(3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flowIM*2),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1P",str(V_injectM),",1R\r"])})
        while self.busy(3): sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"])})
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to inject (s): %r" % (time()-t0))
        info("%r" % self.positions())
        
    def reverse(self):
        self.write_read({1: "".join(["/1V",str(S_flowIM),",1F\r"]),
                         3: "".join(["/1V",str(S_flowRV),",1P",str(V_injectX),",1R\r"])})
     
        
    def injectN(self):
        """inject without flush."""
        t0 = time()
        #info("Executing inject...")
        self.write_read({1: "".join(["/1V",str(S_flowIM/4),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM/2),",1D",str(V_injectR),",1R\r"])})
        while self.busy(3): sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flowIM),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM/2),",1D",str(V_injectX),",1R\r"])})
        while self.busy(3): sleep(0.02) 
        self.write_read({1: "".join(["/1V",str(S_flowIM),",1F\r"]),
                         3: "".join(["/1V",str(S_flowIM/4),",1P",str(V_injectX/2),",1R\r"])})
        while self.busy(3): sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flow*4),",1F\r"])})
        sleep (0.2)
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"])})
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to inject (s): %r" % (time()-t0))
        info("%r" % self.positions())
        
    def clean(self):
        """injects cleaning solution and pressurizes from pump 4 to remove xtals."""
        t0 = time()
        info("Executing clean...")
        self.abort() 
        self.valve(2,port = "I")
        self.valve(4,port = "O")
        while self.busy(2): sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flowIX),",1D",str(V_injectR),",1R\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1P",str(V_injectX),",1R\r"])})
        while self.busy(1,3): sleep(0.02)
        self.write_read({4: "".join(["/1V",str(S_flush*2),",1D",str(V_clean),",1R\r"])})
        while self.busy(4): sleep(0.02)
        self.write_read({1: "".join(["/1V",str(S_flowRV),",1D",str(V_injectR),",1R\r"]),
                         3: "".join(["/1V",str(S_flowIM),",1D",str(V_injectM),",1R\r"])})
        while self.busy(1,3): sleep(1.0) 
        self.valve(2,port = "B")
        self.valve(4,port = "I")
        while self.busy(2,4): sleep(0.02)
        info("Initiating Flush...")
        self.write_read({1: "".join(["/1V",str(S_flowIX*5),",1D",str(V_flush),",1R\r"])})
        while self.busy(1): sleep(0.02)
        info("Clean Sequence Finished, Resume Flow")
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to clean (s): %r" % (time()-t0))
        self.flow()
    
    def xtal_grow1(self):
        t0 = time()
        info("   Initiating protein droplet generation")
        self.write_read({1: "".join(["/1V",str(S_flowS1),",1D",str(V_droplet),",1R\r"]),
                         4: "".join(["/1V",str(S_flowS1),",1D",str(V_droplet),",1R\r"])})
        while self.busy(1,4):
            sleep(0.1)
        info("   Sample loaded")
        info("time to load (s): %r" % (time()-t0))
                            
    def xtal_grow2(self):
        t0 = time()
        info("   Initiating protein droplet generation")
        self.write_read({1: "".join(["/1V",str(S_flowS1),",1D",str(V_droplet),",1R\r"]),
                         4: "".join(["/1V",str(S_flowS1),",1D",str(V_droplet),",1R\r"])})
        while self.busy(1,4): sleep(0.1)
        self.write_read({1: "".join(["/1V",str(S_flowRV),",1P",str(V_injectR),",1R\r"]),
                         4: "".join(["/1V",str(S_flowRV),",1P",str(V_injectR),",1R\r"])})
        info("   Sample loaded")
        info("time to load (s): %r" % (time()-t0))
        
    def run(self):
        """executes a refill, flow, inject, flush, flow cycle"""
        t0 = time()
        info("%r" % self.positions())
        info("executing run...") 
        
        self.flow(0.2)
        sleep(3.0)
        self.inject_new()
        info("injecting xtals...")
        sleep(8.0)
        self.flush()
        info("flushing xtals...")
        info("resume flow...")
        info("%r" % self.positions())
        info("run time (s): %r" % (time()-t0))
                        
        
    def inject_old(self, V = V_injectX):
        """Assumes flow is active; slow flow from [1], inject using [3], then resume normal flow rate through [3]."""        
        t0 = time()
        #info("Executing inject...")
        info("%r" % self.positions())
        self.write_read({1: "".join(["/1V",str(S_min),",1F\r"]),
                         4: "".join(["/1V",str(S_flow),",1D",str(V_injectX),",1R\r"])})
        sleep(V/S_flow)
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"]),
                         4: "/1TR\r"})
        #info("time to swap flow source (s): %r" % (t1-t0))
        info("time to inject (s): %r" % (time()-t0))
        info("%r" % self.positions())

    def flush(self, V = V_flush, S = S_flush):
        """Stops flow, washes crystals out of tubing, then resumes flow."""        
        t0 = time()
        info("Executing flush...")
        self.write_read({1: "".join(["/1V",str(S),",1F\r"])})
        sleep(V/float(S))
        self.write_read({1: "".join(["/1V",str(S_min),",1F\r"])})
        sleep(2)
        self.write_read({1: "".join(["/1V",str(S_flow),",1F\r"])})

        info("time to flush (s): %r" % (time()-t0))

    def flush_1(self):
        """Stops flow, washes crystals out of tubing, then resumes flow."""        
        t0 = time()
        info("Executing flush...")
        #self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({2: "/1OR\r"})  #Set pump2 valve to "O".
        while self.busy(2): sleep(0.1)

        #info("   filling capillary with water")
        self.write_read({4: "".join(["/1V",str(S_flush),",1D",str(V_flush),",1R\r"])})
        while self.busy(4): sleep(0.1)

        self.write_read({2: "/1BR\r"})  #Set pump2 valve to "B".
        while self.busy(2): sleep(0.1)
        info("time to flush (s): %r" % (time()-t0))

        #self.flow()
        #sleep(1)
        #self.inject()
        
    def flush_2(self,N = 4):
        """Stops flow, washes crystals out of tubing, then resumes flow."""        
        t0 = time()
        info("Executing flush...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({2: "/1OR\r"})  #Set pump2 valve to "O".
        while self.busy(2): sleep(0.1)

        info("   pulling back crystals in capillary 3")
        self.write_read({1: "".join(["/1V",str(S_flush),",1D",str(V_injectX),",1R\r"]),
                         3: "".join(["/1V",str(S_flush),",1P",str(V_injectX),",1R\r"])})
        while self.busy(1,3): sleep(0.1)

        info("   filling capillary with water")
        self.write_read({4: "".join(["/1V",str(S_flush),",1D",str(V_flush),",1R\r"])})
        while self.busy(4): sleep(0.1)

        info("   swishing water back and forth to dislodge/dissolve crystals")
        for i in range(N):
            self.write_read({1: "".join(["/1V",str(S_flush),",1D",str(V_flush),",1R\r"]),
                             4: "".join(["/1V",str(S_flush),",1P",str(V_flush),",1R\r"])})
            while self.busy(1,4): sleep(0.1)
            self.write_read({1: "".join(["/1V",str(S_flush),",1P",str(V_flush),",1R\r"]),
                             4: "".join(["/1V",str(S_flush),",1D",str(V_flush),",1R\r"])})
            while self.busy(1,4): sleep(0.1)
        info("   pushing crystals into capillary 2")
        self.write_read({1: "".join(["/1V",str(S_flush),",1D",str(V_flush),",1R\r"]),
                         2: "".join(["/1V",str(S_flush),",1P",str(V_flush),",1R\r"])})
        while self.busy(1,2): sleep(0.1)

        self.write_read({2: "/1BR\r"})  #Set pump2 valve to "B".
        while self.busy(2): sleep(0.1)

        info("   pushing back crystals in capillary 3")
        self.write_read({1: "".join(["/1V",str(S_flush),",1P",str(V_injectX),",1R\r"]),
                         3: "".join(["/1V",str(S_flush),",1D",str(V_injectX),",1R\r"])})
        while self.busy(1,3): sleep(0.1)
        info("time to flush (s): %r" % (time()-t0))
        self.flow()
        self.inject()
        
    def refillN(self):
        """Loads syringe 1 and 3.""" 
        t0=time()
        info("Executing refill...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({3: "".join(["/1IV",str(S_load),",1A",str(Vol[4]),",1OR\r"]),
                         1: "".join(["/1IV",str(S_load),",1A",str(Vol[1]),",1OR\r"]),
                         4: "".join(["/1IV",str(S_load),",1A",str(Vol[1]),",1OR\r"])})
        i = -1
        while self.busy(1,3):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.valve(2,port = "B")
        self.valve(4,port = "I")
        info("      time to refill (s): %r" % (time()-t0))
        info("%r" % self.valve_read())
        
    def degas(self):
        """increases upstream pressure to remove nucleated air bubbles."""
        info("Degassing lines...")
        self.valve(2, "O")
        sleep(0.1)
        self.flow(S=1.0)
        sleep(3.0)
        self.valve(2, "B")
        sleep(0.1)
        self.flow()
        info("degassing complete, continue flow") 
        
    def refill_1(self):
        """Loads syringe 1 and restarts flow."""
        t0=time()
        info("Executing refill of pump 1...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({1: "".join(["/1IV",str(S_load),",1A",str(Vol[4]),",1OR\r"])})
        i = -1
        while self.busy(1):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.valve(2,port = "B")
        self.valve(4,port = "I")
        info("      time to refill 1 (s): %r" % (time()-t0))
        self.flow() 

    def refill_3(self):
        """Loads syringe 3."""
        t0=time()
        info("Executing refill of pump 3...")
        self.write_read({3: "/1TR\r"})
        self.write_read({3: "".join(["/1IV",str(S_load),",1A",str(Vol[4]),",1OR\r"])})
        i = -1
        while self.busy(3):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.valve(2,port = "B")
        self.valve(4,port = "I")
        info("      time to refill 1 (s): %r" % (time()-t0))

    def refill_all(self):
        """Loads syringe 1 and restarts flow."""
        t0=time()
        info("Executing refill...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({3: "".join(["/1IV",str(S_load),",1A",str(Vol[4]),",1OR\r"]),
                         1: "".join(["/1IV",str(S_load),",1A",str(Vol[1]),",1OR\r"]),
                         4: "".join(["/1IV",str(S_load),",1A",str(Vol[1]),",1OR\r"])})
        i = -1
        while self.busy(1,3):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.valve(2,port = "B")
        self.valve(4,port = "I")
        info("      time to refill (s): %r" % (time()-t0))
        self.flow()
        
    def valve(self,pid,port = "I"):
        """Set port of pump[pid] to 'O', 'I', or 'B'."""
        if port == 'i':
            port = 'I'
        elif port == 'o':
            port = 'O'
        elif port == 'b':
            port = B
        t0 = time()
        self.write_read({pid: "".join(["/1",str(port),"R\r"])})
        while self.busy(pid): sleep(0.1)
        info("time to rotate valve (s): %r" % (time()-t0))

    def empty(self):
        """Empty all syringes; switch all ports to B."""
        self.write_read({1: "/1IV25,1A0,1R\r", 2: "/1IV25,1A0,1R\r",
                         3: "/1IV25,1A0,1R\r", 4: "/1IV25,1A0,1R\r"})
        while self.busy(1, 2, 3, 4): sleep(0.1)
        self.write_read({1: "/1BR\r", 2: "/1BR\r", 3: "/1BR\r", 4: "/1BR\r"})       

    def busy(self, *pids):
        """Returns True if any specified pump is busy. The query (?29) returns 
        the pump status, whose 4th byte is 1 or 0 (1 is busy)."""
        from numpy import nan
        reply = []
        for pid in pids:
            try:
                reply.apend(self.write_read({pid: "/1?29\r"})[4])      
            except:
                 reply.append(nan)
        return reply
    
    def positions(self):
        """Queries positions of all pumps. Returns dict of pids to positions."""
        reply = self.write_read({pid: "/1?18R\r" for pid in port})
        return {pid: float(reply[pid][4:-3]) for pid in reply}

    def valve_read(self,pids = []):
        reply = []
        """Queries positions of all pumps. Returns dict of pids to positions."""

        reply.append(self.write_read({pid: "/1?20R\r" for pid in port}))
        return reply


    def flow_old(self,S = S_flow):
        """Starts flow pfl changes flow speed on the fly."""
        #self.write_read({1: "/1TR\r", 2: "/1TR\r"})
        temp = self.positions()
        info("%r" % temp)
        if self.busy(1,2):
            self.write_read({1: "".join(["/1V",str(S),",1F\r"]),
                             2: "".join(["/1V",str(S),",1F\r"])})
        else:  
           V = min(temp[1],Vol[2]-temp[2]) 
           self.write_read({1: "".join(["/1J1V",str(S),",1D",str(V),",1J0R\r"]),
                            2: "".join(["/1J1V",str(S),",1P",str(V),",1J0R\r"])})  
    
    def purge_12(self):
        """Purge bubbles from capillary using pumps (1,2) to displace 75 uL."""        
        
        self.write_read({pid: "/1TR\r" for pid in port})
        temp = self.positions()
        V = min(temp[1], Vol[2]-temp[2])
        if V < 78: self.refill()
        self.write_read({pid: "/1TR\r" for pid in port})
        info("   purging...")
        self.write_read({4: "/1OR\r"})  #Reposition #4 valve port before inflating.
        while self.busy(4): sleep(0.1)
        self.inflate(V_inflate)
        while self.busy(2): sleep(0.1)
        self.write_read({1: "".join(["/1J1V",str(S_prime),",1D",str(V_purge),",1J0R\r"]),
                         2: "".join(["/1J1V",str(S_prime),",1P",str(V_purge),",1J0R\r"])})
        i = -1
        while self.busy(1, 2):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.refill()

    def purge_32(self):
        """Purge bubbles from capillary using pumps (3,2) to displace 75 uL."""        
        
        self.write_read({pid: "/1TR\r" for pid in port})
        temp = self.positions()
        V = min(temp[3], Vol[2]-temp[2])
        if V < 78: self.refill()
        self.write_read({pid: "/1TR\r" for pid in port})
        info("   purging...")
        self.write_read({4: "/1OR\r"})  #Reposition #4 valve port before inflating.
        while self.busy(4): sleep(0.1)
        self.inflate(V_inflate)
        while self.busy(2): sleep(0.1)
        self.write_read({3: "".join(["/1J1V",str(S_prime),",1D",str(V_purge),",1J0R\r"]),
                         2: "".join(["/1J1V",str(S_prime),",1P",str(V_purge),",1J0R\r"])})
        i = -1
        while self.busy(2, 3):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) #  every 2 s
        self.refill()
    def run_create_pressure(self,N):
        start_new_thread(self.create_low_pressure,(N,))
        
    def run_create_pressure_new(self,N):
        start_new_thread(self.create_low_pressure_new,(N,))
        
    def create_low_pressure_new(self,N):
        from cavro_centris_syringe_pump_IOC import volume, port
        for i in range(N):
            port[1].value = 1
            while port[1].moving: sleep(0.1)
            volume[1].value = 250
            while volume[1].moving: sleep(0.1)
            port[1].value = 0
            while port[1].moving: sleep(0.1)
            volume[1].value = 0
            while volume[1].moving: sleep(0.1)
            
    def create_low_pressure(self, N = 2):
        for i in range(N):
            p.valve(2,'I')
            while self.busy(2): sleep(0.1)
            p.move_abs(2,250)
            while self.busy(2): sleep(0.1)
            p.valve(2,'O')
            while self.busy(2): sleep(0.1)
            p.move_abs(2,0)
            while self.busy(2): sleep(0.1)

    def fill(self, pid = 1):
        while self.busy(pid): sleep(0.1)
        p.valve(pid,'I')
        p.move_abs(pid,250)
        
    def prime_old(self):
        """Use after init; primes syringes and tubing (1,2) and (3,4) at S_load flow rate."""
        info("   priming...")
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({4: "/1OR\r"})
        while self.busy(4): sleep(0.1)
        self.inflate(V_inflate)
        while self.busy(2): sleep(0.1)
        self.write_read({1: "".join(["/1J1V",str(S_load),",1D225,1J0R\r"]),
                         2: "".join(["/1J1V",str(S_load),",1P225,1J0R\r"]),
                         3: "".join(["/1J1V",str(S_load),",1D225,1J0R\r"]),
                         4: "".join(["/1J1V",str(S_load),",1P225,1JBR\r"])})
        i = -1
        while self.busy(1, 2, 3, 4):
            i += 1
            sleep(0.1)
            if (i/20. == i/20): info("%r" % self.positions()) # every 2 s
        self.refill()
                         
    def inflate(self, V = V_inflate):
        """Inflate tubing."""
        self.write_read({1: "/1TR\r", 2: "/1TR\r"})
        self.write_read({2: "".join(["/1J1V",str(S_flush),",1D",str(V),",1J0R\r"])})
        while self.busy(2): sleep(0.1)

    def reinject(self,V = V_flush):
        """Solution from pump 2 is rapidly pushed into the collapsible tubing;
        then flow is continued."""
        t0 = time()
        self.write_read({pid: "/1TR\r" for pid in port})
        self.write_read({4: "/1OR\r"})
        while self.busy(4): sleep(0.1)
        self.write_read({2: "".join(["/1V",str(S_flush),",1D",str(V),",1R\r"])})
        while self.busy(2): sleep(0.1)
        info("time to reinject (s): %r" % (time()-t0))
        self.write_read({4: "/1BR\r"})
        while self.busy(4): sleep(0.1)
        self.flow()
                          

    
if __name__ == "__main__":
    import logging; logging.basicConfig(filename=gettempdir()+'/suringe_pump_DL.log',level=logging.INFO,format="%(levelname)s: %(message)s")
    p = PumpController()
    self = p # for debugging
    print
    print("p.init()")
    print("p.flow()")
    print("p.inject_new() # V = V_injectX")
    print("p.flush() # V = V_flush, S = S_flush")
    print("p.refillF()")
    print("p.pressure() # strokes = -1")
    print("p.positions()")
    print("p.valve(2,'O') # pid, 'O', 'I', or 'B'")
    print("p.valve_read()")
    print("p.move_rel(3,-1,1) # pid,position,speed")
    print("p.refill_1()")
    print("p.refill_3()")
    print("p.abort()")
    
    # p.write_read({4:"/1?20R\r"}) # query valve position
    # p.write_read({1: "/1IR\r"}) # Move pump1 valve to Input
    # p.write_read({2: "/1V0.3,1F\r"}) # Change speed to 0.3 uL/s
    # sum(p.positions().values()[:2])  # Returns sum of first two values
