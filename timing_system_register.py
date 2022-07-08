"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-07-07
Revision comment: Not caching PVs
"""
__version__ = "1.0.1"

import warnings
from logging import warning
from traceback import format_exc

from cached_function import cached_function
from reference import reference


@cached_function()
def register(
        timing_system,
        name,
        min=None,
        max=None,
        min_count=None,
        max_count=None,
):
    return Register(
        timing_system,
        name,
        min=min,
        max=max,
        min_count=min_count,
        max_count=max_count,
    )


class Register(object):
    """User-programmable parameter of FPGA timing system"""
    from monitored_property import monitored_property
    from timing_system_register_property import Register_Property
    from timing_system_parameter import Parameter

    sign = 1

    def __init__(
            self, timing_system, name, min=None, max=None, min_count=None, max_count=None
    ):
        """
    name: mnemonic or hexadecimal address as string
    stepsize: resolution in units of seconds
    min: minimum count
    max: maximum count
    min_count: minimum count
    max_count: maximum count
    """
        self.timing_system = timing_system
        self.name = name
        if min is not None:
            self.min = min
        if max is not None:
            self.max = max
        if min_count is not None:
            self.min_count = min_count
        if max_count is not None:
            self.max_count = max_count
        self.unit = ""

    # for sorting
    def __lt__(self, other):
        result = self.name < getattr(other, "name", "")
        # debug("%r < %r? %r" % (self, other, result))
        return result

    from numpy import nan
    count = Register_Property("count", nan, int)

    @property
    def PV_name(self):
        """Process variable name for EPICS Channel Access"""
        return self.timing_system.prefix + "registers." + self.name + ".count"

    @property
    def PV(self):
        from CA import PV
        return PV(self.PV_name)

    def next_count(self, count):
        """Round value to the next allowed integer count"""
        from numpy import rint, isnan, nan
        from to_int import to_int

        if isnan(count):
            return nan
        if count < self.min_count:
            count = self.min_count
        if count > self.max_count:
            count = self.max_count
        count = to_int(rint(count))
        return count

    def next(self, value):
        """What is the closest possible value to the given user value the
        register can hold?
        Return value: user value"""
        count = self.count_from_value(value)
        value = self.value_from_count(count)
        return value

    description = Register_Property("description", "", str)
    address = Register_Property("address", 0, int)
    bit_offset = Register_Property("bit_offset", 0, int)
    bits = Register_Property("bits", 0, int)

    def calculate_value(self, dial, offset):
        return self.user_from_dial(dial, offset)

    def set_value(self, value):
        from numpy import isnan
        if not isnan(value):
            self.dial = self.dial_from_user(value)

    def inputs_value(self):
        return [
            reference(self, "dial"),
            reference(self, "offset"),
        ]

    value = monitored_property(
        calculate=calculate_value,
        fset=set_value,
        inputs=inputs_value,
    )
    command_value = value

    def calculate_dial(self, count):
        return self.dial_from_count(count)

    def set_dial(self, value):
        self.count = self.count_from_dial(value)

    def inputs_dial(self):
        return [
            reference(self, "count"),
        ]

    dial = monitored_property(
        calculate=calculate_dial,
        fset=set_dial,
        inputs=inputs_dial,
    )

    def get_min_count(self):
        """Lowest allowed count"""
        if hasattr(self, "__min_count__"):
            return self.__min_count__
        return 0

    def set_min_count(self, value):
        if value < 0:
            value = 0
        self.__min_count__ = value

    min_count = property(get_min_count, set_min_count)

    def get_max_count(self):
        """Highest allowed count"""
        if hasattr(self, "__max_count__"):
            return self.__max_count__
        return 2 ** self.bits - 1

    def set_max_count(self, value):
        self.__max_count__ = value

    max_count = property(get_max_count, set_max_count)

    min = min_count
    max = max_count

    def get_min_dial(self):
        return self.dial_from_count(self.min_count)

    def set_min_dial(self, min_dial):
        # noinspection PyBroadException
        try:
            self.min_count = self.count_from_dial(min_dial)
        except Exception:
            warning("%r.min_dial = %r: %s" % (self, min_dial, format_exc()))

    min_dial = property(get_min_dial, set_min_dial)

    def get_max_dial(self):
        return self.dial_from_count(self.max_count)

    def set_max_dial(self, max_dial):
        # noinspection PyBroadException
        try:
            self.max_count = self.count_from_dial(max_dial)
        except Exception:
            warning("%r.max_dial = %r: %s" % (self, max_dial, format_exc()))

    max_dial = property(get_max_dial, set_max_dial)

    def get_min_value(self):
        return self.user_from_dial(self.min_dial)

    def set_min_value(self, value):
        self.min_dial = self.dial_from_user(value)

    min_value = property(get_min_value, set_min_value)

    def get_max_value(self):
        return self.user_from_dial(self.max_dial)

    def set_max_value(self, value):
        self.max_dial = self.dial_from_user(value)

    max_value = property(get_max_value, set_max_value)

    def count_from_value(self, value):
        """Convert user value to integer register count"""
        return self.count_from_dial(self.dial_from_user(value))

    def value_from_count(self, count):
        """Convert integer register count to user value"""
        return self.user_from_dial(self.dial_from_count(count))

    def count_from_dial(self, dial_value):
        """Convert delay in seconds to integer register count"""
        count = self.next_count(dial_value / self.stepsize)
        return count

    def dial_from_count(self, count):
        """Convert integer register count to delay in seconds"""
        dial_value = count * self.stepsize
        return dial_value

    def user_from_dial(self, value, offset=None):
        if offset is None:
            offset = self.offset
        return value * self.sign + offset

    def dial_from_user(self, value, offset=None):
        if offset is None:
            offset = self.offset
        return (value - offset) / self.sign

    stepsize = Parameter("stepsize", 1.0)
    offset = Parameter("offset", 0.0)

    def __repr__(self):
        return self.name

    def get_PP_enabled(self):
        value = False
        if self.channel is not None:
            value = self.channel.PP_enabled
        return value

    def set_PP_enabled(self, value):
        if self.channel is not None:
            self.channel.PP_enabled = value

    PP_enabled = property(get_PP_enabled, set_PP_enabled)

    def get_special(self):
        value = ""
        if self.channel is not None:
            value = self.channel.special
        return value

    def set_special(self, value):
        if self.channel is not None:
            self.channel.special = value

    special = property(get_special, set_special)

    @property
    def channel(self):
        channel = None
        if self.name.startswith("ch") and "_" in self.name:
            count = self.name.split("_")[0].replace("ch", "")
            # noinspection PyBroadException
            try:
                channel_number = int(count) - 1
                channel = self.timing_system.channels[channel_number]
            except Exception:
                pass
        return channel

    def monitor(self, *args, **kwargs):
        warnings.warn("monitor() is deprecated, use reference(register, 'count').monitors.add()",
                      DeprecationWarning, stacklevel=2)

        if type(args[0]) != str:  # for backward compatibility
            warning(
                ("'%r.monitor(%r,...)' without property name is deprecated. " % (self, args[0])) +
                ("Use 'monitor(%r,'count',...)' instead" % self)
            )
            property_name = "count"
            proc = args[0]
            args = args[1:]
        else:
            property_name = args[0]
            proc = args[1]
            args = args[2:]
        monitor = getattr(getattr(type(self), property_name), "monitor", None)
        if monitor:
            monitor(self, proc, *args, **kwargs)
        else:
            warning("%r.%s does not support monitoring" % (self, property_name))

    def monitor_clear(self, *args, **kwargs):
        warnings.warn("monitor_clear() is deprecated, use reference(register, 'count').monitors.remove()",
                      DeprecationWarning, stacklevel=2)

        if type(args[0]) != str:  # for backward compatibility
            warning(
                ("'%r.monitor_clear(...)' without property name is deprecated. " % self) +
                ("Use 'monitor_clear(%r,'count',...)' instead" % self)
            )
            property_name = "count"
            proc = args[0]
            args = args[1:]
        else:
            property_name = args[0]
            proc = args[1]
            args = args[2:]
        monitor_clear = getattr(getattr(type(self), property_name), "monitor_clear", None)
        if monitor_clear:
            monitor_clear(self, proc, *args, **kwargs)

    @property
    def monitors(self):
        warnings.warn("monitors() is deprecated, use reference(register, 'count').monitors",
                      DeprecationWarning, stacklevel=2)
        property_name = "count"
        handlers = getattr(type(self), property_name).monitors(self)
        procedures = [handler.procedure for handler in handlers]
        return procedures
