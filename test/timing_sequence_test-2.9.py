"""Friedrich Schotte, 23 Jul 2015 - 29 Sep 2015"""
__version__ = "2.9"

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True
    from timing_system import *
    from numpy import *
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    dt = 1/hscf
    eps = 1e-6

    timepoints = round(10**arange(-9,-1+eps,0.25),3)
    laser_modes = [1] # [0,1] = off/on
    nrepeat = 5 # pulses per image
    waitt_delay = rint(0.2/dt)*dt
    
    delays = array([x for x in timepoints for l in laser_modes])
    waitt_delays = maximum(ceil(delays/dt)*dt,waitt_delay)
    laser_on = laser_modes*len(timepoints)
    always = [1]*len(laser_modes)*len(timepoints)
    nrepeats = [nrepeat]*len(laser_modes)*len(timepoints)
    
    variables,value_lists = [],[]
    variables += [timing_system.ps_lxd];   value_lists += [delays]
    variables += [timing_system.waitt];    value_lists += [waitt_delays]
    variables += [timing_system.npulses];  value_lists += [nrepeats]
    variables += [timing_system.pst.on];   value_lists += [laser_on]
    variables += [timing_system.xosct.on]; value_lists += [always]
    variables += [timing_system.losct.on]; value_lists += [always]
    variables += [timing_system.ms.on];    value_lists += [always]
    dependencies = [],[]
    ##for l in value_lists: l += [0] # After last image, turn everything off.
    ##data = sequencer_stream(variables,value_lists)
    values = [l[0] for l in value_lists]

    ##print 'timing_system.xosct.offset = -6.82e-06'
    print 'set_sequence(variables,value_lists)'
    print 'packets,names = sequencer_packets(variables,value_lists)'
    print 'timing_sequencer.set_sequence(variables,value_lists,1,name="collection")'
    print 'timing_sequencer.add_sequence(variables,value_lists,1,name="collection")'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
    self = timing_sequencer
