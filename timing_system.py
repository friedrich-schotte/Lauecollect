#!/usr/bin/env python
"""
FPGA Timing System

Author: Friedrich Schotte
Date created: 2007-04-02
Date last modified: 2022-07-17
Revision comment: Made monitored property: channel_mnemonics
"""
__version__ = "8.31.4"

import logging
from logging import debug, info, warning, error
from traceback import format_exc

from triggered_method import triggered_method
from PV_property import PV_property
from cached_function import cached_function
from handler import handler
from monitored_property import monitored_property
from timing_system_channel import Channel, channel
from timing_system_configuration import Configuration
from timing_system_dummy_register import dummy_register
from timing_system_parameter import Parameter
from timing_system_parameters import Parameters
from timing_system_register import register
from timing_system_timing_register_property import timing_register_property
from timing_system_variable import Variable
from timing_system_variable_property import variable_property


@cached_function()
def timing_system(domain_name):
    return Timing_System(domain_name)


class Timing_System(object):
    """FPGA Timing system"""
    from alias_property import alias_property
    from thread_property_2 import thread_property

    def __init__(self, domain_name="BioCARS"):
        self.name = domain_name
        self.register_names_setup()
        self.save_register_names = True
        self.channel_mnemonics_setup()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.name)

    def __dir__(self):
        return sorted(set(self.names + list(super().__dir__()) + list(self.__dict__.keys())))

    @property
    def domain_name(self):
        return self.name

    @property
    def names(self):
        return self.channel_names

    @property
    def default_prefix(self):
        prefix = self.name.upper() + ":TIMING."
        prefix = prefix.replace("BIOCARS", "NIH")
        return prefix

    @property
    def db_name(self):
        return "timing_system/" + self.name

    from db_property import db_property

    prefix = db_property("prefix", default_prefix)
    prefixes = db_property(
        "prefixes", ["NIH:TIMING.", "TESTBENCH:TIMING.", "LASERLAB:TIMING.", ]
    )

    Channel = Channel
    Variable = Variable
    Parameters = Parameters
    Configuration = Configuration

    from PV_info_property import PV_info_property
    ip_address = PV_info_property("registers", "IP_address", upper_case=False)

    @monitored_property
    def online(self, ip_address):
        online = ip_address != ""
        return online

    register_name_list = PV_property("registers", dtype=str, upper_case=False)

    def register_names_setup(self):
        if not self.saved_register_names and self.register_names:
            logging.debug(f"{self}.saved_register_names = {self.register_names}")
            self.saved_register_names = self.register_names

    @triggered_method
    def save_register_names(self, register_names):
        if register_names:
            logging.debug(f"{self}.saved_register_names = {register_names}")
            self.saved_register_names = register_names

    @monitored_property
    def register_names(self, register_name_list):
        names = register_name_list.split(";")
        while "" in names:
            names.remove("")
        return names

    saved_register_names = db_property("saved_register_names", [])

    all_register_names = alias_property("saved_register_names")

    channel_mnemonics = alias_property("channel_mnemonics_saved")

    channel_mnemonics_saved = db_property("channel_mnemonics", [""] * 24)

    def channel_mnemonics_setup(self):
        from CA import camonitor_handlers

        for (i, channel) in enumerate(self.channels):
            camonitor_handlers(self.channel_mnemonic_PV_name(i)). \
                add(handler(self.channel_mnemonics_update, i))

    def channel_mnemonics_update(self, i):
        with self.channel_mnemonics_lock:
            mnemonics = self.channel_mnemonics_saved
            while len(mnemonics) < i + 1:
                mnemonics.append("")
            from CA import caget
            mnemonic = caget(self.channel_mnemonic_PV_name(i))
            if mnemonic:
                # noinspection PyBroadException
                try:
                    mnemonic = eval(mnemonic)
                except Exception:
                    debug("%r: %s" % (mnemonic, format_exc()))
                else:
                    if mnemonic != mnemonics[i]:
                        debug("mnemonics[%d] = %r" % (i, mnemonic))
                        mnemonics[i] = mnemonic
            if self.channel_mnemonics_saved != mnemonics:
                logging.debug(f"{self}.channel_mnemonics_saved = {mnemonics}")
                self.channel_mnemonics_saved = mnemonics

    def channel_mnemonic_PV_name(self, i):
        return self.parameter_PV_name("%s.mnemonic" % (self.channel_names[i]))

    from threading import Lock
    channel_mnemonics_lock = Lock()

    def register_PV_name(self, name):
        """Process variable name for EPICS Channel Access"""
        return self.prefix + "registers." + name + ".count"

    def register(self, name):
        return register(self, name)

    def dummy_register(self, name):
        return dummy_register(self, name)

    @property
    def registers(self):
        from timing_system_registers import timing_system_registers
        return timing_system_registers(self)

    channels_count = 24

    @property
    def channel_names(self):
        return ["ch%d" % (i + 1) for i in range(0, self.channels_count)]

    def channel(self, i):
        return channel(self, i)

    @property
    def channels(self):
        from timing_system_channels import timing_system_channels
        return timing_system_channels(self)

    def channel_register_name(self, name):
        register_name = ""
        properties = Channel.register_names
        for channel in self.channels:
            if name.startswith(channel.mnemonic + "_"):
                for prop in properties:
                    if name == channel.mnemonic + "_" + prop:
                        register_name = channel.name + "_" + prop
        return register_name

    variable_dict = {}

    def add_variable(self, variable):
        """register: register object"""
        self.variable_dict[repr(variable)] = variable
        self.__dict__[repr(variable)] = variable  # helpful for auto-complete

    def variable(self, name):
        return self.variable_dict[name]

    @property
    def variables(self):
        return list(self.variable_dict.values())

    @property
    def variable_names(self):
        return list(self.variable_dict.keys())

    def __getattr__(self, name):
        """A register object"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        # debug("__getattr__(%r)" % name)
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("attribute %r not found" % name)
        if name.startswith("_") and name.endswith("_"):
            raise AttributeError("attribute %r not found" % name)
        # debug("Is %r a register?" % name)
        if name in self.channel_names:
            return self.channels[self.channel_names.index(name)]
        elif name in self.variable_dict:
            return self.variable_dict[name]
        elif name in self.all_register_names:
            return register(self, name)
        elif self.channel_register_name(name):
            return register(self, self.channel_register_name(name))
        elif name in self.channel_mnemonics:
            return self.channels[self.channel_mnemonics.index(name)]
        else:
            raise AttributeError("Is %r a register?" % name)

    def register_count(self, name):
        """Reads the content of a register as integer value"""
        from numpy import nan

        name = "registers.%s.count" % name
        value = self.get_property(name)
        try:
            return int(value)
        except ValueError:
            return nan

    def set_register_count(self, name, value):
        """Loads an integer value into the register"""
        from numpy import isnan

        if isnan(value):
            return
        value = "%d" % value
        name = "registers.%s.count" % name
        self.set_property(name, value)

    def register_property(self, name, property_name, default_value=0):
        """Information about the register
        property_name: 'address','bit_offset','bits'"""
        from numpy import nan  # noqa - needed for eval

        full_name = "registers.%s.%s" % (name, property_name)
        string_value = self.get_property(full_name)
        try:
            value = type(default_value)(eval(string_value))
        except Exception as msg:
            if type(default_value) != str:
                if string_value != "":
                    debug(
                        "%s: %r(%r): %s"
                        % (full_name, type(default_value), string_value, msg)
                    )
                value = default_value
            else:
                value = string_value
        if string_value == "":
            error("%r defaulting to %r" % (full_name, value))
        # Convert from signed to unsigned int
        # (Channel Access does not support unsigned int)
        if is_int(value):
            value = unsigned_int(value)
        return value

    def set_register_property(self, name, property_name, value):
        """Information about the register.
        property_name: 'address','bit_offset','bits'"""
        from numpy import isnan

        if isnan(value):
            return
        value = "%d" % value
        name = "registers.%s.%s" % (name, property_name)
        self.set_property(name, value)

    def parameter(self, name, default_value=0.0):
        """This retrieves a calibration constant from non-volatile memory of the
        FPGA."""
        property_name = "parameters." + name
        value = self.get_property(property_name)
        value = parameter_value(value, default_value,
                                report_name=property_name)
        return value

    def set_parameter(self, name, value, default_value=None):
        """This stores a calibration constant in non-volatile memory in the FPGA."""
        # debug("set_parameter(%r,%r)" % (name,value))
        property_name = "parameters.%s" % name
        str_value = parameter_PV_value(value, default_value)
        self.set_property(property_name, str_value)

    def parameter_PV_name(self, name):
        return self.property_PV_name("parameters." + name)

    def parameter_PV(self, name):
        from CA import PV
        return PV(self.parameter_PV_name(name))

    def parameter_monitor(self, name, handler, *args, **kwargs):
        return self.monitor_property("parameters." + name, handler, *args, **kwargs)

    def parameter_monitor_clear(self, name, handler, *args, **kwargs):
        return self.monitor_clear_property(
            "parameters." + name, handler, *args, **kwargs
        )

    def parameter_monitors(self, name):
        return self.monitors_property("parameters." + name)

    @property
    def parameter_names(self):
        return self.get_property("parameters").split(";")

    @property
    def parameters(self):
        from timing_system_parameters import Parameters
        return Parameters(self)

    @staticmethod
    def caget(PV_name):
        from CA_cached import caget_cached as caget
        value = caget(PV_name)
        return value

    def get(self, name, default_value=None, dtype=None):
        """Retrieve a register content ot parameter, using Channel Access
        return value: string"""
        PV_name = self.property_PV_name(name)
        value = self.caget(PV_name)
        value = register_property_value(value, default_value, dtype, report_name=PV_name)
        return value

    def get_property(self, name):
        """Retrieve a register content ot parameter, using Channel Access
        return value: string"""
        PV_name = self.property_PV_name(name)
        value = self.caget(PV_name)
        if value is None:
            debug("Failed to get PV %r" % PV_name)
            value = ""
        # Convert from signed to unsigned int (Channel Access does not support unsigned int)
        if is_int(value) and value < 0:
            value = value + 0x100000000
        if type(value) != str:
            value = str(value)
        # debug("%r:  %.80r" % (name,value))
        return value

    def set_property(self, name, value):
        """Modify a register content ot parameter, using Channel Access
        value: string"""
        PV_name = self.property_PV_name(name)
        from CA import caput

        # debug("caput(%r,%r,wait=True)" % (PV_name,value))
        caput(PV_name, value, wait=True)

    def monitor_property(self, name, proc, *args, **kwargs):
        PV_name = self.property_PV_name(name)
        from CA import camonitor_handlers
        camonitor_handlers(PV_name).add(handler(proc, *args, **kwargs))

    def monitor_clear_property(self, name, proc, *args, **kwargs):
        PV_name = self.property_PV_name(name)
        from CA import camonitor_handlers
        camonitor_handlers(PV_name).remove(handler(proc, *args, **kwargs))

    def monitors_property(self, name):
        PV_name = self.property_PV_name(name)
        from CA import camonitor_handlers

        return camonitor_handlers(PV_name)

    def property_PV_name(self, name):
        return self.prefix + name

    def property_PV(self, name):
        from CA import PV
        return PV(self.property_PV_name(name))

    @monitored_property
    def clock_period(self, clk_src_count, clock_period_internal, clock_period_external):
        """Clock period in s (ca. 2.8 ns)"""
        if clk_src_count == 29:
            return clock_period_internal
        else:
            return clock_period_external

    @clock_period.setter
    def clock_period(self, value):
        if self.clk_src_count == 29:
            self.clock_period_internal = value
        else:
            self.clock_period_external = value

    clk_src_count = alias_property("registers.clk_src.count")

    clock_period_external = Parameter("clock_period_external", 1 / 351933984.0)
    clock_period_internal = Parameter("clock_period_internal", 1 / 350000000.0)

    @monitored_property
    def bct(self, clk_on_count, clock_period, clock_multiplier, clock_divider):
        """Bunch clock period in s (ca. 2.8 ns)"""
        if clk_on_count == 0:
            T = clock_period
        else:
            T = clock_period / clock_multiplier * clock_divider
        return T

    @bct.setter
    def bct(self, value):
        if self.clk_on_count == 0:
            self.clock_period = value
        else:
            self.clock_period = value * self.clock_multiplier / self.clock_divider

    clk_on_count = alias_property("registers.clk_on.count")

    @monitored_property
    def clock_divider(self, clk_div_count):
        """Clock scale factor"""
        value = clk_div_count + 1
        return value

    @clock_divider.setter
    def clock_divider(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_div_count = value - 1
        else:
            warning("%r must be in range 1 to 32.")

    clk_div_count = alias_property("registers.clk_div.count")

    @monitored_property
    def clock_multiplier(self, clk_mul_count):
        value = (clk_mul_count + 1) / 2
        return value

    @clock_multiplier.setter
    def clock_multiplier(self, value):
        from numpy import rint

        value = int(rint(value))
        if 1 <= value <= 32:
            self.clk_mul_count = 2 * value - 1
        else:
            warning("%r must be in range 1 to 32.")

    clk_mul_count = alias_property("registers.clk_mul.count")

    @monitored_property
    def P0t(self, hsct, p0_div_1kHz_count):
        """Single-bunch clock period (ca. 3.6us)"""
        from numpy import nan

        try:
            value = hsct / p0_div_1kHz_count
        except ZeroDivisionError:
            value = nan
        return value

    @P0t.setter
    def P0t(self, value):
        from numpy import rint

        try:
            self.p0_div_1kHz_count = rint(self.hsct / value)
        except ZeroDivisionError:
            pass

    p0_div_1kHz_count = alias_property("registers.p0_div_1kHz.count")

    @monitored_property
    def hsct(self, bct, clk_88Hz_div_1kHz_count):
        """High-speed chopper rotation period (ca. 1 ms)"""
        return bct * 4 * clk_88Hz_div_1kHz_count

    @hsct.setter
    def hsct(self, value):
        from numpy import rint

        try:
            self.clk_88Hz_div_1kHz_count = rint(value / (self.bct * 4))
        except ZeroDivisionError:
            pass

    clk_88Hz_div_1kHz_count = alias_property("registers.clk_88Hz_div_1kHz.count")

    def get_hlct(self):
        """X-ray pulse repetition period.
    Selected by the heatload chopper.
    Depends on the number of slots in the X-ray beam path:
    period = hlct / 12 * number of slots
    (ca 12 ms with one slot) Number of slots: 1,4,12"""
        return self.hsct * self.hlc_div

    def set_hlct(self, value):
        from numpy import rint

        try:
            self.hlc_div = rint(value / self.hsct)
        except ZeroDivisionError:
            pass

    hlct = property(get_hlct, set_hlct)

    hlc_div = Parameter("hlc_div", 12)

    def get_hlc_nslots(self):
        """Number of slots of the heatload chopper in the X-ray beam"""
        from numpy import rint, nan

        try:
            nslots = rint(12.0 / self.hlc_div)
        except ZeroDivisionError:
            nslots = nan
        return nslots

    def set_hlc_nslots(self, nslots):
        from numpy import rint

        try:
            self.hlc_div = rint(12.0 / nslots)
        except ZeroDivisionError:
            pass

    hlc_nslots = property(get_hlc_nslots, set_hlc_nslots)

    def get_nslt(self):
        """ns laser flash lamp period (ca. 100 ms)"""
        return self.hsct * self.nsl_div

    def set_nslt(self, value):
        from numpy import rint

        self.nsl_div = rint(value / self.hsct)

    nslt = property(get_nslt, set_nslt)

    nsl_div = Parameter("nsl_div", 96)

    clk_shift_stepsize = Parameter("clk_shift_stepsize", 8.594e-12)

    def reset_dcm(self):
        """Reinitialize digital clock manager"""
        from time import sleep

        self.registers.clk_shift_reset.count = 1
        sleep(0.2)
        self.registers.clk_shift_reset.count = 0

    xd = Parameter("xd", 0.000985971429)  # X-ray pulse timing

    delay = variable_property("delay", stepsize=1e-12)  # Ps laser to X-ray delay

    xdet_on = Parameter("xdet_on", False)  # Read detector?
    laser_on = Parameter("laser_on", False)  # Pump sample?
    ms_on = Parameter("ms_on", False)  # Probe sample?
    trans_on = Parameter("trans_on", False)  # Translate sample?

    waitt = variable_property("waitt", stepsize="hlct")
    npulses = Parameter("npulses", 1)  # pulses per burst
    burst_waitt = variable_property("burst_waitt", stepsize="hlct")
    burst_delay = variable_property("burst_delay", stepsize="hlct")
    bursts_per_image = Parameter("bursts_per_image", 1)
    sequence = Parameter(
        "sequence", ""
    )  # more flexible replacement for bursts_per_image
    acquisition_sequence = Parameter(
        "acquisition_sequence", ""
    )  # used when acquiring data
    temp_inc_on = Parameter("temp_inc_on", False)
    image_number_inc_on = Parameter("image_number_inc_on", False)
    pass_number_inc_on = Parameter("pass_number_inc_on", False)

    phase_matching_period = Parameter("phase_matching_period", 1)

    lxd = ps_lxd = delay  # For backward compatibility
    laseron = laser_on  # For backward compatibility

    # For sample translation stage
    translate_mode = Parameter("translate_mode", "")
    transc = Parameter("transc", 0)
    pump_on = Parameter("pump_on", False)

    transon = variable_property("trans.on", stepsize=1)  # For backward compatibility
    mson = variable_property("ms.on", stepsize=1)  # For backward compatibility
    xoscton = variable_property("xosct.on", stepsize=1)  # For backward compatibility

    # Ps oscillator coarse delay [0-11.2 ns, step 2.8 ns]
    psod1 = timing_register_property("psod1", stepsize="bct", max_count=4)
    # Ps oscillator fine delay [0-2.8ns, step 9 ps]
    psod2 = timing_register_property("psod2", stepsize="clk_shift_stepsize")
    # Ps oscillator coarse delay [0-7.1 ns, step 7.1 ns]
    psod3 = timing_register_property("psod3", stepsize="bct*2.5", max_count=1)

    # P0 fine tune delay [0-8.4ns,step 2.8ns]
    p0fd = timing_register_property("p0fd", stepsize="bct")
    # P0 delay [0-5.8us,step 11ns]
    p0d = timing_register_property("p0d", stepsize="bct*4")

    # P0 actual fine delay [0-8.4ns,step 2.8ns,read-only]
    p0afd = timing_register_property("p0afd", stepsize="bct")
    # P0 actual delay [0-3.6us,step 11ns,read-only]
    p0ad = timing_register_property("p0ad", stepsize="bct*4")

    # P0 fine tune delay [0-8.4ns,step 2.8ns]
    p0fd2 = timing_register_property("p0fd2", stepsize="bct")
    # P0 delay 2 [0-5.8us,step 11ns]
    p0d2 = timing_register_property("p0d2", stepsize="bct*4")

    @property
    def p0_shift(self):
        from timing_system_p0_shift import timing_system_p0_shift
        return timing_system_p0_shift(self)

    # Ps laser delay 1 [0-20.47ns,step 10ps] (phase of seed beam)
    psd1 = timing_register_property("psd1", stepsize=10.048e-12)
    # The "psd1.offset" parameter needs to be determined empirically and changes with
    # the length of the cables that route the clock and trigger signals
    # from the FPGA to the Lok-to-Clock and Spitfire TDG.
    # tweak psd1.offset on both directions, until the amplifier
    # output pulse timing toggles between two delays, spaced by 14.2 ns, with equal
    # probability. Then set psd1.offset to the midpoint of the two values.
    # psd1.offset = 1.2630336e-08 # Schotte, Mar 3, 2015

    # Heatload chopper nominal delay
    hlcnd = timing_register_property("hlcnd", stepsize="bct*4")
    # This offset determines when the heatload chopper opening window is centered
    # on the high speed chopper opening window.
    # At 82.3 Hz the opening window should be centered on the 12th high speed
    # chopper transmission after the FPGA t=0.
    # hlcnd.offset = -0.0056959639810284885 # Schotte, 4 Mar 2015, 82-Hz mode

    # Heatload chopper transient delay
    hlctd = timing_register_property("hlctd", stepsize="bct*4")
    # Heatload chopper actual delay, read only [0-24ms,step 12ns]
    hlcad = timing_register_property("hlcad", stepsize="bct*4")

    configuration_name = Parameter("configuration_name", "BioCARS")

    def save_configuration(self):
        self.configuration.save()

    def load_configuration(self):
        self.configuration.load()

    saving_configuration = thread_property(save_configuration)
    loading_configuration = thread_property(load_configuration)

    @property
    def configuration(self):
        return self.Configuration(self, self.configuration_name)

    @property
    def configuration_names(self):
        return configuration_names()

    high_speed_chopper = Parameter("chopper", "Julich")
    high_speed_chopper_choices = "Julich"

    @property
    def high_speed_chopper_phase(self):
        return self.channels.hsc.delay

    cache = 0  # for backward compatibility
    cache_timeout = 0  # for backward compatibility
    use_CA = True  # for backward compatibility

    @property
    def sequencer(self):
        from timing_system_sequencer import timing_system_sequencer
        return timing_system_sequencer(self.name)

    @property
    def composer(self):
        from timing_system_composer import timing_system_composer
        return timing_system_composer(self.name)

    @property
    def acquisition(self):
        from timing_system_acquisition import timing_system_acquisition
        return timing_system_acquisition(self)

    @property
    def delay_scan(self):
        from timing_system_delay_scan import timing_system_delay_scan
        return timing_system_delay_scan(self)

    @property
    def laser_on_scan(self):
        from timing_system_laser_on_scan import timing_system_laser_on_scan
        return timing_system_laser_on_scan(self)


def register_property_value(value, default_value, dtype, report_name=""):
    if value is None:
        debug(f"{report_name}: Defaulting to {default_value!r}")
        value = default_value
    else:
        if is_int(value) and value < 0:
            value = int(value) + 0x100000000
        if dtype is None and default_value is not None:
            dtype = type(default_value)
        if dtype is not None:
            try:
                converted_value = dtype(value)
            except Exception as x:
                debug(f"{report_name}: {dtype.__name__}({value!r}): {x}. Defaulting to {default_value!r}")
                value = default_value
            else:
                value = converted_value
    # debug("%r: %.80r" % (PV_name,value))
    return value


def parameter_value(value, default_value, report_name):
    if value is None:
        debug(f"{report_name}: Defaulting to {default_value!r}")
        value = default_value
    else:
        from numpy import nan, inf  # noqa - needed for eval
        try:
            value = type(default_value)(eval(value))
        except Exception as x:
            if value != "":
                debug(f"{report_name}: {type(default_value).__name__}({value}): {x}")
            value = default_value
    return value


def parameter_PV_value(value, default_value):
    from same import same
    str_value = repr(value)
    if default_value is not None and same(value, default_value):
        str_value = ""  # deletes property when passed to "set_property"
    return str_value


def configuration_names():
    """All saved settings"""
    from DB import dbdir

    names = dbdir("timing_system_configurations")
    return names


def unsigned_int(value):
    """Convert from signed to unsigned int
  (Channel Access does not support unsigned int)"""
    if is_int(value) and value < 0:
        value = value + 0x100000000
    return value


def is_int(value):
    return "int" in str(type(value))


# default_timing_system = Timing_System("BioCARS")  # for backward compatibility
# parameters = Parameters(default_timing_system)  # Needed ?

if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from time import sleep

    name = "BioCARS"
    # name = "LaserLab"
    # name = "TestBench"

    self = timing_system(name)
    print('self.prefix = %r' % self.prefix)
    print('self.ip_address = %r' % self.ip_address)
    print('')

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        info(f'event = {event}')

    property_names = [
        "names",
    ]
    for property_name in property_names:
        _reference(self.channels, property_name).monitors.add(report)
