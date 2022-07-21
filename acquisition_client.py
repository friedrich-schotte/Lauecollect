"""
Author: Friedrich Schotte
Date created: 2019-10-29
Date last modified: 2022-07-18
Revision comment: Removed PV no longer needed
"""
__version__ = "2.15"

import logging

from PV_connected_property import PV_connected_property
from PV_property import PV_property
from PV_record import PV_record
from PV_record_property import PV_record_property
from cached_function import cached_function
from reference import reference


@cached_function()
def acquisition_client(domain_name):
    return Acquisition_Client(domain_name)


class Acquisition_Client(PV_record):
    online = PV_connected_property("collecting_dataset")

    time_to_finish = PV_property(dtype=float)
    description = PV_property(dtype=str)
    directory = PV_property(dtype=str)
    info_message = PV_property(dtype=str)
    status_message = PV_property(dtype=str)
    actual_message = PV_property(dtype=str)
    generating_packets = PV_property(default_value=False)
    collecting_dataset = PV_property(default_value=False)
    erasing_dataset = PV_property(default_value=False)
    cancelled = PV_property(default_value=False)
    dataset_started = PV_property(default_value=False)
    dataset_complete = PV_property(default_value=False)
    override_repeat = PV_property(default_value=False)
    override_repeat_count = PV_property(default_value=1)
    final_repeat_count = PV_property(default_value=1)
    finish_series = PV_property(default_value=False)
    finish_series_variable = PV_property(dtype=str)
    collection_variables_with_count = PV_property(dtype=list)
    delay_configuration = PV_property(dtype=str)
    collection_order = PV_property(dtype=str)
    file_basenames = PV_property(dtype=list)
    sequences_per_scan_point = PV_property(default_value=1)
    n = PV_property("n", dtype=int)
    sequence_variables = PV_property(dtype=list)
    collection_variables_with_options = PV_property(dtype=list)
    detector_configuration = PV_property(dtype=str)
    power_configuration = PV_property(dtype=str)

    current = PV_property(dtype=int)
    current_i = PV_property(dtype=int)
    collection_first_i = PV_property(dtype=int)

    scanning = PV_record_property(type_name="acquisition_scanning_client")
    scan_point_dividers = PV_record_property(type_name="acquisition_scan_point_dividers_client")


if __name__ == '__main__':
    from handler import handler

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = acquisition_client(domain_name)

    property_name = "online"

    @handler
    def report(event=None):
        logging.info(f"event={event}")

    reference(self, property_name).monitors.add(report)

    print("self.prefix = %r" % self.prefix)
    print("self.%s = %r" % (property_name, getattr(self, property_name)))
