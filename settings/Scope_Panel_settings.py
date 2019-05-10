setup.value = 'self.scope.setup'
setup.properties = {
    'Enabled': 'self.scope.online',
    'Items': 'self.scope.setups',
}
recall.value = 'self.scope.setup_recall'
recall.properties = {
    'Enabled': 'self.scope.online',
}
save.value = 'self.scope.setup_save'
save.properties = {
    'Enabled': 'self.scope.online',
}
emptying_trace_directory.value = 'self.scope.emptying_trace_directory'
emptying_trace_directory.properties = {
    'Enabled': 'self.scope.online and self.scope.trace_directory_size > 0',
    'Label': [
        ('Clear Trace Directory', 'not self.scope.emptying_trace_directory'),
        ('Clearing Trace Directory...', 'self.scope.emptying_trace_directory'),
    ],
}
trace_directory_size.properties = {
    'Label': '("Traces stored: %.0f" % self.scope.trace_directory_size) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
emptying_trace_directory.refresh_period = 5.0
acquiring_waveforms.value = 'self.scope.acquiring_waveforms'
acquiring_waveforms.properties = {
    'Enabled': 'self.scope.online',
    'BackgroundColour': [
        ('green', 'self.scope.acquiring_waveforms'),
        ('red'  , 'not self.scope.acquiring_waveforms')
    ],
    'Label': [
        ('Recording Traces', 'self.scope.acquiring_waveforms'),
        ('Record Traces', 'not self.scope.acquiring_waveforms'),
    ],
}
acquiring_waveforms.refresh_period = 2.5
auto_acquire.value = 'self.scope.auto_acquire'
auto_acquire.properties = {
    'Enabled': 'self.scope.auto_acquire in [True,False]',
}
trace_count.properties = {
    'Label': '("Trace count: %.0f" % self.scope.trace_count) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
trigger_count.properties = {
    'Label': '("Trigger count: %r" % self.scope.timing_system_trigger_count) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
trace_count_offset.properties = {
    'Label': '("Trace count - Trigger count: %.0f" % self.scope.trace_count_offset) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
timing_jitter.properties = {
    'Label': '("Trigger timing jitter: %.3f s" % self.scope.timing_jitter) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
timing_offset.properties = {
    'Label': '("Trigger timing offset: %.3f s" % self.scope.timing_offset) if self.scope.online else "Offline"',
    'Enabled': 'self.scope.online',
}
trace_count_synchronized.value = 'self.scope.trace_count_synchronized'
trace_count_synchronized.properties = {
    'Enabled': 'self.scope.online and self.scope.acquiring_waveforms',
    'BackgroundColour': [
        ('green', 'self.scope.trace_count_synchronized'),
        ('red'  , 'not self.scope.trace_count_synchronized')
    ],
    'Label': [
        ('Synchronized', 'self.scope.trace_count_synchronized'),
        ('Synchronize', 'not self.scope.trace_count_synchronized'),
    ],
}
trace_count_synchronized.refresh_period = 2.5
auto_synchronize.value = 'self.scope.auto_synchronize'
auto_synchronize.properties = {
    'Enabled': 'self.scope.auto_synchronize in [True,False]',
}
trace_acquisition_running.value = 'self.scope.trace_acquisition_running'
trace_acquisition_running.properties = {
    'Enabled': 'self.scope.online',
    'BackgroundColour': [
        ('green', 'self.scope.trace_acquisition_running'),
    ],
    'Label': [
        ('Data Collection Running', 'self.scope.trace_acquisition_running'),
        ('Data Collection Not Running', 'not self.scope.trace_acquisition_running'),
    ],
}
trace_acquisition_running.refresh_period = 2.5
