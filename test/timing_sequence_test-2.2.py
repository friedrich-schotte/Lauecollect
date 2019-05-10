__version__ = "2.2"
if __name__ == "__main__":
    from pdb import pm # for debugging
    from timing_system import *
    from numpy import *
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    waitt_delay = 0.1 # seconds
    waitt_delay = rint(waitt_delay*hscf)/hscf
    eps = 1e-6
    timepoints = round(10**arange(-9,-2+eps,0.25),3)
    laser_modes = [1] # [0,1] = off/on
    delays = array([x for x in timepoints for l in laser_modes])
    laser_on = laser_modes*len(timepoints)
    xray_on = [1]*len(laser_modes)*len(timepoints)

    N = len(delays)
    n = rint(waitt_delay*hscf)
    hsc_delay = -hscd.offset # assume hscd.value ~ 0 (with small adjustments)
    margin = 1/hscf - hsc_delay
    xosct_delay = waitt_delay - margin # X-ray timing determined by high-speed chopper
    xosct_delays = array([xosct_delay]*len(laser_modes)*len(timepoints))
    pst_delays = xosct_delays-delays
    
    variables,value_lists = [],[]
    variables += [timing_system.xosct]; value_lists += [xosct_delays]
    variables += [timing_system.pst];   value_lists += [pst_delays]
    ##for l in value_lists: l += [0] # After last image, turn everything off.
    dependencies = [[timing_system.waitt],[waitt_delay]]
    ##data = sequencer_stream(variables,value_lists,dependencies)

    print 'timing_system.xosct.offset = -6.82e-06'
    print 'timing_sequencer.set_sequence(variables,value_lists,1,dependencies)'
    print 'timing_sequencer.add_sequence(variables,value_lists,1,dependencies)'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
    print 'timing_system.xosct_enable.count = 0'
