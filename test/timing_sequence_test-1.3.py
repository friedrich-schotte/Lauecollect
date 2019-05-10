__version__ = "1.0"
if __name__ == "__main__":
    from pdb import pm # for debugging
    from timing_system import *
    from Ensemble_SAXS import Ensemble_SAXS
    from numpy import arange,vectorize
    from time import time # for timing
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True

    @vectorize
    def round(x,n): return float(("%."+str(n)+"g") % x)

    timepoints = round(10**arange(-10,-1.75+1e-6,0.25),3)
    laser_modes = [0,1]
    delays = [x for x in timepoints for l in laser_modes]
    laser_on = laser_modes*len(timepoints)
    modes =  [Ensemble_SAXS.delay_mode(d) for d in delays]
    waitts = [Ensemble_SAXS.delay_waitt(d) for d in delays]

    N = len(delays)
    variables,value_lists = [],[]
    variables += [lxd];     value_lists += [delays]
    variables += [laseron]; value_lists += [laser_on]
    variables += [mson];    value_lists += [[1]*N]
    variables += [xdeton];  value_lists += [[1]*N]
    variables += [xoscton]; value_lists += [[1]*N]
    variables += [loscton]; value_lists += [[1]*N]
    variables += [transc_0];value_lists += [[1]*N] 
    variables += [transc_1];value_lists += [[1]*N]
    variables += [waitt];   value_lists += [waitts]
    variables += [Ensemble_SAXS];value_lists += [modes] 
    ##for l in value_lists: l += [0] # After last image, turn everything off. 
    data = sequencer_stream(variables,value_lists)
        
    print 'timing_system.ip_address = %r' % timing_system.ip_address
    print 'timing_sequencer.set_sequence(variables,value_lists,1)'
    print 'timing_sequencer.add_sequence(variables,value_lists,1)'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
