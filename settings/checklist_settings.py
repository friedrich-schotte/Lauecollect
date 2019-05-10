1.code = 'float(value) > 10'
1.enabled = False
1.format = u'"%.3f mA" % value'
1.label = 'Storage ring'
1.value = 'caget("S:SRcurrentAI.VAL")'
2.code = 'float(value) < 10.75'
2.enabled = False
2.format = '"%.3f mm" % value'
2.label = 'Insertion device U23'
2.value = 'caget("ID14ds:Gap.VAL")'
3.code = u'15.84 < float(value) < 15.86'
3.enabled = False
3.format = u'"%.3f mm" % value'
3.label = u'Insertion device U27'
3.value = u'caget("ID14us:Gap.VAL")'
4.code = 'int(value)'
4.enabled = False
4.format = '{0:"CLOSED",1:"OPEN"}[value]'
4.label = 'Frontend shutter 14IDA'
4.value = 'caget("PA:14ID:STA_A_FES_OPEN_PL.VAL")'
5.code = 'int(value)'
5.enabled = False
5.format = '{0:"CLOSED",1:"OPEN"}[value]'
5.label = 'Station shutter 14IDC'
5.value = 'caget("PA:14ID:STA_B_SCS_OPEN_PL.VAL")'
6.code = '-8e-6 < value < +8e-6'
6.enabled = False
6.format = '"%+.3f us" % (value/1e-6)'
6.label = 'Heatload chopper phase error'
6.value = u'timing_system.hlcad.value - timing_system.hlcnd.value'
7.code = 'value == 1'
7.enabled = False
7.format = '{0:"off",1:"green",2:"red",3:"orange"}[value]'
7.label = 'Heatload chopper FPGA status LED'
7.value = 'timing_system.hlcled.count'
8.code = u'int(value) == 0'
8.enabled = False
8.format = u'{1:"Closed",0:"Open"}[value]'
8.label = u'Laser Safety Shutter'
8.value = u'caget("14IDB:B1Bi0.VAL")'
9.enabled = False
9.format = u'"Online" if value else "Offline"'
9.label = u'Timing System'
9.value = u'timing_system.online'
10.label = u'Lok-to-Clock'
10.enabled = False
10.code = u'int(value)'
10.format = u'"Unlocked" if value==0 else "Locked" if value==1 else "Offline"'
10.value = u'LokToClock.locked'
11.code = 'int(value) == 0'
11.enabled = False
11.format = u'"OK" if value==0 else "Fault" if value==1 else "unknown"'
11.label = 'Ensemble status'
11.value = 'ensemble.fault'
12.code = u'value == "SAXS-WAXS_PVT.ab"'
12.enabled = False
12.format = u'value if value else "Not running"'
12.label = u'SAXS/WAXS Ensemble program'
12.value = u'ensemble.program_filename'
13.value = u'ensemble.program_filename'
13.label = u'Laue Ensemble program'
13.code = u'value in ["ms-shutter.ab","PVT_Fly-thru.ab"]'
13.format = u'value'
13.enabled = False
14.enabled = False
14.format = u'"Online" if value else "Offline"'
14.label = u'X-ray detector'
14.value = u'xray_detector.online'
15.label = u'Sample frozen?'
15.value = u'sample_frozen.diffraction_spots'
15.format = u'"%s spots" % value'
15.enabled = False
15.code = u'value < 20'
N = 16
16.label = u'Freeze intervention'
16.value = u'freeze_intervention.active'
16.format = u'"Active" if value else "Not active"'
16.code = u'value == False'
16.enabled = True