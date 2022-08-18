"""
Author: Friedrich Schotte
Date created: 2015-05-27
Date last modified: 2022-07-31
Revision comment:
"""
__version__ = "6.0"
__generator_version__ = "5.6.6"

import logging
from traceback import format_exc
import numpy
from numpy import nan

from db_property import db_property
from reference import reference
from monitored_property import monitored_property
from alias_property import alias_property
from thread_property_2 import thread_property
from cached_function import cached_function

numpy.seterr(invalid="ignore", divide="ignore")  # Turn off IEEE-754 warnings


def sequence_property(name, default_value=None, dtype=None):
    def calculate(self, descriptor):
        if default_value is None and dtype is None:
            my_default_value = self.get_default(name)
        else:
            my_default_value = default_value
        if my_default_value is None:
            from numpy import nan
            my_default_value = nan
        if dtype is not None:
            my_default_value = dtype()
        value = property_value(descriptor, name, my_default_value, dtype)
        return value

    def fset(self, value):
        self.set_default(name, value)
        self.update_later = True

    def inputs(self):
        return [reference(self.sequencer, "descriptor")]

    property_object = monitored_property(
        calculate=calculate,
        fset=fset,
        inputs=inputs,
    )
    return property_object


def property_value(property_string, name, default_value=nan, dtype=None):
    """Extract a value from a comma-separated list
    property_string: comma separated list
    e.g. 'mode=Stepping-48,delay=0.0316,laser_on=True,count=6'
    name: e.g. 'mode','delay','laser_on','count'
    default_value: e.g. ''
    dtype: data type
    """
    if dtype is None:
        dtype = type(default_value)
    for record in property_string.split(","):
        parts = record.split("=")
        key = parts[0]
        if key != name:
            continue
        if len(parts) < 2:
            return default_value
        value = parts[1]
        # noinspection PyBroadException
        try:
            return dtype(eval(value))
        except Exception:
            return default_value
    return default_value


@cached_function()
def timing_system_composer_driver(timing_system):
    return Timing_System_Composer_Driver(timing_system)


