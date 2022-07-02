"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-07
Revision comment:
"""
__version__ = "1.0"

import warnings

from EPICS_CA.cached_function import cached_function

from timing_system_parameter import Parameter


@cached_function()
def timing_system_channel(timing_system, count):
    return Channel(timing_system, count)


class Channel(object):
    """Output of the timing system"""
    from alias_property import alias_property
    from monitored_property import monitored_property

    def __init__(self, timing_system, count):
        """count:  0 = ch1 ... 23 = ch24
        """
        self.timing_system = timing_system
        self.count = count

    def __repr__(self):
        # return self.name
        return f"{self.timing_system!r}.{self.name}"

    def PV_name(self, property_name):
        prop = getattr(type(self), property_name, None)
        if hasattr(prop, "PV_name"):
            PV_name = prop.PV_name(self)
        else:
            property_name = property_name.split(".")[0]
            obj = getattr(self, property_name, None)
            PV_name = getattr(obj, "PV_name", "")
        return PV_name

    def monitor(self, property_name, handler, *args, **kwargs):
        warnings.warn("monitor() is deprecated, use __getattr_monitors__",
                      DeprecationWarning, stacklevel=2)
        prop = getattr(type(self), property_name, None)
        if hasattr(prop, "monitor"):
            prop.monitor(self, handler, *args, **kwargs)
        else:
            property_name = property_name.split(".")[0]
            obj = getattr(self, property_name, None)
            if hasattr(obj, "monitor"):
                obj.monitor(handler, *args, **kwargs)

    def monitor_clear(self, property_name, handler, *args, **kwargs):
        warnings.warn("monitor_clear() is deprecated, use __getattr_monitors__",
                      DeprecationWarning, stacklevel=2)
        prop = getattr(type(self), property_name, None)
        if hasattr(prop, "monitor_clear"):
            prop.monitor_clear(self, handler, *args, **kwargs)
        else:
            property_name = property_name.split(".")[0]
            obj = getattr(self, property_name, None)
            if hasattr(obj, "monitor_clear"):
                obj.monitor_clear(handler, *args, **kwargs)

    def monitors(self, property_name):
        warnings.warn("monitors() is deprecated, use __getattr_monitors__",
                      DeprecationWarning, stacklevel=2)
        monitors = []
        prop = getattr(type(self), property_name, None)
        if hasattr(prop, "monitors"):
            monitors = prop.monitors(self)
        else:
            property_name = property_name.split(".")[0]
            obj = getattr(self, property_name, None)
            if hasattr(obj, "monitors"):
                monitors = obj.monitors
        return monitors

    @property
    def name(self):
        name = "ch%d" % (int(self.count) + 1)
        return name

    @property
    def db_name(self):
        return self.timing_system.db_name + "." + self.name

    from numpy import nan

    PP_enabled = Parameter("PP_enabled", False)
    description = Parameter("description", "")
    mnemonic = Parameter("mnemonic", "")
    offset_HW = Parameter("offset", nan)
    offset_sign = Parameter("offset_sign", 1.0)
    offset_sign_choices = 1, -1
    pulse_length_HW = Parameter("pulse_length", nan)
    offset_PP = Parameter("offset_PP", nan)
    pulse_length_PP = Parameter("pulse_length_PP", nan)
    counter_enabled = Parameter("counter_enabled", 0)
    sign = Parameter("sign", 1)
    timed = Parameter("timed", "")  # timing relative to pump or probe
    timed_choices = "pump", "probe", "pump+probe", "pump-probe", "period"
    gated = Parameter("gated", "")  # enable?
    gated_choices = "detector", "pump", "probe", "trans"
    repeat_period = Parameter("repeat_period", "")  # how often?
    repeat_period_choices = (
        "pulse",
        "burst start",
        "burst end",
        "image",
        "50 ms",
        "100 ms",
        "",
    )
    on = Parameter("on", True)
    bit_code = Parameter("bit_code", 0)
    special = Parameter("special", "")
    special_choices = (
        "ms",  # X-ray millisecond shutter
        "ms_legacy",  # X-ray millisecond shutter
        "trans",  # Sample translation trigger
        "pso",  # Picosecond oscillator reference clock
        "nsf",  # Nanosecond laser flash lamp trigger
    )

    def get_pulse_length(self):
        from numpy import nan, isnan

        value = nan
        if not isnan(self.pulse_length_PP):
            value = self.pulse_length_PP * self.timing_system.hsct
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
            value = self.offset_PP * self.timing_system.hsct
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
        from timing_system_timing_register import timing_register
        return timing_register(
            self.timing_system,
            self.register_name("delay"),
            stepsize="bct/2",
            max_count=712799,
        )

    @property
    def fine(self):
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("fine")
        )

    @property
    def enable(self):
        """Generate pulse every millisecond?"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("enable")
        )

    @property
    def state(self):
        """Current level: 0=low,1=high"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("state")
        )

    @property
    def pulse(self):
        """Output pulse duration"""
        from timing_system_timing_register import timing_register
        return timing_register(
            self.timing_system, self.register_name("pulse"), stepsize="bct*4"
        )

    pulse_choices = [1e-3, 2e-3, 3e-3, 10e-3, 30e-3, 100e-3]

    @property
    def input(self):
        """Configured as input?"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("input")
        )

    @property
    def override(self):
        """Override Piano player? [0=pass,1=override]"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("override")
        )

    @property
    def override_state(self):
        """Override state [0=low,1=high]"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("override_state")
        )

    @property
    def trig_count(self):
        """Trigger count [0-4294967295]"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("trig_count")
        )

    @property
    def acq_count(self):
        """Acquisition count [0-2147483647]"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("acq_count")
        )

    @property
    def acq(self):
        """Acquiring? [0=discard,1=save]"""
        from timing_system_register import register
        return register(
            self.timing_system, self.register_name("acq")
        )

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

    output_status_choices = ["PP", "Low", "High"]

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
        return 0.5 * self.timing_system.bct

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


@cached_function()
def channel(timing_system, count):
    return Channel(timing_system, count)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system import timing_system

    timing_system = timing_system(domain_name)
    self = timing_system_channel(timing_system, 6)

    print("self.trig_count")
