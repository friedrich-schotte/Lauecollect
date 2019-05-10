Enabled.action = {
    False: 'freeze_intervention.enabled = False',
    True: 'freeze_intervention.enabled = True'}
Enabled.defaults = {
    'Enabled': False, 'Label': '?'
}
Enabled.properties = {
    'BackgroundColour': [
        ('green', 'freeze_intervention.enabled == False'),
        ('red', 'freeze_intervention.enabled == True'),
        ('grey80', 'freeze_intervention.enabled not in [True,False]'),
    ],
    'Enabled': [(True, 'freeze_intervention.enabled in [True,False]')],
    'Value': [
        (True, 'freeze_intervention.enabled == True'),
        (False, 'freeze_intervention.enabled == False'),
    ],
    'Label': [
        ('Enabled', 'freeze_intervention.enabled == True'),
        ('Disabled', 'freeze_intervention.enabled == False'),
        ('?', 'freeze_intervention.enabled not in [True,False]'),
    ]
}

Active.action = {
    False: 'freeze_intervention.active = False',
    True: 'freeze_intervention.active = True'}
Active.defaults = {
    'Enabled': False, 'Label': '?'
}
Active.properties = {
    'BackgroundColour': [
        ('green', 'freeze_intervention.active == False'),
        ('red', 'freeze_intervention.active == True'),
        ('grey80', 'freeze_intervention.active not in [True,False]'),
    ],
    'Enabled': [(True, 'freeze_intervention.active in [True,False]')],
    'Value': [
        (True, 'freeze_intervention.active == True'),
        (False, 'freeze_intervention.active == False'),
    ],
    'Label': [
        ('Active', 'freeze_intervention.active == True'),
        ('Not active', 'freeze_intervention.active == False'),
        ('?', 'freeze_intervention.active not in [True,False]'),
    ]
}
