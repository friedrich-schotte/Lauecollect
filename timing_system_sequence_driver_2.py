"""
Author: Friedrich Schotte
Date created: 2021-10-12
Date last modified: 2022-08-12
Revision comment: Fixed: imports
"""
__version__ = "2.0.1"

import logging
from logging import exception


class Timing_System_Sequence_Driver(object):
    def __init__(self, timing_system, delay=None, **kwargs):
        self.timing_system = timing_system
        from collections import OrderedDict
        self.__parameters__ = OrderedDict()
        if delay is not None:
            self.delay = delay
        for name in kwargs:
            value = kwargs[name]
            if value is not None:
                self.setattr(name, value)
        # self.set_defaults()

    def __repr__(self):
        p = self.ordered_parameters(self.__parameters__)
        parameter_list = [f"{self.timing_system}"]
        parameter_list += [f"{key}={p[key]!r}" for key in p]
        parameter_str = ", ".join(parameter_list)
        s = f"{self.class_name}({parameter_str})"
        return s

    def __deepcopy__(self, memo):
        from copy import deepcopy
        copy = type(self)(self.timing_system)
        memo[id(self)] = copy
        copy.__parameters__ = deepcopy(self.__parameters__, memo)
        return copy

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def composer(self):
        return self.timing_system.composer

    @property
    def sequencer(self):
        return self.timing_system.sequencer

    def set_defaults(self):
        for name in self.properties:
            if name not in self.__parameters__:
                self.__parameters__[name] = self.composer.get_default(name)

    def update(self, sequence):
        """Copy parameters from another Sequence object
        sequence: another Sequence object"""
        self.__parameters__.update(sequence.__parameters__)

    def __getattr__(self, name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("Sequence object has no attribute %r" % name)
        if name.startswith("_") and name.endswith("_"):
            raise AttributeError("Sequence object has no attribute %r" % name)
        # debug("%r" % name)
        if name in self.__parameters__:
            value = self.__parameters__[name]
        else:
            value = self.composer.get_default(name)
        # debug("%r: %r" % (name, value))
        return value

    def __setattr__(self, name, value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        elif name == "timing_system":
            object.__setattr__(self, name, value)
        else:
            try:
                object.__getattribute__(self, name)
                object.__setattr__(self, name, value)
            except AttributeError:
                self.setattr(name, value)

    def setattr(self, name, value):
        # self.__parameters__[name] = value
        parameters = dict([(name, value)])
        parameters = self.normalize(parameters, self.composer)
        self.__parameters__.update(parameters)

    @staticmethod
    def normalize(par, composer):
        """translate parameters dictionary"""
        from collections import OrderedDict
        parameters = OrderedDict()
        for name in par:
            value = par[name]
            if name == "delay":
                from numpy import isnan
                if isnan(value):
                    parameters["laser_on"] = False
                # Philip Anfinrud, 2018-10-01: integer value means nominal delay
                # for logging purposes in multiples of 1 ms clock ticks.
                elif value == int(value) and value >= 48:
                    parameters["nom_delay"] = value * composer.tick_period
                else:
                    parameters["delay"] = value
            elif name in ["S", "SEQ", "enable"]:
                # Philip Anfinrud, 2018-10-01: "Sequence Configuration"
                # 1010: xdet_on=1, laser_on=0, ms_on=1, trans_on=0
                bits = {0: "xdet_on", 1: "laser_on", 2: "ms_on", 3: "trans_on"}
                for i in bits:
                    name = bits[i]
                    if len(value) > i:
                        try:
                            val = int(value[i])
                        except (ValueError, TypeError, ArithmeticError):
                            val = composer.get_default(name)
                        parameters[name] = val
                # if len(value) >0: parameters["xdet_on"]  = int(value[0])
                # if len(value) >1: parameters["laser_on"] = int(value[1])
                # if len(value) >2: parameters["ms_on"]    = int(value[2])
                # if len(value) >3: parameters["trans_on"] = int(value[3])
            # Philip Anfinrud, 2018-10-01...2018-10-05: "Player-Piano Modes"
            elif name in ["PLP", "PP", "pp"]:
                parameters["mode"] = value
            # Philip Anfinrud, 2018-09-28: circulate liquid sample
            elif name in ["circulate"]:
                parameters["pump_on"] = value
            # Philip Anfinrud, 2018-10-04...2018-10-05: short for of "acquire"
            elif name in ["acq", "image"]:
                parameters["acquire"] = value
            elif name in ["laser", "pump"]:
                parameters["laser_on"] = value
            elif name in ["probe", "xray", "xray_on"]:
                parameters["ms_on"] = value
            elif name in ["trans"]:
                parameters["trans_on"] = value
            elif name in ["xdet"]:
                parameters["xdet_on"] = value
            else:
                parameters[name] = value
        return parameters

    @property
    def tick_period(self):
        T = self.composer.tick_period
        # T = 0.0010126898793523787
        # T = 0.0010182857142857144
        return T

    @property
    def values(self):
        """Values of all parameters as tuple"""
        return tuple(self.__parameters__.values())

    @property
    def packet_description(self):
        """Binary data and descriptive string as tuple"""
        packet, description = self.composer.sequencer_packet(self)
        return packet, description

    @property
    def register_specs(self):
        """Register objects and count arrays as tuple"""
        return self.composer.register_specs(self)

    @property
    def description(self):
        """The parameters for generating a packet represented as text string."""
        description = ""
        description += "delay=%.3g," % self.delay
        description += "nom_delay=%.3g," % self.nom_delay
        description += "laser_on=%r," % self.laser_on
        description += "ms_on=%r," % self.ms_on
        description += "pump_on=%r," % self.pump_on
        description += "xdet_on=%r," % self.xdet_on
        description += "trans_on=%r," % self.trans_on
        description += "pass_number=%r," % self.pass_number
        description += "image_number_inc=%r," % self.image_number_inc
        description += "pass_number_inc=%r," % self.pass_number_inc
        description += "acquiring=%r," % self.acquiring
        description += "mode_number=%r," % self.mode_number
        description += "N=%r," % self.N
        description += "period=%r," % self.period
        description += "transd=%r," % self.transd
        description += "dt=%r," % self.dt
        description += "t0=%r," % self.t0
        description += "z=%r," % self.z

        transc = self.composer.trigger_code_of(
            self.mode_number,
            self.following_sequence.pump_on,
            self.following_sequence.delay,
            self.z,
        )
        description += "transc=%r," % transc

        description += "preceding_sequence.delay=%.3g," % self.preceding_sequence.delay

        description += self.parameter_description
        return description

    descriptor = description

    @property
    def parameter_description(self):
        if hasattr(self.sequences, "parameter_description"):
            description = self.sequences.parameter_description
        else:
            if not self.__parameter_description__:
                self.__parameter_description__ = self.composer.parameter_description
            return self.__parameter_description__
        return description

    __parameter_description__ = ""

    @property
    def id(self):
        """Binary data and descriptive string as tuple"""
        from timing_system_sequencer_driver_9 import get_hash
        ID = get_hash(self.description)
        return ID

    @property
    def packet_representation(self):
        """Sequence data as formatted text"""
        from timing_system_sequencer_driver_9 import packet_representation
        return packet_representation(self.data)

    @property
    def is_cached(self):
        """Packet is generated"""
        is_cached = len(self.cached_data) > 0
        return is_cached

    @property
    def data(self):
        """Binary sequence data"""
        data = b""
        # noinspection PyBroadException
        try:
            data = self.cached_data
            if len(data) == 0:
                data = self.generated_data
                self.cached_data = data
        except Exception:
            logging.exception("")
        return data

    packet = packet_data = data

    def get_cached_data(self):
        data = self.sequencer.cache_get(self.description)
        return data

    def set_cached_data(self, data):
        self.sequencer.cache_set(self.description, data)

    cached_data = property(get_cached_data, set_cached_data)

    @property
    def generated_data(self):
        data = b""
        # noinspection PyBroadException
        try:
            from timing_system_sequencer_driver_9 import sequencer_packet
            data = sequencer_packet(self.register_specs, self.descriptor)
        except Exception:
            exception("")
        return data

    @classmethod
    def ordered_parameters(cls, parameters):
        from collections import OrderedDict
        ordered_parameters = OrderedDict()
        for name in cls.order:
            if name in parameters:
                ordered_parameters[name] = parameters[name]
        for name in parameters:
            if name not in cls.order:
                ordered_parameters[name] = parameters[name]
        return ordered_parameters

    order = [
        "delay",
        "nom_delay",
        "xdet_on",
        "laser_on",
        "ms_on",
        "trans_on",
        "pump_on",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",
    ]

    properties = [
        "delay",
        # "nom_delay",
        "xdet_on",
        "laser_on",
        "ms_on",
        "trans_on",
        "pump_on",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",
        "pass_number",
        "mode_number",
        "N",
        "period",
        "transd",
        "dt",
        "t0",
        "z",
    ]

    @property
    def nom_delay(self):
        from numpy import isnan
        if "nom_delay" in self.__parameters__ and not isnan(self.__parameters__["nom_delay"]):
            return self.__parameters__["nom_delay"]
        else:
            return self.delay

    @property
    def sequences(self):
        """Which list of sequences is this sequence part of?"""
        if self.__sequences__ is not None:
            return self.__sequences__
        else:
            return [self]

    @sequences.setter
    def sequences(self, value):
        self.__sequences__ = value

    __sequences__ = None

    # At which place in the list of sequences it belongs to is this sequence?
    count = 0

    @property
    def following_sequence(self):
        return self.sequences[(self.count + 1) % len(self.sequences)]

    @property
    def preceding_sequence(self):
        return self.sequences[(self.count - 1) % len(self.sequences)]


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = Timing_System_Sequence_Driver(timing_system, delay=1e-9)
