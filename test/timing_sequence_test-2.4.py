"""Friedrich Schotte, 23 Jul 2015 - 22 Sep 2015"""
__version__ = "2.4"
if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    import timing_system; timing_system.DEBUG = True
    from timing_system import *
    from numpy import *
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    dt = 1/hscf
    waitt_delay = rint(0.024/dt)*dt
    eps = 1e-6
    timepoints = round(10**arange(-9,-1+eps,0.25),3)
    laser_modes = [0,1] # [0,1] = off/on
    delays = array([x for x in timepoints for l in laser_modes])
    waitt_delays = maximum(ceil(delays/dt)*dt,waitt_delay)
    laser_on = laser_modes*len(timepoints)
    xray_on = [1]*len(laser_modes)*len(timepoints)
    
    variables,value_lists = [],[]
    variables += [timing_system.ps_lxd];   value_lists += [delays]
    variables += [timing_system.waitt];    value_lists += [waitt_delays]
    variables += [timing_system.pst_on];   value_lists += [laser_on]
    variables += [timing_system.xosct_on]; value_lists += [xray_on]
    variables += [timing_system.losct_on]; value_lists += [xray_on]
    variables += [timing_system.ms_on];    value_lists += [xray_on]
    ##for l in value_lists: l += [0] # After last image, turn everything off.
    dependencies = [],[]
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
