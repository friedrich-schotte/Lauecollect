"""
Milliscond X-ray shutter

The shutter is an aluminum block a slot for the X-ray beam
operated by a direct drive rotary servo motor driven by an Aerotech
Soloist server motor controller with an Etherner interface.

Friedrich Schotte, Feb 17, 2017 - Jun 30, 2017
"""
__version__ = "4.0.2" # top speed: closed_pos to closed_pos2

class Ms_Shutter(object):
    name = "ms_shutter"
    from persistent_property import persistent_property

    closed_pos = persistent_property("closed_pos",-0.3) # deg
    open_pos = persistent_property("open_pos",9.7) # deg
    # alternating closed position used only in pulsed mode
    closed_pos2 = persistent_property("closed_pos2",19.7) # deg
    dt = persistent_property("dt",0.008) # total operation time in s

    def PVT(self,Topen):
        """list of times and positions for a pulse sequence given by t
        T: opening times in seconds"""
        from numpy import array
        dt = self.dt
        closed_pos,open_pos,closed_pos2 = \
            self.closed_pos,self.open_pos,self.closed_pos2
        top_speed = 2*(self.closed_pos2-self.closed_pos)/self.dt
        P,V,T = [],[],[]
        for i,t in enumerate(Topen):
            if i%2 == 0: P += [closed_pos,open_pos,closed_pos2]
            else: P += [closed_pos2,open_pos,closed_pos]
            if i%2 == 0: V += [0,top_speed,0]
            else: V += [0,-top_speed,0]
            T += [t-dt/2,t,t+dt/2]
        P,V,T = array([P,V,T])
        return P,V,T

ms_shutter = Ms_Shutter()


if __name__ == "__main__": # for testing
    from numpy import arange
    self = ms_shutter
    dt = 0.0244388571428
    Topen = dt*arange(0,10)
    print('P,V,T = self.PVT(Topen)')
    print('p,v = self.pv(Topen)')
