#!/usr/bin/env python
"""
Trigger of:
- X-ray shutter:       R32 #1 J3     Event code 90 ch1
- X-ray attenuator:    R32 #2 J4     Event code 91 ch2
- Sample translation:  R31 #2 ETR-04 Event code 92 ch3
- Laser shutter:       R31 #3        Event code 93 (ch3)
- X-ray area detector: R31 #1 ETR-03 Event code 94 ch4
- Data acquisition:                  Event code 95
- Timing tool reference              Event code 96

Using LCLS event sequencer and event reveiver (EVR)

Two patterns:
- Data collection
- Alignment

Friedrich Schotte, 25 Nov 2013 - 2 Dec 2013
"""
__version__ = "1.0.4"

from CA import caget,caput,PV
from numpy import array,nan
from time import sleep

triggers = [
    {"name": "X-ray shutter",      "EVR": "XPP:R32:EVR:32", "row":1, "channel": 1, "event_code":90},
    {"name": "X-ray attenuator",   "EVR": "XPP:R32:EVR:32", "row":2, "channel": 2, "event_code":91},
    {"name": "Sample translation", "EVR": "XPP:R31:EVR:21", "row":1, "channel": 2, "event_code":92},
    {"name": "Laser shutter",      "EVR": "XPP:R31:EVR:21", "row":2, "channel": 3, "event_code":93},
    {"name": "X-ray area detector","EVR": "XPP:R31:EVR:21", "row":3, "channel": 1, "event_code":94},
]
# EVR: Event Receiver's EPICS record name
# row: 1-based index of the event row in the EDM screen
# channel: 0-based index of the event receiver

def event_code_name(event_code):
    """event_code: integer between 90 and 98"""
    for trigger in triggers:
        if trigger["event_code"] == event_code: return trigger["name"]
    return ""

def event_receiver_setup():
    for trigger in triggers:
        caput(trigger["EVR"]+":EVENT%sNAME"%trigger["row"],trigger["name"])
        caput(trigger["EVR"]+":EVENT%sCTRL.ENM"%trigger["row"],trigger["event_code"])
        caput(trigger["EVR"]+":EVENT%sCTRL.ENAB"%trigger["row"],1)
        for row in range(1,15):
            caput(trigger["EVR"]+":EVENT%sCTRL.OUT%d"%(row,trigger["channel"]),
                  row==trigger["row"])          
        # Reset event counter to zero.
        caput(trigger["EVR"]+":EVENT%sCNT"%trigger["row"],0)
        # Enable event counter.
        caput(trigger["EVR"]+":EVENT%sCRTL.VME"%trigger["row"],1)
        # Enable the trigger output
        caput(trigger["EVR"]+":CTRL.DG%sE"%trigger["channel"],1)
        # Polarity normal
        caput(trigger["EVR"]+":CTRL.DG%sP"%trigger["channel"],0)
        # Program output pulse length of event receiver to 8.333 ms.
        caput(trigger["EVR"]+":CTRL.DG%sW"%trigger["channel"],8400)
        caput(trigger["EVR"]+":CTRL.DG%sC"%trigger["channel"],119)

