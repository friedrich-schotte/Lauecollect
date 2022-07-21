"""
Interface module for GUI
Author: Friedrich Schotte
Date created: 2020-09-21
Date last modified: 2022-07-12
Revision comment: Simplified method_color
"""
__version__ = "1.6.6"

import logging

from acquisition_client import Acquisition_Client
from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


@cached_function()
def acquisition_control(domain_name):
    return Acquisition_Control(domain_name)


class Acquisition_Control(Acquisition_Client):
    method = alias_property("domain.configuration_tables.method")
    method_online = alias_property("method.online")
    method_name = alias_property("method.selected_description")
    method_selected_description = alias_property("method.selected_description")
    method_names = alias_property("method.values")
    method_value = alias_property("method.value")
    method_command_value = alias_property("method.command_value")
    method_in_position = alias_property("method.in_position")
    method_applying = alias_property("method.applying")

    @monitored_property
    def method_color_with_orange(self, method_applying, method_in_position):
        from numpy import isnan
        from color import red, orange, green, light_gray
        if isnan(method_in_position):
            color = light_gray
        elif method_applying:
            color = orange
        elif method_in_position:
            color = green
        else:
            color = red
        return color

    @monitored_property
    def method_color(self, method_in_position):
        from numpy import isnan
        from color import red, green, light_gray
        if isnan(method_in_position):
            color = light_gray
        elif method_in_position:
            color = green
        else:
            color = red
        return color

    @monitored_property
    def configuring(self, method_applying):
        return method_applying

    @configuring.setter
    def configuring(self, configuring):
        self.method_applying = configuring
        if configuring:
            self.override_repeat = False

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    @monitored_property
    def time_to_finish_message(self, time_to_finish):
        from time_string import time_string
        return time_string(time_to_finish)

    @monitored_property
    def generating_packets_label(self, generating_packets, cancelled):
        label = "Generate Packets"
        if generating_packets:
            label = "Cancel Generate"
        elif generating_packets and cancelled:
            label = "Cancelled"
        return label

    @monitored_property
    def collecting_dataset_label(
            self,
            collecting_dataset,
            cancelled,
            dataset_started,
            dataset_complete,
    ):
        label = "Collect Dataset"
        if collecting_dataset:
            label = "Cancel Collection"
        elif collecting_dataset and cancelled:
            label = "Cancelled"
        elif dataset_complete:
            label = "Dataset Complete"
        elif dataset_started:
            label = "Resume Dataset"
        return label

    @monitored_property
    def collecting_dataset_enabled(self, online, collecting_dataset_label):
        if not online:
            enabled = False
        else:
            if collecting_dataset_label == "Dataset Complete":
                enabled = False
            elif collecting_dataset_label == "Cancelled":
                enabled = False
            else:
                enabled = True
        return enabled

    @monitored_property
    def erasing_dataset_label(self, erasing_dataset, cancelled):
        label = "Erase Dataset"
        if erasing_dataset:
            label = "Cancel Erase"
        elif erasing_dataset and cancelled:
            label = "Cancelled"
        return label

    @monitored_property
    def erasing_dataset_enabled(self, collecting_dataset, dataset_started, online):
        return not collecting_dataset and dataset_started and online

    override_repeat_label = monitored_value_property("Repeat:")
    override_repeat_enabled = monitored_value_property(True)

    @monitored_property
    def repeat_count_text(self, final_repeat_count):
        return str(final_repeat_count)

    @repeat_count_text.setter
    def repeat_count_text(self, text):
        try:
            count = int(text)
        except ValueError as x:
            logging.error(f"{text:r}: {x}")
        else:
            self.final_repeat_count = count

    finish_series_label = monitored_value_property("Finish Series")

    @monitored_property
    def play_sound_value(self, collecting_dataset, cancelled):
        return collecting_dataset and not cancelled


if __name__ == '__main__':  # for testing
    fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=fmt)

    from handler import handler as _handler
    from reference import reference as _reference

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = acquisition_control(domain_name)

    print("self.domain_name = %r" % self.domain_name)
    print("")

    property_name = "method_color"


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, property_name).monitors.add(report)
    assert len(_reference(self, property_name).monitors) > 0
    print(f"self.{property_name} = {getattr(self, property_name)!r}")
