Environment.defaults = {'Enabled': False, 'Value': 'offline?'}
Environment.properties = {'Enabled': [(True, 'control.ensemble_online')]}
Environment.value = 'control.environment'
XRayDetector.properties = {
    'Enabled': 'True',
    'Label': '"X-Ray Detector %g mm" % control.DetZ.value',
}
XRayDetectorInserted.action = {
    False: 'control.det_retracted = True',
    True: 'control.det_inserted = True'
}
XRayDetectorInserted.defaults = {
    'Enabled': False,
    'Label': 'offline',
}
XRayDetectorInserted.properties = {
    'BackgroundColour': [
        ('green', 'control.det_inserted == True'),
        ('yellow', 'control.det_retracted == True'),
        ('red', 'control.det_inserted == control.det_retracted'),
    ],
    'Enabled': [(True, 'control.det_inserted in [True,False]')],
    'Value': [
        (True, 'control.det_inserted == True'),
        (False, 'control.det_retracted == True'),
    ],
    'Label': [
        ('Cancel', 'control.det_moving == True'),
        ('Retract', 'control.det_inserted == True'),
        ('Insert', 'control.det_inserted == False'),
    ],
}
ProgramRunning.action = {
    False: 'control.ensemble_program_running = False',
    True: 'control.ensemble_program_running = True',
}
ProgramRunning.defaults = {'Enabled': False, 'Label': 'offline'}
ProgramRunning.properties = {
    'BackgroundColour': [
        ('green', 'control.ensemble_program_running == True'),
        ('red', 'control.ensemble_program_running == False')],
    'Enabled': [(False, 'control.fault == True'),
                (True, 'control.fault == False')],
    'Value': [(False, 'control.ensemble_program_running == False'),
              (True, 'control.ensemble_program_running == True')],
    'Label': [
        ('Fault', 'control.fault == True'),
        ('Start', 'control.ensemble_program_running == False'),
        ('Stop', 'control.ensemble_program_running == True')]
}
GotoSaved.action = {True: 'control.inserted = True'}
GotoSaved.defaults = {'Enabled': False}
GotoSaved.properties = {
    'BackgroundColour': [('red', 'control.XY_enabled == False')],
    'Enabled': [(True, '1-control.inserted')]}
Home.action = {
    False: 'control.ensemble_homing = True',
    True: 'control.ensemble_homing = True'}
