delay = 'delays=pairs(-10us, [-10.1us, 0]+log_series(562ns, 10ms, steps_per_decade=4))'
description = 'Laser Y = -4.235mm,  X-ray 40um (H) x 40um (V), Laser 1443nm, 1.10mJ'
finish_series = False
finish_series_variable = u'Delay'
basename = 'RNA-Hairpin-8BP-AU-Stem-End-1'
power = ''
temperature_wait = 1.0
temperature_idle = 22.0
temperature = 'ramp(low=20,high=24,step=0.5,hold=2,repeat=1)'
scan_points = ''
scan_return = 1.0
scan_relative = 1.0
scan_motor = ''
temperatures = '-15.35, 20.15, 89.15'
collection_order = 'Delay, Repeat=4, Temperature, Repeat=5'
cancelled = False
directory = '/net/mx340hs/data/anfinrud_1906/Data/WAXS/RNA-Hairpin/RNA-Hairpin-8BP/RNA-Hairpin-8BP-AU-Stem-End/RNA-Hairpin-8BP-AU-Stem-End-1'
diagnostics = 'ring_current, bunch_current, temperature'
logfile_basename = 'RNA-Hairpin-8BP-AU-Stem-End-1.log'
scan_origin = -1.1740000000000004
detector_configuration = 'xray_detector, xray_scope, laser_scope'