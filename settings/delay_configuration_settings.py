title = 'Delay Configuration'
motor_labels = ['list of delays']
names = ['delay_configuration']
motor_names = ['collect.delay_configuration']
line0.description = 'NIH:H-1_ps'
line1.description = 'NIH:H-56_ps'
line0.collect.delay_configuration = 'delays=pairs(-10us, lin_series(-100ps, 75ps, 25ps)+sorted(log_series(100ps, 1us, steps_per_decade=4)+[75ns, 133ns]))'
line1.collect.delay_configuration = 'hsc=CH-56, pp=Flythru-48, seq=NIH:i1, delays=pairs(-10us, [-10.1us]+log_series(316ns, 178ms, steps_per_decade=4))'
line0.updated = '28 Jan 09:48'
line1.updated = '09 Oct 14:07'
widths = [500]
row_height = 40
description_width = 140
nrows = 18
line2.collect.delay_configuration = 'delays=pairs(-10us, sorted(log_series(10ns, 563ns, steps_per_decade=4)+[75ns, 133ns]))'
line3.collect.delay_configuration = 'delays=pairs(-10us, [-10.1us]+log_series(316ns, 178ms, steps_per_decade=4))'
line2.description = 'NIH:H-1_ns'
line5.collect.delay_configuration = 'hsc=H-56, pp=Flythru-48, seq=NIH:i1, delays=pairs(-10us, log_series(10ms, 178ms, steps_per_decade=4))'
line4.collect.delay_configuration = 'delays=log_series(1ms, 75ms, steps_per_decade=4)'
line7.collect.delay_configuration = u'delays=[[(pp=Period-48, enable=010)]*5, (image=0, pp=Period-144, enable=100), (264+1*144, enable=101), [(image=0, enable=100)]*2, (264+4*144, enable=101), (image=0, enable=100)*4, (264+9*144, enable=101), (image=0, enable=100)*8, (264+18*144, enable=101), (image=0, enable=100)*16, (264+35*144, enable=101), (image=0, enable=100)*32, (264+68*144, enable=101)]'
line6.collect.delay_configuration = u'hsc=H-56, pp=Flythru-4, seq=NIH:i1, delays=[-10us, -10us, (264, enable=101, circulate=0), 528, 792, 1056, (-10us, enable=111, circulate=1), -10us]'
line3.description = 'NIH:H-56_ns'
line4.description = 'NIH:CW-longtime'
line5.description = 'NIH:H-56_LT'
line6.description = 'NIH:H-56_Exotic_ps'
line7.description = 'BioCARS:TR-LT'
line2.updated = '04 Nov 16:55'
line6.updated = '09 Oct 20:30'
line7.updated = '09 Oct 20:30'
line5.updated = '09 Oct 20:30'
line3.updated = '04 Nov 10:18'
command_row = 9
show_apply_buttons = True
apply_button_label = 'Select'
define_button_label = 'Update'
show_define_buttons = True
show_stop_button = False
line8.description = 'NIH:H-1-ps-56-sb'
line8.updated = '23 Oct 19:24'
line8.collect.delay_configuration = 'hsc=CH-1, seq=NIH:i1, delays=pairs(-10us, lin_series(-100ps, 75ps, 25ps)+sorted(log_series(100ps, 10us, steps_per_decade=4)+[75ns, 133ns])), hsc=CH-56, delays=pairs(-10us,log_series(10us, 178ms, steps_per_decade=4))'
line9.description = 'NIH:single_timepoint'
line9.collect.delay_configuration = 'delays=[-10us, 10us]'
line10.description = 'NIH:H-56_-10us'
line10.collect.delay_configuration = 'delays = [-10us]'
line11.collect.delay_configuration = 'delays=[(delay=-10us,circulate=1), -10us, -10us, (delay=-10us,laser=1), 264, 2*264,3*264,4*264,5*264,6*264,7*264,8*264]'
line11.updated = '03 Nov 13:32'
line11.description = 'NIH:TR-LT_Exotic'
line12.collect.delay_configuration = 'delays=[(-10us,image=0, enable=111,circulate=1), (-10us, image=1, enable=101,circulate=0), (264, enable=101), (2*264, enable=101),(3*264, enable=101),(4*264, enable=101),(5*264, enable=101),(6*264, enable=101),(7*264, enable=101)]'
line12.updated = '03 Nov 10:56'
line12.description = 'NIH:TR-LT_Exotic2'
line13.description = 'NIH:TR-LT_Exotic3'
line13.collect.delay_configuration = 'delays=[(-10us,circulate=1), -10us, -10us, (-10us,laser=1), 264, 2*264,3*264,4*264,5*264,6*264,7*264,8*264]'
command_rows = [17]
line14.description = 'UCSF:T-jump\t'
line14.collect.delay_configuration = 'delays=pairs(-10us, log_series(562ns, 1ms, steps_per_decade=8))'
line14.updated = '04 Nov 01:15'
line15.description = 'NIH:H-1_ns_linear'
line15.collect.delay_configuration = 'delays=pairs(-10us, lin_series(50ns, 550ns, 25ns))'
line15.updated = '2019-03-25 05:24:39'
multiple_selections = False
line16.collect.delay_configuration = 'delays=[-10.1us]+log_series(1us, 1ms, steps_per_decade=1)'
line16.updated = '2019-02-04 11:39:16'
line16.description = 'Rob test'
line17.collect.delay_configuration = 'delays=pairs(-10us, [-10.1us, 0]+log_series(562ns, 10ms, steps_per_decade=4))'
line17.updated = '2019-06-01 08:19:55'
line17.description = 'NIH:S-7'