Home.defaults = {'Enabled': False, 'Label': 'Home'}
Home.properties = {
    'BackgroundColour': [
        ('yellow', 'control.ensemble_homing == True'),
        ('green', 'control.ensemble_homed == True'),
        ('red', 'control.ensemble_homed == False')],
    'Enabled': [
        (False, "control.ensemble_homing_prohibited != ''"),
        (True, "control.ensemble_homing_prohibited == ''")],
    'Value': [
        (False, 'control.ensemble_homed == False'),
        (True, 'control.ensemble_homed == True')],
    'Label': [
        ('Cancel', 'control.ensemble_homing == True'),
        ('Home', 'control.ensemble_homed == False'),
        ('Home', 'control.ensemble_homed == True')]
}
Inserted.action = {
    False: 'control.retracted = True',
    True: 'control.inserted = True',
}
Inserted.defaults = {
    'Enabled': True,
    'Label': 'Inserted [Withdrawn]'
}
Inserted.properties = {
    'BackgroundColour': [
        ('grey80', 'control.moving_sample == True'),
        ('green', 'control.inserted == True'),
        ('yellow', 'control.retracted == True'),
        ('red', 'control.inserted == control.retracted'),
    ],
    'Enabled': [
        (True, 'control.XY_enabled and not control.moving_sample'),
        (False, 'not control.ensemble_online'),
    ],
    'Value': [
        (True, 'control.inserted == True'),
        (False, 'control.retracted == True'),
    ],
    'Label': [
        ('Cancel', 'control.inserting_sample == True'),
        ('Cancel', 'control.retracting_sample == True'),
        ('Retract', 'control.inserted == True'),
        ('Insert', 'control.inserted == False'),
    ],
}
Temperature_Setpoint.defaults = {'Enabled': False, 'Value': 'offline'}
Temperature_Setpoint.type = 'float'
Temperature_Setpoint.format = '%.1f'
Temperature_Setpoint.unit = 'C'
Temperature_Setpoint.properties = {'Enabled': [(True, 'control.temperature_online')]}
Temperature_Setpoint.value = 'control.temperature_setpoint'
Temperature.defaults = {'Enabled': False, 'Value': 'offline'}
Temperature.type = 'float'
Temperature.format = '%.3f'
Temperature.unit = 'C'
Temperature.properties = {'Enabled': [(True, 'control.temperature_online')]}
Temperature.value = 'control.temperature'
XRayShutter.defaults = {'Enabled': False, 'Label': 'offline'}
XRayShutter.properties = {
    'Enabled': 'control.xray_safety_shutters_enabled == True',
    'Value': 'control.xray_safety_shutters_open == True',
    'Label': [
        ('Disabled', 'control.xray_safety_shutters_enabled == False'),
        ('Close','control.xray_safety_shutters_open == True'),
        ('Open', 'control.xray_safety_shutters_open == False'),
    ],
    'BackgroundColour': [
        ('green', 'control.xray_safety_shutters_open'),
        ('red',   'not control.xray_safety_shutters_open and control.xray_safety_shutters_enabled'),
    ],
}
XRayShutter.action = {
    False: 'control.xray_safety_shutters_open = False',
    True: 'control.xray_safety_shutters_open = True',
}
XRayShutterAutoOpen.defaults = {'Enabled': False}
XRayShutterAutoOpen.properties = {
    'Enabled': 'control.xray_safety_shutters_auto_open in [True,False]',
    'Value': 'control.xray_safety_shutters_auto_open == True',
}
XRayShutterAutoOpen.action = {
    False: 'control.xray_safety_shutters_auto_open = False',
    True: 'control.xray_safety_shutters_auto_open = True',
}
LaserShutter.defaults = {'Enabled': False, 'Label': 'offline'}
LaserShutter.properties = {
    'Enabled': 'control.laser_safety_shutter_open in [True,False]',
    'Value': 'control.laser_safety_shutter_open == True',
    'Label': [
        ('Close','control.laser_safety_shutter_open == True'),
        ('Open', 'control.laser_safety_shutter_open == False'),
    ],
    'BackgroundColour': [
        ('green', 'control.laser_safety_shutter_open == True'),
        ('red',   'control.laser_safety_shutter_open == False'),
    ],
}
LaserShutter.action = {
    False: 'control.laser_safety_shutter_open = False',
    True:  'control.laser_safety_shutter_open = True',
}
LaserShutterAutoOpen.defaults = {'Enabled': False}
LaserShutterAutoOpen.properties = {
    'Enabled': 'control.laser_safety_shutter_auto_open in [True,False]',
    'Value': 'control.laser_safety_shutter_auto_open == True',
}
LaserShutterAutoOpen.action = {
    False: 'control.laser_safety_shutter_auto_open = False',
    True:  'control.laser_safety_shutter_auto_open = True',
}
Mode.defaults = {'Enabled': False, 'Value': 'offline'}
Mode.properties = {'Enabled': [(True, 'control.timing_system_online == True')]}
Mode.value = 'control.mode'
PumpEnabled.action = {
      False: 'control.pump_on_command = False',
      True: 'control.pump_on_command = True'
}
PumpEnabled.defaults = {'Enabled': False, 'Label': 'offline'}
PumpEnabled.properties = {
    'Enabled': [(True, 'control.timing_system_running == True')],
    'Value': [
        (False, 'control.pump_on_command == False'),
        (True, 'control.pump_on_command == True')],
    'Label': [
        ('running', 'control.pump_on == True'),
        ('stopped', 'control.pump_on == False'),
        ('offline', 'control.pump_on not in [True,False]'),
    ]
}
LoadSample.action = {
    False: 'control.sample_loading = False',
    True: 'control.sample_loading = True'
}
LoadSample.defaults = {'Enabled': False}
LoadSample.properties = {
    'BackgroundColour': [
        ('yellow', 'control.sample_loading'),
        ('red', 'control.pump_enabled == False')],
    'Enabled': [
        (True, 'control.pump_movable or control.sample_loading')],
    'Value': [(True, 'control.sample_loading == True')],
    'Label': [('Load Sample', 'not control.sample_loading'),
              ('Cancel Load', 'control.sample_loading')]
}
LoadSampleStep.value = 'control.load_step'
LoadSampleStep.properties = {'Enabled': 'True'}
ExtractSample.action = {
    False: 'control.sample_extracting = False',
    True: 'control.sample_extracting = True',
}
ExtractSample.defaults = {'Enabled': False}
ExtractSample.properties = {
    'BackgroundColour': [
        ('yellow', 'control.sample_extracting == True'),
        ('red', 'control.pump_enabled == False')
    ],
    'Enabled': [(True, 'control.pump_movable or control.sample_extracting')],
    'Value': [(True, 'control.sample_extracting == True')],
    'Label': [
        ('Extract Sample', 'not control.sample_extracting'),
        ('Cancel Extract', 'control.sample_extracting')
    ]
}
ExtractSampleStep.value = 'control.extract_step'
ExtractSampleStep.properties = {'Enabled': 'True'}
CirculateSample.action = {
    False: 'control.sample_circulating = False',
    True: 'control.sample_circulating = True'
}
CirculateSample.defaults = {'Enabled': False}
CirculateSample.properties = {
    'BackgroundColour': [
        ('yellow', 'control.sample_circulating'),
        ('red', 'control.pump_enabled == False')
    ],
    'Enabled': [(True, 'control.pump_movable or control.sample_circulating')],
    'Value': [(True, 'control.sample_circulating == True')],
    'Label': [
        ('Circulate Sample', 'not control.sample_circulating'),
        ('Cancel Circulate', 'control.sample_circulating')
    ],
}
CirculateSampleStep.value = 'control.circulate_step'
CirculateSampleStep.properties = {'Enabled': 'True'}
PumpHomed.action = {
    False: 'control.pump_homed = True',
    True: 'control.pump_homed = True',
}
PumpHomed.defaults = {'Enabled': False, 'Label': 'offline', 'Value': True}
PumpHomed.properties = {
    'Enabled': [
        (True, 'control.pump_movable == True')
    ],
    'Label': [
        ('Home', 'control.ensemble_online'),
    ]
}
PumpPosition.defaults = {'Enabled': False, 'Value': 'offline'}
PumpPosition.format = '%.1f'
PumpPosition.properties = {'Enabled': [(True, 'control.ensemble_online')]}
PumpPosition.value = 'control.pump_position'
PumpSpeed.defaults = {'Enabled': False, 'Value': 'offline'}
PumpSpeed.properties = {'Enabled': [(True, 'control.ensemble_online')]}
PumpSpeed.value = 'control.pump_speed'
PumpStep.defaults = {'Enabled': False, 'Value': 'offline'}
PumpStep.properties = {'Enabled': [(True, 'control.ensemble_online')]}
PumpStep.value = 'control.pump_step'
Save.action = {True: 'control.at_inserted_position = True'}
Save.defaults = {'Enabled': False}
Save.properties = {
    'Enabled': [(True, 'control.at_inserted_position == False')]
}
