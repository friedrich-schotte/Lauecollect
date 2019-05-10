"""Aerotech Ensemble Motion Controller
Hardware triggered XYZ scans
Friedrich Schotte, NIH, 5 Oct 2013 - 11 Feb 2016"""

__version__ = "1.5" 

from Ensemble_client import EnsembleClient
from array_wrapper import ArrayWrapper
from numpy import rint,nan
from logging import debug,info,warn,error

def integer_register(index,scale="1"):
    def get(self): return self.integer_registers[index]*eval(scale)
    def set(self,value): self.integer_registers[index] = rint(value/eval(scale))
    return property(get,set)

def floating_point_register(index,scale="1"):
    def get(self): return self.floating_point_registers[index]*eval(scale)
    def set(self,value): self.floating_point_registers[index] = value/eval(scale)
    return property(get,set)

class EnsembleTriggeredMotion(EnsembleClient):
    """Motion Controller"""
    ##required_program_filenname = "TriggeredMotion.ab"
    required_program_filenname = "Ensemble_Laue.ab"
    required_version = 4.1

    naxes = integer_register(10)
    nsteps = integer_register(6)
    POS00 = 5 # offset of first coordinate within floating point registers
    
    # Waiting time between steps in base periods
    M = integer_register(3) 
    # Waiting time between steps in seconds
    waitt = integer_register(3,scale="self.dt")
    # Base period (ca. 1 ms)
    dt = (351.934/350.0)*0.024304558/24	# NIH base period (based on internal oscillator for Pico23)
    ##dt = 0.024304558/24 # APS base period (275th subharmonic of P0)
    ##dt = 1.0/960 # LCLS base period (inverse of 8*120 = 960 Hz)

    # Operation mode:
    # 0: close
    # 1: open
    # 2: open Npts times on trigger
    # 3: synchronous (NIH/APS)
    # 4: LCLS edge finding
    # 5: LCLS data collection)
    O_mode = floating_point_register(2) 
    # Handshaking register, should read back "O_mode"
    O_mode_readback = floating_point_register(1) 
   
    # diagnostics
    version = floating_point_register(0)
    trigger_enabled = integer_register(0)
    auto_return = integer_register(1)
    trigger_count = integer_register(4)
    step_count = integer_register(7)
    timer_count = integer_register(9)

    def max_steps(self,naxes=3):
        """Maximum number of positions that can be stored in the controller."""
        ntot = len(self.floating_point_registers)
        nmax = (ntot-self.POS00)/naxes
        return nmax
    
    def get_pos(self):
        """Coordinates on controller coordinate system.
        NxNaxes array of coordinates , N=0,...,Nmax"""
        naxes = self.naxes
        nsteps = self.nsteps
        pos = self.floating_point_registers[self.POS00:self.POS00+nsteps*naxes]\
            .reshape((nsteps,naxes))
        return pos
    def set_pos(self,values):
        nsteps,naxes = values.shape
        self.naxes = naxes
        self.nsteps = nsteps
        self.floating_point_registers[self.POS00:self.POS00+nsteps*naxes] = \
            values.flatten()
    def pos_count(self): return self.nsteps
    _pos = property(get_pos,set_pos)

    def _get_pos(self):
        return ArrayWrapper(self,"pos",method="all")
    def _set_pos(self,values):
        self._pos = values
    pos = property(_get_pos,_set_pos)
    XYZ = xyz = pos  # for backward comptibility

    def get_armed(self):
        """Is the system ready to start a scan on trigger?"""
        return self.O_mode == 3 and self.O_mode_readback == 3
    def set_armed(self,value):
        if value:
            self.O_mode = 3
            self.wait_for("self.O_mode_readback == 3")
        else: self.O_mode = -1
    armed = property(get_armed,set_armed)

    from Ensemble import ensemble # for "program_directory"
    
    def get_program_running(self):
        """Is the Aerobasic program executing the triggered motion loaded
        and running?"""
        from normpath import normpath
        return normpath(self.program_filename) == \
            normpath(self.ensemble.program_directory+"/"+self.required_program_filenname)
    def set_program_running(self,value):
        from normpath import normpath
        if bool(value) == True and not self.program_running:
            self.program_filename = \
                self.ensemble.program_directory+"/"+self.required_program_filenname
        if bool(value) == False: self.program_filename = ""
    program_running = property(get_program_running,set_program_running)
    enabled = program_running # for backward comptibility

    def wait_for(self,condition,timeout=nan):
        """Halt execution until the condition passed as string evaluates to 
        True.
        timeout: in unit of seconds. If specified unconditionally return after
        the number of seconds has passed."""
        from time import time,sleep
        start = time()
        while not eval(condition): 
            if time() - start > timeout: break
            debug("triggered_motion: waiting for %r" % condition)
            sleep(0.05)
        
triggered_motion = EnsembleTriggeredMotion()


if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/lauecollect_debug.log"
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
        filename=logfile)
    self = triggered_motion # for debugging
    from numpy import zeros,arange,nan,array
    print('triggered_motion.ip_address = %r' % triggered_motion.ip_address)
    print('triggered_motion.version >= triggered_motion.required_version')
    print('triggered_motion.naxes')
    print('triggered_motion.max_steps(3)')
    print('triggered_motion.nsteps')
    print('triggered_motion.pos')
    print('triggered_motion.pos = array([zeros(10),arange(0,0.1,0.01),zeros(10)]).T')
    print('triggered_motion.waitt')
    print('triggered_motion.armed = True')