class EventSequencer(object):
    """Trigger generator"""
    stop_at_step    = PV("ECS:SYS0:3:LEN")
    event_code      = PV("ECS:SYS0:3:SEQ.A")
    delta_beam      = PV("ECS:SYS0:3:SEQ.B")
    fiducial_delays = PV("ECS:SYS0:3:SEQ.C")
    burst_count     = PV("ECS:SYS0:3:SEQ.D")
    process         = PV("ECS:SYS0:3:SEQ.PROC")
    base_rate       = PV("EVNT:SYS0:1:LCLSBEAMRATE")

    events = []

    def clear(self): self.events = []
    def add_event(self,time_mark,event_code):
        for i in range(len(self.events),time_mark+1): self.events += [[]]
        if not event_code in self.events[time_mark]:
            self.events[time_mark] += [event_code]
    def add_burst(self,start_time_mark,end_time_mark,event_code):
        """start_time_mark: first
        end_time_mark: not included"""
        for i in range(start_time_mark,end_time_mark):
            self.add_event(i,event_code)

    def update(self):
        event_code = []
        delta_beam = []
        last_time_mark = 0
        for i in range(0,len(self.events)):
            event_group = self.events[i]
            if len(event_group) == 0: continue
            event_code += event_group
            delta_beam += [i-last_time_mark]
            delta_beam += [0]*(len(event_group)-1)
            last_time_mark = i
        assert len(event_code) == len(delta_beam)
        n = len(event_code)
        self.stop_at_step.value = n
        self.event_code.value = event_code+[0]*(2048-n)
        self.delta_beam.value = delta_beam+[0]*(2048-n)
        self.fiducial_delays.value = [0]*2048
        self.burst_count.value = [0]*2048
        # Add labels to MEDM screen
        event_code += [0]*(20-len(event_code))
        for i in range(0,20):
            caput("XPP:ECS:IOC:01:EC_3:%02d.DESC"%i,
                  event_code_name(event_code[i]))
        sleep(0.1) # needed
        self.process.value = 1
        sleep(0.2) # needed
        self.process.value = 1 # needed

    @property
    def sequence_length(self):
        """interger value in multiples of 120-Hz cycles"""
        n = self.stop_at_step.value
        delta_beam = self.delta_beam.value
        sequence_length = sum(delta_beam[0:n])
        return sequence_length

    @property
    def period(self):
        """Repetion time in seconds"""
        rate = tofloat(self.base_rate.value)
        if rate == 0: return nan
        period = self.sequence_length/rate
        return period

    def single_shot_setup(self):
        self.clear()
        self.add_burst( 0, 1,90)# X-ray shutter
        self.add_burst( 2, 3,92)# Sample translation
        self.add_burst( 2, 3,94)# X-ray detector
        self.add_burst( 1, 2,95)# Data Acquisition
        self.add_event( 0,96)   # Timing tool reference
        self.add_event(13,0)    # add delay and the end for the rep rate
        self.update()
        event_receiver_setup()

    def collection_setup(self):
        self.clear()
        self.add_burst( 1,11,90)# X-ray shutter
        self.add_burst(14,15,90)# X-ray shutter
        self.add_burst( 1,11,91)# X-ray attenuator
        self.add_burst( 2, 3,92)# Sample translation
        self.add_burst(15,16,92)# Sample translation
        self.add_burst(14,15,93)# Laser shutter
        self.add_burst(12,13,94)# X-ray detector
        self.add_burst(25,26,94)# X-ray detector
        self.add_burst( 1,13,95)# Data Acquisition (X-ray shutter+1)
        self.add_burst(25,26,95)# Data Acquisition (X-ray shutter+1)
        self.add_event(26,0)    # add delay and the end for the rep rate
        self.update()
        event_receiver_setup()

    def alignment_setup(self):
        self.clear()
        self.add_burst( 2,12,90)# X-ray shutter
        self.add_burst( 2,12,91)# X-ray attenuator
        self.add_burst(13,14,92)# Sample translation
        self.add_burst(13,14,94)# X-ray detector
        self.add_burst( 3,13,95)# Data Acquisition (X-ray shutter+1)
        self.add_burst( 0, 1,95)# Data Acquisition (X-ray shutter+1)
        self.add_event(12,0)    # add delay and the end for the rep rate
        ##self.add_event(120,0)   # for debugging, slow down to 1 Hz
        self.update()
        event_receiver_setup()

    def test_setup(self):
        self.clear()
        self.add_event(0,90)
        self.add_event(0,91)
        self.add_event(0,92)
        self.add_event(0,93)
        self.add_event(0,94)
        self.add_event(24,0)
        self.update()

event_sequencer = EventSequencer() 


def start():
    """Start event sequencer"""
    caput("ECS:SYS0:3:PLYCTL",1)

def stop():
    """Start event sequencer"""
    caput("ECS:SYS0:3:PLYCTL",0)

