title = 'Sequence Configuration'
nrows = 13
row_height = 40
motor_names = ['Ensemble_SAXS.acquisition_sequence', 'Ensemble_SAXS.sequence']
names = ['acquisition', 'idle']
motor_labels = ['acquisition', 'idle']
widths = [200, 200]
description_width = 100
line0.description = 'NIH:i1'
line1.description = 'NIH:i3'
line2.description = 'NIH:i5c1'
line3.description = 'NIH:i15'
line4.description = 'NIH:i24c1'
line5.description = 'NIH:i1_no_laser'
line6.description = 'NIH:TR-SAXS'
line0.Ensemble_SAXS.acquisition_sequence = 'enable=111'
line0.Ensemble_SAXS.sequence = 'enable=110'
line0.updated = '2019-03-29 19:25:05'
line1.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*2+[111], circulate=[1]'
line1.Ensemble_SAXS.sequence = 'enable=[011]*2+[111]'
line1.updated = '2019-03-24 13:05:27'
line2.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*4+[111], circulate=[0]*4+[1]'
line2.Ensemble_SAXS.sequence = 'enable=[011]*4+[111], circulate=[0]*4+[1]'
line2.updated = '18 Oct 21:30'
line3.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*14+[111]'
line3.Ensemble_SAXS.sequence = 'enable=[011]*14+[111]'
line3.updated = '2019-02-01 02:15:34'
line4.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*23+[111], circulate=[0]*23+[1]'
line4.Ensemble_SAXS.sequence = 'enable=[011]*23+[111], circulate=[0]*23+[1]'
line4.updated = '18 Oct 21:30'
line5.Ensemble_SAXS.acquisition_sequence = 'enable=101'
line5.Ensemble_SAXS.sequence = 'enable=101'
line5.updated = '18 Oct 22:06'
line6.Ensemble_SAXS.acquisition_sequence = 'enable=101,circulate=0'
line6.Ensemble_SAXS.sequence = 'enable=100'
line6.updated = '18 Oct 22:59'
command_row = 0
show_define_buttons = True
line7.description = 'NIH:Laser_on/off'
line7.updated = '26 Oct 01:51'
line7.Ensemble_SAXS.acquisition_sequence = 'enable=111'
line7.Ensemble_SAXS.sequence = 'enable=101'
line8.description = 'NIH:i1c1w9'
line8.Ensemble_SAXS.acquisition_sequence = 'enable=[111]+[000]*9, circulate=[1]*1+[0]*9'
show_stop_button = False
line8.Ensemble_SAXS.sequence = 'enable=[111]+[000]*9, circulate=[1]*1+[0]*9'
line8.updated = '31 Oct 21:58'
line9.description = 'Rayonix start'
line9.Ensemble_SAXS.acquisition_sequence = 'circulate=[0]'
line9.Ensemble_SAXS.sequence = 'circulate=[0]'
line10.Ensemble_SAXS.acquisition_sequence = 'enable=[111]+[101]*7, circulate=[1]+[0]*7'
line10.Ensemble_SAXS.sequence = 'enable=[111]+[101]*7, circulate=[1]+[0]*7'
line10.updated = '03 Nov 01:30'
line10.description = 'NIH:e8'
command_rows = [11]
line11.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*3+[111]'
line11.updated = '2019-01-30 18:51:28'
line11.Ensemble_SAXS.sequence = 'enable=[011]*3+[111]'
line11.description = 'NIH:i4'
line12.Ensemble_SAXS.acquisition_sequence = 'enable=[011]*4+[111]'
line12.updated = '2019-03-17 00:19:42'
line12.Ensemble_SAXS.sequence = 'enable=[011]*4+[111]'
line12.description = 'NIH:i5'