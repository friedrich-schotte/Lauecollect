XRayDetectorInserted.action = {
    False: 'control.det_retracted = True',
    True: 'control.det_inserted = True'}
XRayDetectorInserted.defaults = {
    'Enabled': False, 'Label': 'Inserted [Withdrawn]'
}
XRayDetectorInserted.properties = {
    'BackgroundColour': [
        ('green', 'control.det_inserted == True'),
        ('yellow', 'control.det_retracted == True'),
        ('red', 'control.det_inserted == control.det_retracted')
    ],
    'Enabled': [(True, 'control.det_inserted in [True,False]')],
    'Value': [
        (True, 'control.det_inserted == True'),
        (False, 'control.det_retracted == True')
    ],
    'Label': [
        ('Inserted', 'control.det_inserted == True'),
        ('Retracted', 'control.det_retracted == True'),
        ('Insert', 'control.det_inserted == control.det_retracted')
    ]
}
GotoSaved.action = {True: 'control.centered = True'}
GotoSaved.defaults = {"Enabled":False}
GotoSaved.properties = {
    'Label': [
        ("Go To Saved XYZ Position","control.centered == False"),
        ("At Saved XYZ Position","control.centered == True"),
    ],
    'Enabled': 'control.centered == False and control.stage_online and not control.scanning',
    'BackgroundColour': [
        ("red","control.stage_enabled == False"),
    ],
}
Save.action = {True: 'control.define_center()'}
Save.defaults = {"Enabled":False}
Save.properties = {
    'Label': '"Save Current XYZ Position"',
    'Enabled': 'control.centered == False and control.stage_online and not control.scanning',
}
Inserted.action = {
    False: 'control.retracted = True',
    True: 'control.inserted = True',
}
Inserted.defaults = {'Label': 'Insert/Retract'}
Inserted.properties = {
    'BackgroundColour': [
        ('green', 'control.inserted == True'),
        ('yellow', 'control.retracted == True'),
    ],
    'Enabled': 'not control.scanning',
    'Value': [
        (True, 'control.inserted == True'),
        (False, 'control.retracted == True'),
    ],
    'Label': [
        ('Inserted', 'control.inserted == True'),
        ('Retracted', 'control.retracted == True'),
        ('Insert', 'control.inserted == control.retracted'),
    ]
}
StepSize.value = 'control.image_scan.stepsize'
StepSize.scale = 1000
StepSize.format = '%g'
StepSize.properties = {'Enabled':'not control.scanning'}
HorizontalRange.value = 'control.image_scan.width'
HorizontalRange.scale = 1000
HorizontalRange.format = '%g'
HorizontalRange.properties = {'Enabled':'not control.scanning'}
VerticalRange.value = 'control.image_scan.height'
VerticalRange.scale = 1000
VerticalRange.format = '%g'
VerticalRange.properties = {'Enabled':'not control.scanning'}
StartRasterScan.action = {
    True: 'control.scanning = True',
    False:'control.scanning = False',
}
StartRasterScan.defaults = {"Enabled":False}
StartRasterScan.properties = {
    "Label": [
        ("Start Raster Scan","not control.scanning"),
        ("Cancel Raster Scan","control.scanning"),
    ],
    "Value": [
        (False, "control.scanning == False"),
        (True,  "control.scanning == True"),
    ],
    "Enabled": [
        (True,  "control.stage_online or control.scanning"),
    ],
    "BackgroundColour": [
        ("red","control.stage_enabled == False"),
    ],
}
CrystalCoordinates.value = "control.crystal_coordinates"
Initialize.action = {True: 'control.init()'}
Initialize.properties = {'Enabled': 'control.pump_online'}
Flow.action = {
    True:  'control.flowing = True',
    False: 'control.flowing = False',
}
Flow.properties = {
    'Enabled': 'control.pump_online',
    'Value': 'control.flowing',
    'Label': [
        ('Resume Flow','not control.flowing'),
        ('Suspend Flow','control.flowing'),
    ],
    "BackgroundColour": [("green","control.flowing")],
}
Inject.action = {
    True:  'control.injecting = True',
    False: 'control.injecting = False',
}
Inject.properties = {
    'Enabled': 'control.pump_online',
    'Value': 'control.injecting',
    'Label': '("Inject %s" if not control.injecting else "Cancel Inject %s") % control.inject_count'
}
MotherLiquorSyringeRefill.action = {
    True:  'control.mother_liquor_refilling = True',
    False: 'control.mother_liquor_refilling = False',
}
MotherLiquorSyringeRefill.properties = {
    'Enabled': 'control.pump_online',
    'Value': 'control.mother_liquor_refilling',
    'Label': [
        ('Refill','not control.mother_liquor_refilling'),
        ('Cancel Refill','control.mother_liquor_refilling'),
    ],
}
MotherLiquorSyringeVolume.value = 'control.mother_liquor.value'
MotherLiquorSyringeVolume.properties = {'Enabled': 'control.pump_online'}
MotherLiquorSyringeStepsize.value = 'control.mother_liquor_dV'
MotherLiquorSyringeStepsize.properties = {'Enabled': 'True'}
CrystalLiquorSyringeRefill.action = {
    True:  'control.crystal_liquor_refilling = True',
    False: 'control.crystal_liquor_refilling = False',
}
CrystalLiquorSyringeRefill.properties = {
    'Enabled': 'control.pump_online',
    'Value': 'control.crystal_liquor_refilling',
    'Label': [
        ('Refill','not control.crystal_liquor_refilling'),
        ('Cancel Refill','control.crystal_liquor_refilling'),
    ],
}
CrystalLiquorSyringeVolume.value = 'control.crystal_liquor.value'
CrystalLiquorSyringeVolume.properties = {'Enabled': 'control.pump_online'}
CrystalLiquorSyringeStepsize.value = 'control.crystal_liquor_dV'
CrystalLiquorSyringeStepsize.properties = {'Enabled': 'True'}
UpstreamPressure.value = 'control.upstream_pressure.value'
UpstreamPressure.format = '%.4f'
UpstreamPressure.properties = {'Enabled': 'True'}
DownstreamPressure.value = 'control.downstream_pressure.value'
DownstreamPressure.format = '%.4f'
DownstreamPressure.properties = {'Enabled': 'True'}
Image.properties = {
    'Image': 'control.camera.RGB_array',
    'ScaleFactor': '0.275',
    'Mirror': 'True',
    'Orientation': '0',
}
AcquireImage.properties = {'Enabled': 'True'}
ImageRootName.value = 'control.image_rootname'
ImageRootName.properties = {'Enabled': 'True'}
SaveImage.action = {True: 'control.save_image()'}
SaveImage.properties = {'Enabled': 'True'}
time = 1533775661.236139