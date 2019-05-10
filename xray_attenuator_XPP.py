"""
Variable Silicon X-ray attenuator of XPP hutch

10 retractable Silicon absorbers with thicknesses from 20 um to 10.24 mm
increasing in powers of two.
Driven by servo motors 20 = in, 0 mm = out.

Friedrich Schotte, 12 Dec 2010
"""
__version__ = "1.0.1"

from EPICS_motor import motor
from CA import PV
from Si_abs import Si_mu


class XrayAttenuator(object):
    motors = [motor("XPP:SB2:MMS:%d" % i) for i in range(26,16,-1)]
    for motor in motors: motor.readback_slop = 0.075
    thicknesses = [0.020*2**i for i in range(0,len(motors))]
    outpos = [0]*len(motors)
    inpos = [20]*len(motors)
    inpos[3] = 19 # Filter #4 is damaged at position 20 mm.

    photon_energy_PV = PV("SIOC:SYS0:ML00:AO627") # in eV

    """Variable Si X-ray attenuator of XPP hutch"""
    def get_transmission(self):
        from numpy import exp
        x = self.pathlength
        E = self.photon_energy
        return exp(-float(Si_mu(E))*x)
    def set_transmission(self,T):
        from numpy import log
        E = self.photon_energy
        x = -log(T)/float(Si_mu(E))
        self.pathlength = x
    transmission = property(get_transmission,set_transmission)
    value = transmission

    def get_photon_energy(self):
        "Photon energy in eV"
        return self.photon_energy_PV.value
    photon_energy = property(get_photon_energy)

    def get_pathlength(self):
        "Thickness of silicon the X-ray beam passes through"
        pathlength = 0
        inserted = self.inserted
        for i in range(0,len(self.motors)):
            if inserted[i]: pathlength += self.thicknesses[i]
        return pathlength
    def set_pathlength(self,pathlength):
        from numpy import rint
        pathlength = min(pathlength,sum(self.thicknesses))
        steps = int(rint(pathlength/min(self.thicknesses)))
        insert = [(steps & 2**i != 0) for i in range(0,len(self.motors))]
        self.inserted = insert
    pathlength = property(get_pathlength,set_pathlength)
        
    def get_inserted(self):
        "True of False for each abosrber, list of 10"
        positions = self.positions
        return [abs(positions[i]-self.inpos[i]) < abs(positions[i]-self.outpos[i])
            for i in range(0,len(self.motors))]
    def set_inserted(self,insert):
        "Inserted: list of booleans, one for each absorber"
        positions = [self.inpos[i] if insert[i] else self.outpos[i]
            for i in range(0,len(self.motors))]
        self.positions = positions
    inserted = property(get_inserted,set_inserted)

    def get_positions(self):
        "Position for each absorber, list of 10"
        return [self.motors[i].value for i in range(0,len(self.motors))]
    def set_positions(self,positions):
        "Inserted: list of positions, one for each absorber"
        for i in range(0,len(self.motors)): self.motors[i].value = positions[i]
    positions = property(get_positions,set_positions)
    
    def get_moving(self):
        """Is any of the absorbers moving?"""
        return any(motor.moving for motor in self.motors)
    def set_moving(self,moving):
        """If moving = False, stop all motors."""
        for motor in self.motors: motor.moving = moving
    moving = property(get_moving,set_moving)

    def stop(self):
        """Stop all motors."""
        for motor in self.motors: motor.stop()

xray_attenuator = XrayAttenuator()

if __name__ == "__main__": # for testing
    from time import sleep
    ##xray_attenuator.transmission = 0.337
    print "moving",xray_attenuator.moving
    print "inserted",xray_attenuator.inserted
    print "pathlength",xray_attenuator.pathlength
    print "photon energy",xray_attenuator.photon_energy
    print "transmission",xray_attenuator.transmission
    sleep(1)
    print "moving",xray_attenuator.moving