class Timing_System_Composer_Driver(object):
    def __init__(self, timing_system):
        self.timing_system = timing_system

        # To suppress "Instance attribute ... defined outside __init__"
        self.update_later = False

    def __repr__(self):
        return f"{self.timing_system}.composer"

    timing_system = None

    @property
    def name(self):
        return self.timing_system.domain_name

    def Sequence(self, delay=None, **kwargs):
        return self.Sequences(delay=delay, **kwargs)[0]

    def Sequences(self, delay=None, sequences=None, **kwargs):
        from timing_system_sequences_driver_2 import Sequences
        return Sequences(self.timing_system, delay=delay, sequences=sequences, **kwargs)

    @property
    def db_name(self):
        return self.timing_system.db_name

    @property
    def sequencer(self):
        return self.timing_system.sequencer

    mode_number = sequence_property("mode_number")
    # Packet length in 987-Hz cycles
    period = sequence_property("period")
    # Number of X-ray pulses
    N = sequence_property("N")
    # X-ray pulse repetition period, in 987-Hz cycles
    dt = sequence_property("dt")
    # Trigger rising edge to first X-ray pulse, in 987-Hz cycles
    t0 = sequence_property("t0")
    # Sample translation trigger delay
    transd = sequence_property("transd")
    # Laser focusing optics translation stage setting to compensate
    # moving sample lateral offset as function of pump-probe delay,
    # when collecting in "Flythru" mode.
    z = sequence_property("z")

    default_values = {
        "mode_number": 0,
        "period": 264,
        "N": 40,
        "dt": 4,
        "t0": 100,
        "transd": 17,
        "z": 1,
    }

    def command_value(self, name):
        value = self.parameter(name, self.default_values[name])
        # logging.debug(f"{name}={value!r}")
        return value

    def set_command_value(self, name, value):
        logging.debug(f"{name}={value!r}")
        self.set_parameter(name, value)

    def parameter(self, name, default_value):
        from DB import db
        return db(f"{self.db_name}.{name}", default_value)

    def set_parameter(self, name, value):
        from DB import dbset
        dbset(f"{self.db_name}.{name}", value)

    @thread_property
    def update_later(self):
        from time import sleep
        sleep(0.5)
        self.update()

    def get_default(self, name):
        """Default value for the  parameter given by name.
        name: "delay","laser_on","ms_on","pump_on","trans_on"
        "image_number_inc","pass_number_inc",
        "xdet_on"
        """
        if name in self.default_values:
            value = self.command_value(name)
        else:
            value = self.sequencer.get_default(name)
        return value

    def set_default(self, name, value):
        """Default value for the  parameter given by name.
        name: "delay","laser_on","ms_on","pump_on","trans_on"
        "image_number_inc","pass_number_inc"
        """
        if name in self.default_values:
            self.set_command_value(name, value)
        else:
            self.sequencer.set_default(name, value, update=False)

    delay = sequence_property("delay")
    nom_delay = sequence_property("nom_delay", default_value=nan)
    trigger_period_in_1kHz_cycles = sequence_property("period", dtype=int)
    laser_on = sequence_property("laser_on")
    ms_on = sequence_property("ms_on")
    pump_on = sequence_property("pump_on")
    xdet_on = sequence_property("xdet_on")
    trans_on = sequence_property("trans_on")
    image_number_inc = sequence_property("image_number_inc")
    pass_number_inc = sequence_property("pass_number_inc")
    trigger_code = sequence_property("transc", dtype=int)
    generator = sequence_property("generator", default_value="")
    generator_version = sequence_property("generator_version", default_value="")
    timing_sequence_version = sequence_property("timing_sequence_version", default_value="")

    mson = ms_on  # for backward compatibility
    xray_on = ms_on  # for backward compatibility
    xray_shutter_enabled = ms_on  # for backward compatibility
    pumpA_enabled = pump_on  # for backward compatibility
    pumpon = pump_on  # for backward compatibility
    transc = trigger_code  # for backward compatibility

    mode = alias_property("timing_modes.value")

    modes = alias_property("timing_modes.values")

    @property
    def timing_modes(self):
        from configuration_driver import configuration_driver
        return configuration_driver(self.timing_modes_configuration_name)

    @property
    def timing_modes_configuration_name(self):
        configuration_name = self.name + ".timing_modes"
        return configuration_name

    @monitored_property
    def sequence(self, default_sequence):
        return default_sequence

    @sequence.setter
    def sequence(self, value):
        self.default_sequence = value
        self.update_later = True

    default_sequence = db_property("sequence", "")
    acquisition_sequence = db_property("acquisition_sequence", "")  # "sequence" parameter used during data acquisition

    def sequencer_packet(self, sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        if self.sequencer.cache_enabled:
            method = self.sequencer_packet_cached
        else:
            method = self.sequencer_packet_generate
        packet, description = method(sequence)
        return packet, description

    def sequencer_packet_cached(self, sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        description = sequence.description

        packet = self.sequencer.cache_get(description)
        if len(packet) == 0:
            packet, description = self.sequencer_packet_generate(sequence)
            self.sequencer.cache_set(description, packet)
        return packet, description

    def sequencer_packet_generate(self, sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        from timing_system_sequencer_driver_9 import sequencer_packet
        logging.info("Generating packet...")
        description = sequence.description
        register_specs = self.register_specs(sequence)
        data = sequencer_packet(register_specs, description)
        return data, description

    def register_specs(self, sequence):
        """list of registers and lists of counts
        """
        from timing_system_register_spec import timing_system_register_spec as spec
        from numpy import isnan, arange, rint, floor, array
        from sparse_array import sparse_array

        T_base = self.timing_system.clock.hsct
        n = sequence.period

        # The high-speed chopper determines the X-ray pulse timing.
        # xd = -self.timing_system.channels.hsc.delay.offset
        xd = self.xd
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g. super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-bunch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        # phase = self.timing_system.high_speed_chopper_phase.value
        # if 100e-9 < abs(phase) < 4e-6: xd += phase

        it_xray = sequence.t0 + arange(0, sequence.N * sequence.dt, sequence.dt)
        t_xray = it_xray * T_base + xd
        t_laser = t_xray - sequence.delay

        registers = self.timing_system.registers

        specs = []

        if not isnan(sequence.pass_number):
            pass_number_counts = sparse_array(n, sequence.pass_number)
            specs.append(spec(registers.pass_number, pass_number_counts, "set,report"))
        elif not sequence.pass_number_inc:
            pass_number_counts = sparse_array(n, 0)
            specs.append(spec(registers.pass_number, pass_number_counts, "set,report"))
        if sequence.image_number_inc:
            image_number_inc_counts = sparse_array(n)
            image_number_inc_counts[n - 1] = 1
            specs.append(spec(registers.image_number, image_number_inc_counts, "inc,report"))
        if sequence.pass_number_inc:
            pass_inc_counts = sparse_array(n, 0)
            pass_inc_counts[0] = sequence.pass_number_inc
            specs.append(spec(registers.pass_number, pass_inc_counts, "inc,report"))
        if sequence.ms_on:
            pulses_counts = sparse_array(n, 0)
            pulses_inc_counts = sparse_array(n)
            pulses_inc_counts[it_xray] = 1
            specs.append(spec(registers.pulses, pulses_inc_counts, "inc,report"))
            specs.append(spec(registers.pulses, pulses_counts, "set,report"))
        # Indicate whether data acquisition is running.
        acquiring_counts = sparse_array(n, sequence.acquiring)
        specs.append(spec(registers.acquiring, acquiring_counts, "set,report"))

        # Channel configuration-based sequence generation
        for i_channel in range(0, len(self.timing_system.channels)):
            channel = self.timing_system.channels[i_channel]

            if channel.PP_enabled:
                if channel.special == "trans":  # Sample translation trigger
                    # Transmit the mode number to the motion controller as bit pattern.
                    # 2 or 3 clock cycles start, 2 or 3 clock cycles per bit.
                    bit_length = int(rint(channel.pulse_length / T_base))
                    transc = self.trigger_code_of(
                        sequence.mode_number,
                        sequence.following_sequence.pump_on,
                        sequence.following_sequence.delay,
                        sequence.z,
                    )
                    it_trans = list(range(0, bit_length))
                    for i in range(0, 32):
                        if (transc >> i) & 1:
                            it_trans += list(range(bit_length * (i + 1), bit_length * (i + 2)))
                    it_trans = array(it_trans)
                    it_trans += sequence.transd
                    it_trans %= sequence.period
                    trans_state_counts = sparse_array(n)
                    trans_state_counts[it_trans] = 1
                    specs.append(spec(channel.state, trans_state_counts, "set"))
                elif channel.special == "pso":  # Picosecond oscillator reference clock
                    # Picosecond oscillator reference clock (course, 7.1 ns resolution)
                    pso_period = 5 * self.timing_system.clock.bct
                    pso_coarse_step = registers.psod3.stepsize
                    pst_dial_values = t_laser - self.timing_system.channels.pst.offset
                    pst_dial = pst_dial_values[0] % T_base
                    pso_dial = self.timing_system.registers.psod3.dial_from_user(pst_dial) % pso_period
                    psod3_dial = floor(pso_dial / pso_coarse_step) * pso_coarse_step
                    psod3_count = self.timing_system.registers.psod3.count_from_dial(psod3_dial)
                    psod3_counts = sparse_array(n, psod3_count)
                    # Picosecond oscillator reference clock (fine, 9 ps resolution)
                    psod2_dial = pso_dial % pso_coarse_step
                    clk_shift_count = self.timing_system.registers.psod2.count_from_dial(psod2_dial)
                    psod2_counts = sparse_array(n, clk_shift_count)
                    specs.append(spec(registers.psod3, psod3_counts, "set"))
                    specs.append(spec(registers.psod2, psod2_counts, "set"))
                elif channel.special == "nsf":  # Nanosecond laser flash lamp trigger
                    nsf_N_period = 48  # 20 Hz operation (10 Hz would be 96 counts)
                    T_nsf = nsf_N_period * T_base  # flash lamp trigger period
                    N_nsf = n / nsf_N_period  # number of flash lamp triggers per image
                    t_nsf0 = (t_laser[0] + channel.offset_sign * channel.offset) % T_nsf  # first trigger
                    t_nsf = t_nsf0 + arange(0, N_nsf) * T_nsf
                    # Abrupt timing jumps at the end of an image might cause the ns laser
                    # to trip. Make sure that no two trigger pulses arrive within less
                    # than 80% of the nominal period.
                    preceding_t_laser = t_xray - sequence.preceding_sequence.delay
                    preceding_t_nsf0 = (preceding_t_laser[0] - channel.offset_sign * channel.offset) % T_nsf
                    preceding_t_nsf = preceding_t_nsf0 + arange(0, N_nsf) * T_nsf
                    preceding_t_nsf -= n * T_base
                    if len(t_nsf) > 0 and t_nsf[0] - preceding_t_nsf[-1] < 0.80 * T_nsf:
                        t_nsf = t_nsf[1:]
                    nsf_delay_dial = t_nsf[0] % T_base if len(t_nsf) > 0 else 0
                    nsf_count = channel.count_from_dial(nsf_delay_dial)
                    nsf_delay_counts = sparse_array(n, nsf_count)
                    it_nsf = floor(t_nsf / T_base).astype(int)
                    nsf_enable_counts = sparse_array(n)
                    nsf_enable_counts[it_nsf] = 1
                    specs.append(spec(channel.delay, nsf_delay_counts, "set"))
                    specs.append(spec(channel.enable, nsf_enable_counts, "set"))
                else:
                    try:
                        specs += self.channel_register_specs(i_channel, sequence)
                    except Exception as msg:
                        logging.error(f"Channel {i_channel!r}: {msg}\n{format_exc()}")

        return specs

    def channel_register_specs(self, i_channel, sequence):
        """list of registers and lists of counts
        i: channel number (0-based)
        """
        from timing_system_register_spec import timing_system_register_spec as spec
        channel = self.timing_system.channels[i_channel]

        specs = []

        if channel.PP_enabled:
            from numpy import isnan, arange, rint, floor, cumsum, \
                clip, concatenate, array, sort
            from sparse_array import sparse_array

            T_base = self.timing_system.clock.hsct
            n = sequence.period
            T = n * T_base  # packet period

            # The high-speed chopper determines the X-ray pulse timing. 
            # xd = -self.timing_system.channels.hsc.delay.offset
            xd = self.xd
            # If the chopper timing shift is more than 100 ns,
            # assume the chopper selects a different bunch with a different timing.
            # (e.g. super bunch versus single bunch)
            # However, if the time shift is more than 4 us, assume the tunnel
            # 1-bunch selection mode is used so the transmitted X-ray pulse
            # arrives at nominally t=0.
            # phase = self.timing_system.high_speed_chopper_phase.value
            # if 100e-9 < abs(phase) < 4e-6: xd += phase

            it_xray = sequence.t0 + arange(0, sequence.N * sequence.dt, sequence.dt)

            t_xray = it_xray * T_base + xd
            t_laser = t_xray - sequence.delay

            t_xray = sort(t_xray % T)
            t_laser = sort(t_laser % T)

            if channel.gated == "pump":
                on = sequence.laser_on
            elif channel.gated == "probe":
                on = sequence.ms_on
            elif channel.gated == "detector":
                on = sequence.xdet_on
            elif channel.gated == "trans":
                on = sequence.trans_on
            else:
                on = True

            if channel.timed == "pump":
                t_ref = t_laser
            elif channel.timed == "pump-probe":
                t_ref = t_laser
            elif channel.timed == "pump+probe":
                t_ref = t_laser
            elif channel.timed == "probe":
                t_ref = t_xray
            elif channel.timed == "period":
                t_ref = array([0.0])
            else:
                t_ref = array([])

            if on and len(t_ref) > 0:
                if not isnan(channel.offset_HW):  # precision-timed sub-ms pulses
                    pulse_length = channel.pulse_length

                    if channel.timed == "pump":
                        T_on = t_laser
                        T_off = t_laser + pulse_length
                    elif channel.timed == "probe":
                        T_on = t_xray
                        T_off = t_xray + pulse_length
                    elif channel.timed == "pump-probe":
                        T_on = t_laser
                        T_off = t_xray
                        if not isnan(pulse_length):
                            T_off += pulse_length
                    elif channel.timed == "pump+probe":
                        T_on = sort(concatenate([t_laser, t_xray]))
                        T_off = T_on + pulse_length
                    elif channel.timed == "period":
                        T_on = array([0.0])
                        T_off = T_on + pulse_length
                    else:
                        T_on = array([])
                        T_off = array([])

                    offset = channel.offset_sign * channel.offset_HW
                    if not isnan(offset):
                        T_on += offset
                        T_off += offset
                        T_on = sort(T_on % T)
                        T_off = sort(T_off % T)

                    specs += self.channel_register_specs_of_T(
                            channel=channel,
                            period=sequence.period,
                            T_on=T_on,
                            T_off=T_off,
                        )

                    it_on = (floor(T_on / T_base)).astype(int)  # for trigger count

                else:  # ms-resolution multi-ms pulses
                    t0 = channel.offset
                    pulse_length = channel.pulse_length

                    if isnan(pulse_length):
                        pulse_length = 0

                    t = array([t_ref + t0, t_ref + t0 + pulse_length]).T.flatten()

                    t = self.t_special(t, channel.special)

                    N_outside = sum((t < 0) | (t >= T))
                    initial_value = 1 if N_outside % 2 == 1 else 0
                    t = t % T

                    it = clip(rint(t / T_base), 0, n - 1).astype(int)
                    it_on, it_off = it.reshape((-1, 2)).T
                    inc = sparse_array(n)
                    inc[it_on] += 1
                    inc[it_off] -= 1
                    state_counts = clip(cumsum(inc) + initial_value, 0, 1)
                    state_counts = sparse_array(state_counts)

                    specs.append(spec(channel.state, state_counts, "set"))

                if channel.counter_enabled:
                    # Increment the trigger count on the rising edge of the last
                    # trigger pulse within the measure.
                    it_last_trigger = it_on[-1:]
                    count_inc = sparse_array(n)
                    count_inc[it_last_trigger] = 1
                    specs.append(spec(channel.trig_count, count_inc, "inc,report"))
                    if sequence.acquiring:
                        specs.append(spec(channel.acq, count_inc, "set,report"))
                        specs.append(spec(channel.acq_count, count_inc, "inc,report"))
            else:
                # Force the level to be low if the channel is gated off
                specs.append(spec(channel.state, sparse_array(n), "set"))
                specs.append(spec(channel.enable, sparse_array(n), "set"))

        return specs

    def channel_register_specs_of_T(self, channel, period, T_on, T_off):
        from timing_system_register_spec import timing_system_register_spec as spec
        from numpy import rint, floor
        from sparse_array import sparse_array

        T_base = self.timing_system.clock.hsct
        n = period

        delay_counts = sparse_array(n)
        pulse_counts = sparse_array(n)
        enable_counts = sparse_array(n)
        state_counts = sparse_array(n)

        for (t_on, t_off) in zip(T_on, T_off):
            if t_on < t_off:
                it_on = int(floor(t_on / T_base))
                t1 = t_on % T_base
                dt1_max = T_base - t1
                dt1 = min(t_off - t_on, dt1_max)
                it1 = int(rint(t1 / channel.delay.stepsize))
                idt1 = int(rint(dt1 / channel.pulse.stepsize))
                if idt1 > 0:
                    state_counts[it_on] = 0
                    enable_counts[it_on] = 1
                    delay_counts[it_on] = it1
                    pulse_counts[it_on] = idt1
                it_off = int(floor(t_off / T_base))

                dt_max = T_base
                idt_max = int(rint(dt_max / channel.pulse.stepsize))
                # Mixing state and pulse logics generates a 30-ns negative
                # glitch at the last 1-ms boundary.
                # state_counts[it_on+1:it_off] = 1
                # enable_counts[it_on+1:it_off] = 0
                # delay_counts[it_on+1:it_off] = 0
                # pulse_counts[it_on+1:it_off] = 0
                state_counts[it_on + 1:it_off] = 0
                enable_counts[it_on + 1:it_off] = 1
                delay_counts[it_on + 1:it_off] = 0
                pulse_counts[it_on + 1:it_off] = idt_max

                if it_off > it_on:
                    dt2 = t_off - it_off * T_base
                    idt2 = int(rint(dt2 / channel.pulse.stepsize))
                    if idt2 > 0:
                        state_counts[it_off] = 0
                        enable_counts[it_off] = 1
                        delay_counts[it_off] = 0
                        pulse_counts[it_off] = idt2

        register_specs = [
            spec(channel.delay, delay_counts, "set"),
            spec(channel.pulse, pulse_counts, "set"),
            spec(channel.enable, enable_counts, "set"),
            spec(channel.state, state_counts, "set"),
        ]
        return register_specs

    @staticmethod
    def t_special(t, special):
        """Process time delays for channels that have special functions
        t: array of time delays in seconds for rising and falling edges,
           alternating
        special: e.g. "ms" for X-ray millisecond shutter
        """
        from numpy import array
        t_special = t
        t_rise = t[0::2]
        if special == "ms":
            if len(t) >= 2:
                if len(t_rise) >= 2:
                    burst_period = (max(t_rise) - min(t_rise)) / (len(t_rise) - 1)
                else:
                    burst_period = 0
                if 0 < burst_period < 0.024:  # Open continuously for a burst
                    t_special = array([min(t_rise), max(t_rise)])
        return t_special

    @property
    def parameter_description(self):
        """The parameters for generating a packet represented as text string."""
        description = ""
        # Calibration constants and parameters
        # description += f"high_speed_chopper_phase.value={self.timing_system.high_speed_chopper_phase.value:.12f},"
        # description += f"high_speed_chopper_phase.offset={self.timing_system.high_speed_chopper_phase.offset:.12f},"
        # description += f"hsc.delay.offset={self.timing_system.channels.hsc.delay.offset:.12f},"
        description += f"xd={self.xd:.12f},"

        # Channel configuration-based parameters
        for i_channel in range(0, len(self.timing_system.channels)):
            channel = self.timing_system.channels[i_channel]
            if channel.PP_enabled:
                if channel.special == "pso":
                    description += f"psod3.offset={self.timing_system.registers.psod3.offset:.12f},"
                elif channel.special == "trans":
                    description += f"{channel.name}.pulse_length={channel.pulse_length:.4g},"
                elif channel.special == "nsf":
                    description += f"{channel.name}.offset={channel.offset:.12f},"
                else:
                    description += self.channel_description(i_channel)

        description += f"generator={'composer'!r},"
        description += f"generator_version={__generator_version__!r},"
        import timing_system_sequencer_driver_9 as timing_system_sequencer_driver
        description += f"timing_sequence_version={timing_system_sequencer_driver.__generator_version__!r},"

        return description

    def channel_description(self, i_channel):
        """The parameters for generating a packet represented as text string."""
        description = ""
        channel = self.timing_system.channels[i_channel]
        name = channel.mnemonic if channel.mnemonic else channel.name
        description += f"{name}.special={channel.special!r},"
        description += f"{name}.offset_PP={channel.offset_PP},"
        description += f"{name}.offset_sign={channel.offset_sign},"
        description += f"{name}.pulse_length_PP={channel.pulse_length_PP},"
        description += f"{name}.offset_HW={channel.offset_HW},"
        description += f"{name}.pulse_length_HW={channel.pulse_length_HW},"
        description += f"{name}.timed={channel.timed!r},"
        description += f"{name}.gated={channel.gated!r},"
        description += f"{name}.counter_enabled={channel.counter_enabled},"
        return description

    def trigger_code_of(self, mode_number, pump_on, delay, z):
        """Byte code to be transmitted to the Ensemble motion controller
        as bit pattern
        ms_on: operate the X-ray millisecond shutter?
        pump_on: operate the peristaltic pump?
        """
        # mode: 4 bits: pump_on: 1 bit, delay 6 bits
        delay_count = self.delay_count(delay) if z else 0
        transc = (
                (int(mode_number) << 0) |
                (int(pump_on) << 4) |
                (int(delay_count) << 5)
        )
        return transc

    @staticmethod
    def delay_count(delay):
        """Count to indicate the linear translation of the laser beam on a
        logarithmic scale
        delay: delay in seconds, range 0-17.8 ms 
        Return value: integer, range 0-63"""
        from numpy import log10, rint
        delay_count = min(int(rint(8 * log10(max(delay, 10e-6) / 10e-6))), 63)
        return delay_count

    def acquisition_start(self, image_number=1):
        """To be called after 'acquire'
        image_number: 1-based integer
        """
        self.image_number = image_number - 1
        self.pass_number = 0
        self.pulses = 0
        self.sequencer.queue_sequence_count = 0
        self.sequencer.queue_repeat_count = 0
        self.sequencer.queue_active = True

    def acquisition_cancel(self):
        """End current data collection"""
        self.sequencer.queue_active = False

    def update(self):
        self.sequencer.update()

    def clear_queue(self):
        self.sequencer.clear_queue()

    image_number = alias_property("timing_system.registers.image_number.count")
    pass_number = alias_property("timing_system.registers.pass_number.count")
    pulses = alias_property("timing_system.registers.pulses.count")

    @property
    def xd(self):
        return self.default_xd

    @xd.setter
    def xd(self, value):
        if self.default_xd != value:
            self.default_xd = value
            self.update_later = True

    default_xd = db_property("xd", 0.000985971429)  # X-ray pulse timing (high-speed chopper)

    def get_hsc_delay(self):
        return self.timing_system.channels.hsc.delay.value

    def set_hsc_delay(self, value):
        self.timing_system.channels.hsc.delay.value = value

    hsc_delay = property(get_hsc_delay, set_hsc_delay)

    @monitored_property
    def scan_point_acquisition_time(self, sequence_acquisition_time, sequences_per_scan_point):
        return sequence_acquisition_time * sequences_per_scan_point

    @monitored_property
    def sequence_acquisition_time(self, period, tick_period):
        return period * tick_period

    @monitored_property
    def sequences_per_scan_point(self, acquisition_sequence):
        from expand import expand
        from list_length import list_length
        try:
            n = list_length(dict(eval(expand(acquisition_sequence)))['enable'])
        except Exception as x:
            logging.error(f"{acquisition_sequence}: {x}")
            n = 1
        return n

    tick_period = alias_property("timing_system.clock.hsct")

    def __getattr__(self, name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute was not found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"{type(self).__name__} object has no attribute {name!r}")
        alt_name = name.replace("_", ".")  # hsc_delay > hsc.delay
        if hasattr(self.timing_system, name):
            attr = getattr(self.timing_system, name)
            if hasattr(attr, "value"):
                attr = attr.value
            return attr
        elif self.hasattr(self.timing_system, alt_name):
            attr = eval(f"self.timing_system.{alt_name}")
            if hasattr(attr, "value"):
                attr = attr.value
            return attr
        elif hasattr(self.sequencer, name):
            return getattr(self.sequencer, name)
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        alt_name = name.replace("_", ".")  # hsc_delay > hsc.delay
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        elif name == "timing_system":
            object.__setattr__(self, name, value)
        elif name in self.__class__.__dict__:
            object.__setattr__(self, name, value)
        elif hasattr(self.timing_system, name):
            attr = getattr(self.timing_system, name)
            if hasattr(attr, "value"):
                attr.value = value
            else:
                setattr(self.timing_system, name, value)
        elif self.hasattr(self.timing_system, alt_name):
            attr = eval(f"self.timing_system.{alt_name}")
            if hasattr(attr, "value"):
                attr.value = value
            else:
                exec(f"self.timing_system.{alt_name} = {value!r}")
        elif hasattr(self.sequencer, name):
            setattr(self.sequencer, name, value)
        else:
            object.__setattr__(self, name, value)

    @staticmethod
    def hasattr(obj, name):  # noqa - Parameter 'obj' value is not used
        """name: e.g. 'hsc.delay'"""
        try:
            eval(f"obj.{name}")
            return True
        except (AttributeError, SyntaxError):
            return False


def sorted_lists(lists):
    from numpy import argsort
    order = argsort(lists[0])

    def reorder(a_list, order): return [a_list[i] for i in order]

    sorted_lists = [reorder(a_list, order) for a_list in lists]
    return sorted_lists


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = timing_system_composer_driver(timing_system)

    print('self.sequencer.running = True')
    print('self.update()')
    print('')
    i_channel = 1 - 1
    print('i_channel = %r-1' % (i_channel + 1))
    channel = self.timing_system.channels[i_channel]
    print('channel = %r' % channel)
    # print('sequence = self.Sequences()[0]; period = sequence.period')
    # print('self.channel_register_specs_of_T(channel,period,T_on,T_off)')
    print('sequence = self.Sequences()[0]; self.channel_register_specs(i_channel,sequence)')
    print("sequence = self.Sequences()[0]; print(sequence.packet_representation)")
    print('')

    from reference import reference as _reference
    from handler import handler as _handler

    @_handler
    def report(event): logging.info(f"event = {event!r}")

    property_names = [
        # "mode",
    ]

    for property_name in property_names:
        _reference(self, property_name).monitors.add(report)
