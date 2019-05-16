Ensemble.command = 'import Ensemble; Ensemble.run_server()'
WideFieldCamera.command = 'import GigE_camera_server; GigE_camera_server.run("WideFieldCamera")'
names = ['Ensemble', 'WideFieldCamera', 'Server']
Server.command = u'import GigE_camera_server; GigE_camera_server.run("MicroscopeCamera")'
Microscope Camera.command = u'import GigE_camera_server; GigE_camera_server.run("MicroscopeCamera")'
N = 16
1.label = u'Ensemble'
1.command = u'import Ensemble; Ensemble.run_server()'
2.label = u'WideField Camera'
2.command = u'import GigE_camera_server; GigE_camera_server.run("WideFieldCamera")'
3.command = u'import GigE_camera_server; GigE_camera_server.run("MicroscopeCamera")'
3.label = u'Microscope Camera'
4.label = 'Lightwave Temperature Controller DL'
4.command = u'from temperature_controller_server import *;  temperature_controller_IOC.run()'
5.label = u'Centris Syringe IOC'
5.command = u'from cavro_centris_syringe_pump_IOC import *; syringe_pump_IOC.run()'
1.logfile_basename = u'Ensemble_IOC'
2.logfile_basename = u'WideFieldCamera_server'
3.logfile_basename = u'MicroscopeCamera_server'
4.logfile_basename = u'temperature_controller_IOC'
5.logfile_basename = u'cavro_centris_syringe_pump_IOC'
1.value_code = u'ensemble.connected'
2.value_code = u'widefield_camera.state'
3.value_code = u'microscope_camera.state'
3.test_code = u'"offline" not in value'
2.test_code = u'"offline" not in value'
4.value_code = u'caget("NIH:TEMP.VAL")'
4.test_code = u'value is not None and not isnan(value)'
1.test_code = u'value==1'
1.format_code = u'{0:"Device offline",1:"Online",nan:"IOC offline"}[value]'
4.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
5.value_code = u'volume[0].value'
5.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
5.test_code = u'not isnan(value)'
6.label = u'Lab Microscope'
6.command = u'import GigE_camera_server; GigE_camera_server.run("Microscope")'
6.logfile_basename = u'Microscope_server'
6.value_code = u'Camera("Microscope").state'
6.test_code = u'value and "offline" not in value'
7.label = u'Microfluidics Camera'
7.command = u'import GigE_camera_server; GigE_camera_server.run("MicrofluidicsCamera")'
7.logfile_basename = u'MicrofluidicsCamera_server'
7.value_code = u'Camera("MicrofluidicsCamera").state'
7.test_code = u'"offline" not in value'
8.label = u'Ramsey RF Generator'
8.command = u'from Ramsey_RF_generator import *; Ramsey_RF_IOC.run()'
8.value_code = u'caget("NIH:RF.VAL")'
8.logfile_basename = u'temperature_controller_IOC'
8.test_code = u'value is not None and not isnan(value)'
8.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
9.label = u'Test Bench Camera'
9.command = u'import GigE_camera_server; GigE_camera_server.run("TestBenchCamera")'
9.logfile_basename = u'TestBenchCamera_server'
9.value_code = u'Camera("TestBenchCamera").state'
9.test_code = u'"offline" not in value'
9.format_code = u'value'
6.format_code = u'value'
7.format_code = u'value'
10.label = 'Oasis Chiller DL'
10.command = u'from oasis_chiller import *;  oasis_chiller_IOC.run()'
10.logfile_basename = u'oasis_chiller_IOC'
10.value_code = u'caget("NIH:CHILLER.RBV")'
10.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
10.test_code = u'value is not None and not isnan(value)'
11.label = u'Oasis Chiller Auto-tune'
11.command = u'from oasis_chiller_autotune import *; run()'
11.logfile_basename = u'oasis_chiller_autotune'
11.value_code = u'caget("NIH:CHILLER.AUTOTUNE")'
11.format_code = u'"Not active" if value is None else "Active"'
12.label = u'Sample Frozen Optical'
12.command = 'from sample_frozen_optical import *; sample_frozen_optical.run()'
12.logfile_basename = 'sample_frozen_optical'
12.value_code = '\'intervention = %r, enabled = %r\' %(caget("NIH:SAMPLE_FROZEN_OPTICAL2.VAL"),caget("NIH:SAMPLE_FROZEN_OPTICAL2.ENABLED"))'
12.test_code = 'len(value) < 32'
12.format_code = '"Server offline" if value is None else str(value)'
13.label = u'Hamilton Syringe Pump'
13.command = u'from syringe_pump import *; run_server()'
13.logfile_basename = u'syringe_pump'
13.value_code = u'caget("NIH:syringe_pump.V")'
11.test_code = u'value is not None'
13.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
13.test_code = u'value is not None and not isnan(value)'
14.label = u'Thermocouple IOC'
14.command = u'from omega_thermocouple import *; run_IOC()'
14.logfile_basename = u'omega_thermocouple'
14.value_code = u'caget("NIH:TC.VAL")'
14.test_code = u'value is not None and not isnan(value)'
14.format_code = u'"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
15.command = 'from temperature_Friedrich import temperature_server; temperature_server.run()'
15.label = 'Temperature SL (Prototype, Friedrich)'
15.logfile_basename = 'temperature'
15.value_code = 'caget("NIH:TEMPERATURE.VAL")'
15.format_code = '"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
15.test_code = 'value is not None and not isnan(value)'
16.command = 'from temperature_server_IOC import temperature_server_IOC; temperature_server_IOC.run();'
16.logfile_basename = 'temperature_server_IOC'
16.label = 'Temperature SL (Valentyn)'
16.value_code = 'caget("NIH:TRAMP.VAL")'
16.format_code = '"IOC offline" if value is None else "Device offline" if isnan(value) else "Online"'
16.test_code = 'value is not None and not isnan(value)'