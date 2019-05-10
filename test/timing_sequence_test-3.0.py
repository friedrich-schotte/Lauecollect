"""Friedrich Schotte, 23 Jul 2015 - 29 Sep 2015"""
__version__ = "3.0"

def set_vars(timepoint,laser_mode,nrepeat,waitt_delay):
    """
    timepoint: delay in seconds
    laser_modes: 0 = off, 1 = on
    nrepeat: laser/xray pulses per image
    waitt_delay: laser/xray repetition period
    """
    dt = 1/hscf
    waitt_delay = max(ceil(timepoint/dt)*dt,rint(waitt_delay/dt)*dt)
    
    variables,value_lists = [],[]
    variables += [timing_system.ps_lxd];   value_lists += [[timepoint]]
    variables += [timing_system.waitt];    value_lists += [[waitt_delay]]
    variables += [timing_system.npulses];  value_lists += [[nrepeat]]
    variables += [timing_system.pst.on];   value_lists += [[laser_mode]]
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