class Pulses(object):
    """Number of pulses per acquisition"""
    mode_PV = PV("ECS:SYS0:3:PLYMOD") # 0=Once,1=N times,2=Forever
    target_count_PV = PV("ECS:SYS0:3:REPCNT")
    run_PV = PV("ECS:SYS0:3:PLYCTL")
    count_PV = PV("ECS:SYS0:3:PLYCNT") # counting up to target count

    doc = "When read return the number of pulses remaining until the burst"\
        "ends. When set trigger a burst with the given number of pulses."
    def get_value(self):
        """Number of pulses remaining until the burst ends"""
        # PV is counting up from zero to count_PV
        count = toint(self.target_count_PV.value) - toint(self.count_PV.value)
        return count
    def set_value(self,count):
        if count > 0:
            if self.mode_PV.value != 1:
                self.mode_PV.value = 1 # Repeat N Times
            if self.target_count_PV.value != count:
                self.target_count_PV.value = count
            self.run_PV.value = 1
        if count == 0:
            self.run_PV.value = 0
    value = property(get_value,set_value,doc=doc)

pulses = Pulses()

class ContinuousTrigger(object):
    """Is continuous triggering enabled?"""
    mode_PV = PV("ECS:SYS0:3:PLYMOD")
    run_PV = PV("ECS:SYS0:3:PLYCTL")

    def get_value(self):
        """Is continuous triggering enabled?"""
        return self.mode_PV.value == 2 and self.run_PV.value == 1
    def set_value(self,value):
        if bool(value) == True:
            if self.mode_PV.value != 2:
                self.mode_PV.value = 2 # Repeat Forever
            self.run_PV.value = 1
        else:
            self.run_PV.value = 0
    value = property(get_value,set_value)
    
    def __repr__(self): return self.PV.name

continuous_trigger = ContinuousTrigger()

class TMode(object):
    def get_value(self): return not continuous_trigger.value
    def set_value(self,value): continuous_trigger.value = not value
    value = property(get_value,set_value)

tmode = TMode()

class Waitt(object):
    """Waiting time between pulses"""
    unit = "s"
    stepsize = 1/120.
    # The repetiton rate is a subhamonic of 60 Hz.
    # Not every subharmonic is allowed. Only the following ones:
    frequencies={
        0: 60,
        1: 30,
        2: 10,
        3: 5,
        4: 1,
        5: 0.5,
    }

    def get_value(self):
        """Time between susequent X-ray pulse in seconds"""
        return event_sequencer.period
    def set_value(self,waitt): pass
    value = property(get_value,set_value)

    def get_min(self):
        """Lower limit in seconds"""
        return min(1.0/array(self.frequencies.values()))
    min = property(get_min)
    
    def get_max(self):
        """Upper limit in seconds"""
        return max(1.0/array(self.frequencies.values()))
    max = property(get_max)

    def get_choices(self):
        """Upper limit in seconds"""
        return 1.0/array(self.frequencies.values())
    choices = property(get_choices)

    def next(self,waitt):
        """Closest allowed value to the given waitting time in s"""
        from numpy import inf,array,argmin
        waitts = 1.0/array(self.frequencies.values())
        i = argmin(abs(waitt-waitts))
        return waitts[i]

waitt = Waitt()

class TriggerActive(object):
    status_PV =  PV("ECS:SYS0:3:PLSTAT") # 0: Stopped, 1:Playing
    control_PV = PV("ECS:SYS0:3:PLYCTL") # 0: Stop, 1:Start
    def get_value(self):
        return self.status_PV.value != 0
    def set_value(self,value):
        self.control_PV.value = 1 if value else 0
    value = property(get_value,set_value)

trigger_active = TriggerActive()
    
class XRayShutterEnabled(object):
    """X-ray shutter trigger enabled?"""
    enabled_PV = PV("XPP:R32:EVR:32:EVENT1CTRL.ENAB")
    def get_value(self):
        return self.enabled_PV.value
    def set_value(self,value):
        self.enabled_PV.value = 1 if value else 0
    value = property(get_value,set_value)

xray_shutter_enabled = XRayShutterEnabled()
mson = xray_shutter_enabled

class XRayShutterOpen(object):
    """X-ray shutter trigger enabled?"""
    polarity_PV = PV("XPP:R32:EVR:32:CTRL.DG1P")
    def get_value(self):
        level_OK = self.polarity_PV.value == 1
        active =  xray_shutter_enabled.value and trigger_active.value
        return level_OK and not active
    def set_value(self,value):
        self.polarity_PV.value = 1 if value else 0
    value = property(get_value,set_value)

xray_shutter_open = XRayShutterOpen()

