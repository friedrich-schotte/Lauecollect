#!/usr/bin/env python
"""Timing system channel configuration 
Author: Friedrich Schotte
Date created: 2020-06-06
Date last modified: 2022-07-14
Revision comment: Cleanup
"""
__version__ = "1.2.1"

from logging import debug, info, warning

from cached_function import cached_function


@cached_function()
def timing_system_channel_configuration(timing_system_name):
    return Timing_System_Channel_Configuration(timing_system_name)


class Timing_System_Channel_Configuration(object):
    timing_system_name = "BioCARS"

    def __init__(self, timing_system_name=None):
        if timing_system_name is not None:
            self.timing_system_name = timing_system_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.timing_system_name)

    from db_property import db_property
    show_buttons = db_property("show_buttons", True, local=True)

    @property
    def db_name(self):
        return "timing_system_channel_configuration.%s" % self.timing_system_name

    @property
    def title(self):
        return "Timing System Channel Configuration (%s)" % self.timing_system_name

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.timing_system_name)

    def update(self):
        self.timing_system.composer.update_later = True

    class Channels(object):
        def __init__(self, config):
            self.config = config

        @cached_function()
        def __getitem__(self, i):
            return self.config.Channel(self.config, i)

        def __monitor_item__(self, i, proc, *args, **kwargs):
            self[i].monitor_all(proc, *args, **kwargs)

        def __monitor_clear_item__(self, i, proc, *args, **kwargs):
            self[i].monitor_clear_all(proc, *args, **kwargs)

        def __monitors_item__(self, i):
            return self[i].monitors_all

        def __len__(self):
            return len(self.config.timing_system.channels)

        def __iter__(self):
            for i in range(0, len(self)):
                if i < len(self):
                    yield self[i]

        def __repr__(self):
            return "%s(%r)" % (type(self).__name__, self.config)

    from cached import cached

    @cached
    @property
    def channels(self):
        return self.Channels(self)

    class Channel(object):
        def __init__(self, config, count):
            self.config = config
            self.count = count

        def __repr__(self):
            return "%s(%r)" % (type(self).__name__, self.count)

        properties = [
            {"label": "PP", "name": "PP_enabled", "type": "/PP", "width": 35},
            {"label": "I/O", "name": "input.count", "type": "Out/IN", "width": 50},
            {"label": "Description", "name": "description", "width": 140},
            {"label": "Mnemonic", "name": "mnemonic", "width": 75},
            {"label": "Special\nPP", "name": "special", "width": 75},
            {"label": "Special\nHW", "name": "specout.count", "type": "/70MHz/diag1/diag2", "width": 70},
            {"label": "Offset\nHW", "name": "offset_HW", "type": "time.6", "width": 100},
            {"label": "Offset\nsign", "name": "offset_sign", "type": "float", "width": 50},
            {"label": "Duration\nHW", "name": "pulse_length_HW", "type": "time.3", "width": 75},
            {"label": "Duration\nHW reg", "name": "pulse.value", "type": "time.3", "width": 75},
            {"label": "Offset\nPP ticks", "name": "offset_PP", "type": "float", "width": 70},
            {"label": "Duration\nPP ticks", "name": "pulse_length_PP", "type": "float", "width": 70},
            {"label": "Cont.", "name": "enable.count", "type": "/Cont", "width": 45},
            {"label": "Slaved", "name": "timed", "width": 100},
            {"label": "Gated", "name": "gated", "width": 72},
            {"label": "Count\nEnabled", "name": "counter_enabled", "type": "/On", "width": 50},
            {"label": "State", "name": "output_status", "width": 60},
        ]

        def monitor_all(self, proc, *args, **kwargs):
            # warnings.warn("monitor_all() is deprecated, use reference().monitors.add()",
            #              DeprecationWarning, stacklevel=2)
            # from monitor import monitor
            # for obj, property_name in zip(self.objects, self.property_names):
            #    monitor(obj, property_name, proc, *args, **kwargs)

            from reference import reference
            from handler import handler
            for obj, property_name in zip(self.objects, self.property_names):
                reference(obj, property_name).monitors.add(handler(proc, *args, **kwargs))

        def monitor_clear_all(self, proc, *args, **kwargs):
            # warnings.warn("monitor_clear_all() is deprecated, use reference().monitors.remove()",
            #              DeprecationWarning, stacklevel=2)
            # from monitor import monitor_clear
            # for obj, property_name in zip(self.objects, self.property_names):
            #   monitor_clear(obj, property_name, proc, *args, **kwargs)

            from reference import reference
            from handler import handler
            for obj, property_name in zip(self.objects, self.property_names):
                reference(obj, property_name).monitors.remove(handler(proc, *args, **kwargs))

        @property
        def monitors_all(self):
            # warnings.warn("monitors_all() is deprecated, use reference().monitors",
            #              DeprecationWarning, stacklevel=2)
            # from monitor import monitors
            # handlers = []
            # for obj, property_name in zip(self.objects, self.property_names):
            #     handlers += monitors(obj, property_name)
            # handlers = list(set(handlers))

            from event_handlers import Event_Handlers
            from reference import reference

            handlers = Event_Handlers()
            for obj, property_name in zip(self.objects, self.property_names):
                for handler in reference(obj, property_name).monitors:
                    handlers.add(handler)

            return handlers

        @property
        def objects(self):
            return [self.obj(prop) for prop in self.properties]

        @property
        def property_names(self):
            return [property_name(prop) for prop in self.properties]

        def obj(self, prop):
            """prop = {'name': 'input.count'} -> Register('ch1_input')"""
            name = prop["name"]
            obj = self.channel
            while "." in name:
                property_name, name = name.split(".", 1)
                obj = getattr(obj, property_name)
            return obj

        @classmethod
        def label(cls, i):
            return cls.properties[i]["label"]

        @classmethod
        def width(cls, i):
            return cls.properties[i]["width"]

        def property_str(self, i):
            value = self.property_value(i)
            dtype = self.properties[i].get("type", "")
            text = self.to_str(value, dtype)
            # debug("i %r, value %r" % (i,text))
            return text

        def set_property_str(self, i, text):
            # debug("i %r, value %r" % (i,text))
            dtype = self.properties[i].get("type", "")
            value = self.from_str(text, dtype)
            self.set_property_value(i, value)
            return text

        def choices_str(self, i):
            dtype = self.properties[i].get("type", "")
            if "/" in dtype:
                choices = dtype.split("/")
            else:
                property_name = self.properties[i]["name"]
                choices_name = property_name + "_choices"
                choices = self.getattr(self.channel, choices_name, [])
                choices = [str(choice) for choice in choices]
            return choices

        def property_value(self, i):
            property_name = self.properties[i]["name"]
            value = self.getattr(self.channel, property_name)
            # debug("i %r, value %r" % (i,value))
            return value

        def set_property_value(self, i, value):
            # debug("i %r, value %r" % (i,value))
            property_name = self.properties[i]["name"]
            self.setattr(self.channel, property_name, value)

        @property
        def channel(self):
            return self.config.timing_system.channels[self.count]

        @staticmethod
        def to_str(value, dtype):
            if "/" in dtype:
                choices = dtype.split("/")
                try:
                    s = choices[int(value)]
                except (ValueError, TypeError, IndexError):
                    s = str(value)
            elif dtype == "float":
                from numpy import isnan
                try:
                    if isnan(value):
                        s = ""
                    else:
                        s = "%g" % value
                except (ValueError, TypeError):
                    s = str(value)
            elif dtype.startswith("time."):
                precision = int(dtype[len("time."):])
                from time_string import time_string
                s = time_string(value, precision).replace("off", "")
            else:
                s = str(value)
            return s

        @staticmethod
        def from_str(s, dtype):
            if "/" in dtype:
                choices = dtype.split("/")
                value = choices.index(s) if s in choices else 0
            elif dtype == "float":
                from numpy import nan
                value = nan
                try:
                    value = float(eval(s))
                except Exception as x:
                    warning("float(%r): %s" % (value, x))
            elif dtype.startswith("time."):
                from time_string import seconds
                value = seconds(s)
            else:
                value = s
            debug("Converted %r to type %r: %r" % (s, dtype, value))
            return value

        @staticmethod
        def getattr(obj, property_name, default_value=None):
            """property_name: e.g. 'input.count'"""
            for name in property_name.split(".")[0:-1]:
                obj = getattr(obj, name)
            name = property_name.split(".")[-1]
            value = getattr(obj, name, default_value)
            return value

        @staticmethod
        def setattr(obj, property_name, value):
            """property_name: e.g. 'input.count'"""
            for name in property_name.split(".")[0:-1]:
                obj = getattr(obj, name)
            name = property_name.split(".")[-1]
            setattr(obj, name, value)
            return obj

    class Table(object):
        def __init__(self, config):
            self.config = config

        def __repr__(self):
            return "%s(%r)" % (type(self).__name__, self.config)

        @property
        def n_rows(self):
            return len(self.config.channels)

        @property
        def n_cols(self):
            return len(self.config.Channel.properties)

        def col_label(self, col):
            return self.config.Channel.label(col)

        def col_width(self, col):
            return self.config.Channel.width(col)

        @staticmethod
        def row_label(row):
            return "%d" % (row + 1)

        def value(self, row, col):
            value = self.config.channels[row].property_str(col)
            # debug("row %r, col %r, value %r" % (row,col,value))
            return value

        def set_value(self, row, col, value):
            # debug("row %r, col %r, value %r" % (row,col,value))
            self.config.channels[row].set_property_str(col, value)

        def choices(self, row, col):
            choices = self.config.channels[row].choices_str(col)
            # debug("row %r, col %r, value %r" % (row,col,choices))
            return choices

        def __str__(self):
            from numpy import chararray
            cells = chararray((self.n_rows + 2, self.n_cols + 1), itemsize=40, unicode=True)

            def line(s, i):
                return (s + "\n" * i).split("\n")[i]

            cells[0, 0] = "#ch"
            for col in range(self.n_cols):
                cells[0, col + 1] = line(self.col_label(col), 0)
            cells[1, 0] = "#"
            for col in range(self.n_cols):
                cells[1, col + 1] = line(self.col_label(col), 1)
            for row in range(self.n_rows):
                cells[row + 2, 0] = self.row_label(row)
                for col in range(self.n_cols):
                    cells[row + 2, col + 1] = self.value(row, col)
            fill_char = "~"
            for col in range(cells.shape[1]):
                width = max([len(cell) for cell in cells[:, col]])
                cells[:, col] = cells[:, col].ljust(width, fill_char)
            lines = [" ".join([cell for cell in row]) for row in cells]
            text = "\n".join(lines)
            text = text.replace(fill_char, " ")
            return text

    @property
    def table(self):
        return self.Table(self)


