"""
Author: Friedrich Schotte
Date created: 2021-10-12
Date last modified: 2022-07-31
Revision comment:
"""
__version__ = "2.0"

import logging

from timing_system_sequence_driver_2 import Timing_System_Sequence_Driver as Sequence


class Sequences(object):
    def __init__(self, timing_system, delay=None, sequences=None, **kwargs):
        self.timing_system = timing_system
        from collections import OrderedDict
        self.__parameters__ = OrderedDict()
        self.set_defaults()

        acquiring = "acquiring" in kwargs and kwargs["acquiring"]
        params = self.default_parameters(acquiring)
        for name in params:
            self.setattr(name, params[name])
        if delay is not None:
            self.setattr("delay", delay)
        for name in kwargs:
            value = kwargs[name]
            if value is not None:
                self.setattr(name, value)

        if sequences is not None:
            self.set_sequences(sequences)

        self.update_parameter_description()

    def __repr__(self):
        p = Sequence.ordered_parameters(self.__parameters__)
        parameter_list = [f"{self.timing_system!r}"]
        parameter_list += [f"{key}={p[key]!r}" for key in p]
        parameter_str = ", ".join(parameter_list)
        s = f"{self.class_name}({parameter_str})"
        return s

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def composer(self):
        return self.timing_system.composer

    def set_defaults(self):
        for name in Sequence.properties:
            if name not in self.__parameters__:
                self.__parameters__[name] = self.composer.get_default(name)

    def set_sequences(self, sequences):
        keys = self.common_keys(sequences)
        from numpy import nan
        for key in keys:
            self.__parameters__[key] = [nan] * len(sequences)
        for i, sequence in enumerate(sequences):
            for key in keys:
                if key in sequence.__parameters__:
                    self.__parameters__[key][i] = sequence.__parameters__[key]

    @staticmethod
    def common_keys(sequences):
        keys = set()
        for sequence in sequences:
            keys |= set(sequence.__parameters__.keys())
        return keys

    def default_parameters(self, acquiring):
        """Dictionary"""
        from expand import expand
        if not acquiring:
            parameter_string = self.composer.sequence
        else:
            parameter_string = self.composer.acquisition_sequence
        parameter_string = expand(parameter_string)
        parameters = {}
        if parameter_string:
            try:
                parameters = dict(eval(parameter_string))
            except Exception as msg:
                logging.warning(f"{parameter_string}: {msg}")
        return parameters

    def __getattr__(self, name):
        """A property"""
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"Sequences object has no attribute {name!r}")
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name in self.__parameters__:
            value = self.__parameters__[name]
        else:
            value = self.composer.get_default(name)
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
            if not isinstance(value, str) and hasattr(value, "__len__"):
                for v in value:
                    p = Sequence.normalize(dict([(name, v)]), composer)
                    for n in p:
                        parameters[n] = []
                for v in value:
                    p = Sequence.normalize(dict([(name, v)]), composer)
                    for n in p:
                        parameters[n] += [p[n]]
            else:
                p = Sequence.normalize(dict([(name, value)]), composer)
                for n in p:
                    parameters[n] = p[n]
        return parameters

    def __len__(self):
        return self.count

    def __getitem__(self, item):
        if type(item) == slice:
            start = item.start if item.start is not None else 0
            stop = item.stop if item.stop is not None else len(self)
            step = item.step if item.step is not None else 1
            value = [self.sequence(i) for i in range(start, stop, step)]
        else:
            value = self.sequence(item)
        return value

    @property
    def sequences(self):
        """Expand to list of Sequence objects"""
        sequences = [self.sequence(count) for count in range(0, self.count)]
        return sequences

    def sequence(self, count):
        """Sequence object number *count*
        Not taking into account order of collection"""
        from collections import OrderedDict
        parameters = OrderedDict()
        for key in self.__parameters__:
            value = self.__parameters__[key]
            if not isinstance(value, str) and hasattr(value, "__len__"):
                parameters[key] = value[count % len(value)]
            else:
                parameters[key] = value
        sequence = Sequence(self.timing_system)
        for key in parameters:
            setattr(sequence, key, parameters[key])
        sequence.count = count
        sequence.sequences = self
        return sequence

    @property
    def count(self):
        """How many sequences are there?"""
        N = 1
        parameters = self.__parameters__
        for key in parameters:
            value = parameters[key]
            if not isinstance(value, str) and hasattr(value, "__len__"):
                N = max(N, len(value))
        return N

    def update_parameter_description(self):
        if not self.__parameter_description__:
            self.__parameter_description__ = self.composer.parameter_description

    @property
    def parameter_description(self):
        self.update_parameter_description()
        return self.__parameter_description__

    __parameter_description__ = ""


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = Sequences(timing_system, delay=1e-9)
