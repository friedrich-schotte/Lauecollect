title = "Timing System Configuration"
icon = "timing-system"
EPICS_Record.value = 'timing_system.prefix'
EPICS_Record.properties = {
    'Enabled': 'True',
    'Items': 'timing_system.prefixes',
}
IP_Address.properties = {
    'Enabled': 'False',
    'Value': '"Address "+timing_system.ip_address if timing_system.ip_address else "offline"',
}
Configuration.value = 'timing_system.configuration'
Configuration.properties = {
    'Enabled': 'timing_system.online',
    'Items': 'timing_system.configurations',
}
Load.action = {
    True: 'timing_system.load_configuration()'
}
##Load.value = 'timing_system.save_configuration()'
Load.properties = {
    'Enabled': 'timing_system.online',
    'Label': '"Load Configuration"',
}
Save.action = {
    True: 'timing_system.save_configuration()'
}
##Save.value = 'timing_system.save_configuration()'
Save.properties = {
    'Enabled': 'timing_system.online',
    'Label': '"Save Configuration"',
}
