"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "2.0"

from EPICS_CA.cached_function import cached_function

from db_property import db_property
from monitored_value_property import monitored_value_property
from alias_property import alias_property
from monitored_property import monitored_property


@cached_function()
def timing_system_channel_driver(channels, count):
    return Timing_System_Channel_Driver(channels, count)


class Timing_System_Channel_Driver(object):
    """Output of the timing system"""
    def __init__(self, channels, count):
        """count:  0 = ch1 ... 23 = ch24
        """
        self.channels = channels
        self.count = count

    def __repr__(self):
        return f"{self.timing_system}.{self.name}"

    @property
    def db_name(self):
        return f"{self.channels.db_name}.{self.name}"

    @property
    def registers(self):
        return self.timing_system.registers

    @property
    def timing_system(self):
        return self.channels.timing_system

    @property
    def name(self):
        return f"ch{self.count + 1:.0f}"

    from numpy import nan

    PP_enabled = db_property("PP_enabled", False)
    description = db_property("description", "")
    mnemonic = db_property("mnemonic", "")
    offset_HW = db_property("offset", nan)
    offset_sign = db_property("offset_sign", 1.0)
    offset_sign_choices = monitored_value_property([1, -1])
    pulse_length_HW = db_property("pulse_length", nan)
    offset_PP = db_property("offset_PP", nan)
    pulse_length_PP = db_property("pulse_length_PP", nan)
    counter_enabled = db_property("counter_enabled", 0)
    sign = db_property("sign", 1)
    timed = db_property("timed", "")  # timing relative to pump or probe
    timed_choices = monitored_value_property(["pump", "probe", "pump+probe", "pump-probe", "period"])
    gated = db_property("gated", "")  # enable?
    gated_choices = monitored_value_property(["detector", "pump", "probe", "trans"])
    repeat_period = db_property("repeat_period", "")  # how often?
    repeat_period_choices = monitored_value_property([
        "pulse",
        "burst start",
        "burst end",
        "image",
        "50 ms",
        "100 ms",
        "",
    ])
    on = db_property("on", True)
    bit_code = db_property("bit_code", 0)
    special = db_property("special", "")
    special_choices = monitored_value_property([
        "ms",  # X-ray millisecond shutter
        "ms_legacy",  # X-ray millisecond shutter
        "trans",  # Sample translation trigger
        "pso",  # Picosecond oscillator reference clock
        "nsf",  # Nanosecond laser flash lamp trigger
    ])

    def get_pulse_length(self):
        from numpy import nan, isnan

        value = nan
        if not isnan(self.pulse_length_PP):
            value = self.pulse_length_PP * self.timing_system.clock.hsct
        elif not isnan(self.pulse_length_HW):
            value = self.pulse_length_HW
        return value

    def set_pulse_length(self, value):
        self.pulse_length_HW = value

    pulse_length = property(get_pulse_length, set_pulse_length)

    def get_offset(self):
        from numpy import isnan

        value = 0.0
        if not isnan(self.offset_PP):
            value = self.offset_PP * self.timing_system.clock.hsct
        elif not isnan(self.offset_HW):
            value = self.offset_HW
        return value

    def set_offset(self, value):
        self.offset_HW = value

    offset = property(get_offset, set_offset)

    @property
    def channel_number(self):
        return self.count

    register_names = [
        "delay",
        "fine",
        "enable",
        "state",
        "pulse",
        "input",
        "override",
        "override_state",
        "trig_count",
        "acq_count",
        "acq",
        "specout",
    ]

    def register_name(self, name):
        """name: e.g. "state","delay" """
        return "ch%d_%s" % (self.count + 1, name)

    @property
    def delay(self):
        return getattr(self.registers, f"{self.name}_delay")

    @property
    def fine(self):
        return getattr(self.registers, f"{self.name}_fine")

    @property
    def enable(self):
        """Generate pulse every millisecond?"""
        return getattr(self.registers, f"{self.name}_enable")

    @property
    def state(self):
        """Current level: 0=low,1=high"""
        return getattr(self.registers, f"{self.name}_state")

    @property
    def pulse(self):
        """Output pulse duration"""
        return getattr(self.registers, f"{self.name}_pulse")

    pulse_choices = monitored_value_property([1e-3, 2e-3, 3e-3, 10e-3, 30e-3, 100e-3])

    @property
    def input(self):
        """Configured as input?"""
        return getattr(self.registers, f"{self.name}_input")

    @property
    def override(self):
        """Override Piano player? [0=pass,1=override]"""
        return getattr(self.registers, f"{self.name}_override")

    @property
    def override_state(self):
        """Override state [0=low,1=high]"""
        return getattr(self.registers, f"{self.name}_override_state")

    @property
    def trig_count(self):
        """Trigger count [0-4294967295]"""
        return getattr(self.registers, f"{self.name}_trig_count")

    @property
    def acq_count(self):
        """Acquisition count [0-2147483647]"""
        return getattr(self.registers, f"{self.name}_acq_count")

    @property
    def acq(self):
        """Acquiring? [0=discard,1=save]"""
        return getattr(self.registers, f"{self.name}_acq")

    override_count = alias_property("override.count")
    override_state_count = alias_property("override_state.count")

    @monitored_property
    def output_status(self, override_count, override_state_count):
        """PP = pass piano player state, Low, High = override"""
        if not override_count:
            status = "PP"
        else:
            status = "Low" if override_state_count == 0 else "High"
        return status

    @output_status.setter
    def output_status(self, value):
        if value.capitalize() == "High":
            self.override.count = True
            self.override_state.count = True
        if value.capitalize() == "Low":
            self.override.count = True
            self.override_state.count = False
        if value.upper() == "PP":
            self.override.count = False

    output_status_choices = monitored_value_property(["PP", "Low", "High"])

    @property
    def specout(self):
        """Special output: 0=normal, 1=70.4 MHz"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("specout")
        )

    @property
    def stepsize(self):
        """Resolution in seconds"""
        return 0.5 * self.timing_system.clock.bct

    def user_from_dial(self, value):
        return value * self.sign + self.offset

    def dial_from_user(self, value):
        return (value - self.offset) / self.sign

    def count_from_value(self, value):
        """Convert user value to integer register count"""
        return self.count_from_dial(self.dial_from_user(value))

    def value_from_count(self, count):
        """Convert integer register count to user value"""
        return self.user_from_dial(self.dial_from_count(count))

    def count_from_dial(self, dial_value):
        """Convert user value to integer register count"""
        count = self.next_count(dial_value / self.stepsize)
        return count

    def dial_from_count(self, count):
        """Convert integer register count to user value"""
        dial_value = count * self.stepsize
        return dial_value

    from numpy import inf

    min_count = 0
    max_count = inf
    min_dial = 0.0
    max_dial = inf

    def get_min(self):
        return self.user_from_dial(self.min_dial)

    def set_min(self, value):
        self.min_dial = self.dial_from_user(value)

    min = property(get_min, set_min, doc="Low limit in user units")

    def get_max(self):
        return self.user_from_dial(self.max_dial)

    def set_max(self, value):
        self.max_dial = self.dial_from_user(value)

    max = property(get_max, set_max, doc="High limit in user units")

    def next_count(self, count):
        """Round value to the next allowed integer count"""
        from numpy import clip, isnan, nan
        from to_int import to_int

        if isnan(count):
            return nan
        count = clip(count, self.min_count, self.max_count)
        count = to_int(count)
        return count

    def next(self, value):
        """What is the closest possible value to the given user value the register
        can hold?
        value: user value"""
        count = self.count_from_value(value)
        value = self.value_from_count(count)
        return value


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_driver_9 import timing_system_driver
    from timing_system_channels_driver_2 import timing_system_channels_driver

    timing_system = timing_system_driver(domain_name)
    channels = timing_system_channels_driver(timing_system)
    self = timing_system_channel_driver(channels, 0)

    print("self.trig_count")
