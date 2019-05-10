title = 'Delay Configuration'
motor_labels = ['list of delays']
names = ['delay']
motor_names = ['collect.delay']
line0.description = 'NIH:H-1_ps'
line1.description = 'NIH:H-56_ps'
line0.collect.delay = 'hsc=H-1, pp=Flythru-4, seq=NIH:i5c1, delays=pairs(-10us, lin_series(-100ps, 75ps, 25ps)+sorted(log_series(100ps, 1us, steps_per_decade=4)+[75ns, 133ns]))'
line1.collect.delay = 'hsc=H-56, pp=Flythru-4, seq=NIH:i1, delays=pairs(-10us, [-10.1us]+log_series(316ns, 17.8ms, steps_per_decade=4))'
line0.updated = '09 Oct 14:06'
line1.updated = '09 Oct 14:07'
widths = [500]
row_height = 54
description_width = 140
nrows = 9
line2.collect.delay = 'hsc=H-1, pp=Flythru-48, seq=NIH:i5c1, delays=pairs(-10us,[-10.1us, -2.8ns,0, 2.8ns]+sort(log_series(5.6ns, 1us, steps_per_decade=4)+[75ns, 133ns]))'
line3.collect.delay = 'hsc=H-56, pp=Flythru-48, seq=NIH:i1, delays=pairs(-10us, [-10.1us]+log_series(316ns, 178ms, steps_per_decade=4))'
line2.description = 'NIH:H-1_ns'
line5.collect.delay = 'hsc=H-56, pp=Flythru-48, seq=NIH:i1, delays=[pairs(-10us, log_series(10ms, 178ms, steps_per_decade=4)]'
line4.collect.delay = u''
line7.collect.delay = u'delays=[[(pp=Period-48, enable=010)]*5, (image=0, pp=Period-144, enable=100), (264+1*144, enable=101), [(image=0, enable=100)]*2, (264+4*144, enable=101), (image=0, enable=100)*4, (264+9*144, enable=101), (image=0, enable=100)*8, (264+18*144, enable=101), (image=0, enable=100)*16, (264+35*144, enable=101), (image=0, enable=100)*32, (264+68*144, enable=101)]'
line6.collect.delay = u'hsc=H-56, pp=Flythru-4, seq=NIH:i1, delays=[-10us, -10us, (264, enable=101, circulate=0), 528, 792, 1056, (-10us, enable=111, circulate=1), -10us]'
line3.description = 'NIH:H-56_ns'
line4.description = 'NIH:S-11'
line5.description = 'NIH:H-56_LT'
line6.description = 'NIH:H-56_Exotic_ps'
line7.description = 'BioCARS:TR-LT'
line2.updated = '09 Oct 20:20'
line6.updated = '09 Oct 20:30'
line7.updated = '09 Oct 20:30'
line5.updated = '09 Oct 20:30'
line3.updated = '09 Oct 20:21'
command_row = 8
show_apply_buttons = True
apply_button_label = 'Select'
define_button_label = 'Update'
show_define_buttons = False
show_stop_button = False
line8.description = 'None'
line8.updated = '23 Oct 19:24'
line8.collect.delay = ' '