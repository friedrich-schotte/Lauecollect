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

    timepoints = round(10**arange(-9,-3+1e-6,0.25),3)
    laser_modes = [0,1]
    delays = array([x for x in timepoints for l in laser_modes])
    laser_on = laser_modes*len(timepoints)
    xray_on = [1]*2*len(timepoints)
    modes =  [Ensemble_SAXS.delay_mode(d) for d in delays]
    waitts = [Ensemble_SAXS.delay_waitt(d) for d in delays]
    pst_delay_count = rint(delays/(0.5/bcf))
    N = len(delays)
    n = 1000
    xray_on_2 = zeros((N*n),int); xray_on_2[0:-1:n] = xray_on
    laser_on_2 = zeros((N*n),int); laser_on_2[0:-1:n] = laser_on
    pst_delay_count_2 = zeros((N*n),int); pst_delay_count_2[0:-1:n] = pst_delay_count
    
    variables,value_lists = [],[]
    variables += [timing_system.xosct_enable]; value_lists += [xray_on_2]
    variables += [timing_system.pst_enable]; value_lists += [laser_on_2]
    variables += [timing_system.pst_delay]; value_lists += [pst_delay_count_2]
    for l in value_lists: l += [0] # After last image, turn everything off. 
    data = sequencer_stream(variables,value_lists)
        
    print 'timing_sequencer.set_sequence(variables,value_lists,1)'
    print 'timing_sequencer.add_sequence(variables,value_lists,1)'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
    print 'timing_system.xosct_enable.count = 0'
