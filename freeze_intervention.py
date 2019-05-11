"""
Support module for optical freeze detector
Runs code to retract the sample from the cooling stream and operate the pump
at high speed as an AeroBasic program "Freeze_Intervention.ab".

Authors: Valentyn Stadnytskyi, Friedrich Schotte
Date created: 8 Mar 2018
Date last modified: 18 May 2018
"""
__version__ = "1.0.1" # Check if already running

class Freeze_Intervention(object):
    program_filename = "Freeze_Intervention.ab"
    def get_active(self):
        from Ensemble import ensemble
        return ensemble.auxiliary_task_filename == self.program_filename
    def set_active(self,value):
        from Ensemble import ensemble
        if value != self.active:
            if value: ensemble.auxiliary_task_filename = self.program_filename
            else: ensemble.auxiliary_task_filename = ""
    active = property(get_active,set_active)

    def get_enabled(self):
        from CA import caget
        return tobool(caget('NIH:SAMPLE_FROZEN_OPT_RGB:ENABLED'))
    def set_enabled(self,value):
        from CA import caput
        caput('NIH:SAMPLE_FROZEN_OPT_RGB:ENABLED',value)
    enabled = property(get_enabled,set_enabled)    
    
freeze_intervention = Freeze_Intervention()

def tobool(value):
    """Convert value to boolean or Not a Number if not possible"""
    from numpy import nan
    if value is None: value = nan
    else: value = bool(value)
    return value
        
if __name__ == "__main__":
    self = freeze_intervention # for debugging
    from Ensemble import ensemble # for debugging
    from time import sleep
    print("freeze_intervention.active")
    print("freeze_intervention.active = True")
    print("freeze_intervention.enabled")
    print("freeze_intervention.enabled = True")
    print("freeze_intervention.enabled = False")
