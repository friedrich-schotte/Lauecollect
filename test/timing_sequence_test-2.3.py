"""Friedrich Schotte, 23 Jul 2015 - 22 Sep 2015"""
__version__ = "2.3"
if __name__ == "__main__":
    from pdb import pm # for debugging
    import timing_system; timing_system.DEBUG = True
    from timing_system import *
    from numpy import *
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    waitt_delay = 0.5 # seconds
    waitt_delay = rint(waitt_delay*hscf)/hscf
    eps = 1e-6
    timepoints = round(10**arange(-9,-2+eps,0.25),3)
    laser_modes = [0,1] # [0,1] = off/on
    delays = array([x for x in timepoints for l in laser_modes])
    waitt_delays = maximum(delays,waitt_delay)
    laser_on = laser_modes*len(timepoints)
    xray_on = [1]*len(laser_modes)*len(timepoints)
    
    variables,value_lists = [],[]
    variables += [timing_system.ps_lxd]; value_lists += [delays]
    ##for l in value_lists: l += [0] # After last image, turn everything off.
    dvariables,dvalue_lists = [],[]
    dvariables += [timing_system.pst_enable];dvalue_lists += [laser_on]
    dvariables += [timing_system.pswaitt];   dvalue_lists += [waitt_delays]
    dependencies = dvariables,dvalue_lists
    dependency = dvariables,zip(*dvalue_lists)[0]
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