def property_name(prop):
    """prop = {'name': 'input.count'} -> 'count' """
    return prop["name"].split(".")[-1]


if __name__ == '__main__':
    # from pdb import pm # for debugging
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler
    from reference import reference

    timing_system_name = "BioCARS"
    # timing_system_name = "LaserLab"

    self = timing_system_channel_configuration(timing_system_name)

    print("print(str(self.table))")

    def report(event):
        info(f"{event}")


    # print('reference(self,"show_buttons").monitors.add(handler(report, delay=0.1))')
    # print('reference(self,"show_buttons").monitors')
    # print('reference(self,"show_buttons").monitors.remove(handler(report, delay=0.1))')
    # print('')
    # print(f'self.show_buttons = {self.show_buttons!r}')
    # print('')
    # print('self.channels[0].monitor_all(report, delay=0.1)')
    # print('self.channels[0].monitors_all')
    # print('self.channels[0].monitor_clear_all(report, delay=0.1)')
    # print('')
    # print('from monitor import monitor_all; monitor_all(self.channels, report, delay=0.1)')
    # print('from monitor import monitors_all; monitors_all(self.channels)')
    # print('from monitor import monitor_clear_all; monitor_clear_all(self.channels, report, delay=0.1)')
    # print('')
    # print(f'self.timing_system.ch1.enable.count = {self.timing_system.ch1.enable.count!r}')
    # print(f'self.timing_system.ch1.output_status = {self.timing_system.ch1.output_status!r}')
