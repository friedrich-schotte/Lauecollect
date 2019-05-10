__version__ = "2.0.1"
if __name__ == "__main__":
    from pdb import pm # for debugging
    from timing_system import *
    from Ensemble_SAXS import Ensemble_SAXS
    from numpy import arange,vectorize
    from time import time # for timing
    from numpy import *
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    waitt = 2.0 # seconds
    waitt = rint(waitt*hscf)/hscf
    eps = 1e-6
    timepoints = round(10**arange(-9,-2+eps,0.25),3)
    laser_modes = [1] # [0,1] = off/on
    delays = array([x for x in timepoints for l in laser_modes])
    laser_on = laser_modes*len(timepoints)
    xray_on = [1]*len(laser_modes)*len(timepoints)
    N = len(delays)
    n = rint(waitt*hscf)
    hsc_delay = -hscd.offset # assume hscd.value ~ 0 (with small adjustments)
    margin = 1/hscf - hsc_delay
    xosct_delay = waitt - margin # # X-ray timing determined by high-speed chopper
    xosct_delays = array([xosct_delay]*len(laser_modes)*len(timepoints))
    pst_delays = xosct_delays-delays
    xosct_fine_delays = xosct_delays % (1/hscf)
    xosct_coarse_delays = floor(xosct_delays / (1/hscf)).astype(int)
    pst_fine_delays = pst_delays % (1/hscf)
    pst_coarse_delays = floor(pst_delays / (1/hscf)).astype(int)
    
    xosct_delay_count = rint(xosct_fine_delays/(0.5/bcf)).astype(int)
    pst_delay_count = rint(pst_fine_delays/(0.5/bcf)).astype(int)
    xosct_coarse_delays += arange(0,N)*n
    pst_coarse_delays += arange(0,N)*n

    xosct_enable = zeros((N*n),int); xosct_enable[xosct_coarse_delays] = 1
    pst_enable = zeros((N*n),int);   pst_enable[pst_coarse_delays] = laser_on

    xosct_delay_counts = repeat(xosct_delay_count,n)
    pst_delay_counts   = repeat(pst_delay_count,n)
    
    variables,value_lists = [],[]
    variables += [timing_system.xosct_enable]; value_lists += [xosct_enable]
    variables += [timing_system.xosct_delay];  value_lists += [xosct_delay_counts]
    variables += [timing_system.pst_enable];   value_lists += [pst_enable]
    variables += [timing_system.pst_delay];    value_lists += [pst_delay_counts]
    for l in value_lists: l += [0] # After last image, turn everything off. 
    data = sequencer_stream(variables,value_lists)
        
    print 'timing_sequencer.set_sequence(variables,value_lists,100)'
    print 'timing_sequencer.add_sequence(variables,value_lists,100)'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
    print 'timing_system.xosct_enable.count = 0'
