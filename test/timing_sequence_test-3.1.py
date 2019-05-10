"""Friedrich Schotte, 23 Jul 2015 - 29 Sep 2015"""
__version__ = "3.0"

def set_vars(timepoint,laser_mode=None,nrepeat=None,waitt_delay=None):
    """
    timepoint: delay in seconds
    laser_modes: 0 = off, 1 = on
    nrepeat: laser/xray pulses per image
    waitt_delay: laser/xray repetition period
    """
    if laser_mode is not None:  timing_system.pst.on.value = laser_mode
    if nrepeat is not None:     timing_system.npulses.value = nrepeat
    if waitt_delay is not None: timing_system.waitt.value = waitt_delay
    # Make sure the repetition rate is low enough for the time delay.
    dt = timing_system.waitt.stepsize
    timing_system.waitt.value = max(ceil(timepoint/dt)*dt,timing_system.waitt.value)
    
    variables,value_lists = [],[]
    variables += [timing_system.ps_lxd];   value_lists += [[timepoint]]
    variables += [timing_system.waitt];    value_lists += [[timing_system.waitt.value]]
    variables += [timing_system.npulses];  value_lists += [[timing_system.npulses.value]]
    variables += [timing_system.pst.on];   value_lists += [[timing_system.pst.on.value]]
    variables += [timing_system.xosct.on]; value_lists += [[1]]
    variables += [timing_system.losct.on]; value_lists += [[1]]
    variables += [timing_system.ms.on];    value_lists += [[1]]
    variables += [timing_system.xdet.on];  value_lists += [[1]]

    set_sequence(variables,value_lists,repeat_counts=[10])

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ##import timing_system; timing_system.DEBUG = True
    from timing_system import *
    from numpy import *
    print 'timing_system.ip_address = %r' % timing_system.ip_address

    timepoint,laser_mode,nrepeat,waitt_delay = 0,1,5,0.2
    print 'set_vars(0,1,5,0.2)'
    print 'set_sequence(variables,value_lists,repeat_counts=[10])'
    print 'packets,names = sequencer_packets(variables,value_lists)'
    print 'timing_sequencer.set_sequence(variables,value_lists,1,name="collection")'
    print 'timing_sequencer.add_sequence(variables,value_lists,1,name="collection")'
    print 'timing_sequencer.enabled'
    print 'timing_sequencer.running'
    print 'timing_sequencer.queue'
    print 'timing_sequencer.clear_queue()'
    print 'timing_sequencer.abort()'
    self = timing_sequencer
