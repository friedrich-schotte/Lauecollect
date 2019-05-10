1.code = u'value > 10'
1.enabled = True
1.format = u'"%.1f mA" % value'
1.label = u'Storage ring'
1.value = u'caget("S:SRcurrentAI.VAL")'
2.code = u'float(value) < 10.75'
2.enabled = True
2.format = u'"%.3f mm" % value'
2.label = u'Insertion device U23'
2.value = u'caget("ID14ds:Gap.VAL")'
3.code = u'value'
3.enabled = True
3.format = u'{0:"CLOSED",1:"OPEN"}[value]'
3.label = u'Frontend shutter 14IDA'
3.value = u'caget("PA:14ID:STA_A_FES_OPEN_PL.VAL")'
4.code = u'value == 1'
4.enabled = True
4.format = u'{0:"CLOSED",1:"OPEN"}[value]'
4.label = u'Station shutter 14IDC'
4.value = u'caget("PA:14ID:STA_B_SCS_OPEN_PL.VAL")'
5.code = u'-8e-6 < value < +8e-6'
5.enabled = True
5.format = u'"%+.3f us" % (value/1e-6)'
5.label = u'Heatload chopper phase error'
5.value = u'timing_system.hlcad.value'
6.code = u'value == 1'
6.enabled = False
6.format = u'{0:"off",1:"green",2:"red",3:"orange"}[value]'
6.label = u'Heatload chopper FPGA status LED'
6.value = u'timing_system.hlcled.count'
7.code = u'value == 1'
7.enabled = True
7.format = u'"Open" if value else "Closed"'
7.label = u'Laser Shutter'
7.value = u'caget("14IDB:lshutter.VAL")'
8.code = u'value == 0'
8.enabled = True
8.format = u'"OK" if value==0 else "Fault"'
8.label = u'Ensemble status'
8.value = u'ensemble.fault'
9.code = u'value'
9.enabled = True
9.format = u'"Yes" if value else "No"'
9.label = u'Ensemble program running'
9.value = u'ensemble.program_running'
N = 9