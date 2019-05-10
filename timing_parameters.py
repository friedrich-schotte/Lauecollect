"""Support module for "timing_modes" table
"""

class TimingParameters(object):
    name = "timing_modes"
    from persistent_property import persistent_property
    mode_number = persistent_property("mode_number",0)
    N = persistent_property("N",40)
    period = persistent_property("period",264)
    from numpy import inf
    min_delay = persistent_property("min_delay",-inf)
    max_delay = persistent_property("max_delay",inf)
    transd = persistent_property("transd",17)
    dt = persistent_property("dt",4)
    t0 = persistent_property("t0",100)
    z = persistent_property("z",1)
    use = persistent_property("use",True)

timing_parameters = TimingParameters()