class XRayAttenuatorInserted(object):
    """X-ray shutter trigger enabled?"""
    polarity_PV = PV("XPP:R32:EVR:32:CTRL.DG2P")
    def get_value(self):
        level_OK = self.polarity_PV.value == 1
        active =  xray_attenuator_enabled.value and trigger_active.value
        return level_OK and not active
    def set_value(self,value):
        self.polarity_PV.value = 1 if value else 0
    value = property(get_value,set_value)

xray_attenuator_inserted = XRayAttenuatorInserted()

class XRayDetectorTrigger():
    class TriggerLevel(object):
        """X-ray detector tigger input high?"""
        polarity_PV = PV("XPP:R31:EVR:21:CTRL.DG1P")
        def get_value(self):
            return self.polarity_PV.value == 1
        def set_value(self,value):
            self.polarity_PV.value = 1 if value else 0
        value = property(get_value,set_value)

    trigger_level = TriggerLevel()

    def trigger_once(self):
        """Send a single trigger pulse of 100 ms duraction
        to the X-ray detector"""
        self.trigger_level.value = True
        sleep(0.1)
        self.trigger_level.value = False

    class Count(object):
        """X-ray detector tigger input high?"""
        # Was unable to use XPP:R31:EVR:21:EVENT3CNT.
        # Count was not counting up. F. Schotte, 1 Dec 2013
        # Using XPP:IPM:EVR:EVENT2CNT instead.
        count_PV = PV("XPP:IPM:EVR:EVENT2CNT")
        event_code_PV = PV("XPP:IPM:EVR:EVENT2CTRL.ENM")
        enabled_PV = PV("XPP:IPM:EVR:EVENT2CTRL.VME")
        name_PV = PV("XPP:IPM:EVR:EVENT2NAME")
        offset = 0

        def setup(self):
            self.event_code_PV.value = 94
            self.enabled_PV.value = 1
            self.name_PV.value = "X-ray area detector"
            
        def get_value(self):
            return toint(self.count_PV.value) + self.offset
        def set_value(self,value):
            # "caput" does not change the count value.
            # Using a user-defined offset instead.
            self.offset = value - self.value
            ##self.count_PV.value = value
        value = property(get_value,set_value)

    count = Count()

xray_detector_trigger = XRayDetectorTrigger()

class SampleTranslationTrigger():
    class Count(object):
        """X-ray detector tigger input high?"""
        # Was unable to use XPP:R31:EVR:21:EVENT1CNT.
        # Count was not counting up. F. Schotte, 26 Nov 2013
        # Silke recommeded to use XPP:IPM:EVR:EVENT1CNT instead.
        count_PV = PV("XPP:IPM:EVR:EVENT1CNT")
        event_code_PV = PV("XPP:IPM:EVR:EVENT1CTRL.ENM")
        enabled_PV = PV("XPP:IPM:EVR:EVENT1CTRL.VME")
        name_PV = PV("XPP:IPM:EVR:EVENT1NAME")
        offset = 0

        def setup(self):
            self.event_code_PV.value = 92
            self.enabled_PV.value = 1
            self.name_PV.value = "Sample Translation"
            
        def get_value(self):
            return int(self.count_PV.value) + self.offset
        def set_value(self,value):
            # "caput" does not change the count value.
            # Using a user-defined offset instead.
            self.offset = value - self.value
            ##self.count_PV.value = value
        value = property(get_value,set_value)

    count = Count()

sample_translation_trigger = SampleTranslationTrigger()

def toint(x):
    """Convert x to a floating point number.
    If not convertible return zero"""
    try: return int(x)
    except: return 0

def tofloat(x):
    """Convert x to a floating point number.
    If not convertible return 'Not a Number'"""
    from numpy import nan
    try: return float(x)
    except: return nan


if __name__ == "__main__":
    self = event_sequencer # for debugging
    print "event_receiver_setup()"
    print "event_sequencer.single_shot_setup()"
    print "event_sequencer.collection_setup()"
    print "event_sequencer.alignment_setup()"
    print "pulses.value = 1"
    print "continuous_trigger.value = 1"
    print "sample_translation_trigger.count.value"
    print "sample_translation_trigger.count.value = 0"
