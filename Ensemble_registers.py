"""Aerotech Ensemble Motion Controller
Client side communicatiing with Ensemble IOC via Cannel Access
Friedrich Schotte, NIH, 5 Oct 2013 - 7 Nov 2014"""

__version__ = "1.3"

from CA import caget,caput
from numpy import asarray
from time import sleep,time
from logging import debug
from array_wrapper import ArrayWrapper

class EnsembleRegisters(object):
    """Motion Controller"""
    def get_integer_registers(self):
        """Target position in dial units"""
        t0 = time(); msg = False
        registers = None
        while registers is None:
            registers = caget("NIH:ENSEMBLE.integer_registers[:]")
            if registers is None:
                if time()-t0 > 1 and not msg:
                    debug("Ensemble: reading integer registers: retrying...")
                    msg = True
                sleep(0.1)
        if time()-t0 > 1: debug("Ensemble: read integer registers")
        return asarray(registers)
    def set_integer_registers(self,value):
        t0 = time(); msg = False
        value = asarray(value)
        caput("NIH:ENSEMBLE.integer_registers[:]",value)
        while not all(self.integer_registers == value):
            if time()-t0 > 1 and not msg:
                debug("Ensemble: waiting for integer registers to update...")
                msg = True
            sleep(0.1)
        if time()-t0 > 1: debug("Ensemble: integer registers updated")
    all_integer_registers = property(get_integer_registers,
        set_integer_registers)

    def get_floating_point_registers(self):
        """Target position in dial units"""
        registers = None
        t0 = time(); msg = False
        while registers is None:
            registers = caget("NIH:ENSEMBLE.floating_point_registers[:]")
            if registers is None:
                if time()-t0 > 1 and not msg:
                    debug("Ensemble: reading floating point registers: retrying...")
                    msg = True
                sleep(0.1)
        if time()-t0 > 1: debug("Ensemble: read floating point registers")
        return asarray(registers)
    def set_floating_point_registers(self,value):
        value = asarray(value)
        attempts = 0
        t1 = time()
        while not nan_equal(self.floating_point_registers,value):
            t0 = time(); msg = False
            if attempts > 0 and not msg:
                debug("Ensemble: writing floating point registers: retrying...")
                msg = True
            caput("NIH:ENSEMBLE.floating_point_registers[:]",value)
            while not nan_equal(self.floating_point_registers,value) and time()-t0<5:
                if time()-t0 > 1 and not msg:
                    debug("Ensemble: waiting for floating point registers to update...")
                    msg = True
                sleep(0.1)
            attempts += 1
        if time()-t1 > 1: debug("Ensemble: floating point registers updated")
    floating_point_registers = property(get_floating_point_registers,
                                        set_floating_point_registers)

    def get_integer_register(self,i):
        """Target position in dial units"""
        t0 = time(); msg = False
        register = caget("NIH:ENSEMBLE.integer_registers[%d]" % i)
        while register is None:
            if time()-t0 > 1 and not msg:
                debug("Ensemble: reading integer register %d: retrying..." % i)
                msg = True
            sleep(0.1)
            register = caget("NIH:ENSEMBLE.integer_registers[%d]" % i)
        if time()-t0 > 1: debug("Ensemble: integer register %d read"%i)
        return register
    def set_integer_register(self,i,value):
        t0 = time(); msg = False
        caput("NIH:ENSEMBLE.integer_registers[%d]" % i, value)
        while not self.get_integer_register(i) == value:
            if time()-t0 > 1 and not msg:
                debug("Ensemble: waiting for integer register %d to update..."%i)
                msg = True
            sleep(0.1)
        if time()-t0 > 1: debug("Ensemble: integer register %d updated"%i)
    def get_integer_register_count(self):
        return asint(caget("NIH:ENSEMBLE.integer_registers_count"))

    def _get_integer_registers(self):
        return ArrayWrapper(self,"integer_register",method="single")
    def _set_integer_registers(self,values): pass
    integer_registers = property(_get_integer_registers,_set_integer_registers)

Ensemble_registers = EnsembleRegisters()


def asfloat(x):
    """Covert x to float without raising an exception, return nan instead."""
    from numpy import nan
    try: return float(x)
    except: return nan

def asint(x):
    """Convert x to float without raising an exception, return 0 instead."""
    try: return int(x)
    except: return 0

def nan_equal(a,b):
    """Are two arrays containing nan identical, assuming nan == nan?"""
    from numpy import asarray
    from numpy.testing import assert_equal
    a,b = asarray(a),asarray(b)
    try: assert_equal(a,b)
    except: return False
    return True


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    from numpy import nan,isnan # for debbugging
    print('ensemble.integer_registers[0] = 1')
    print('y = ensemble.floating_point_registers')
