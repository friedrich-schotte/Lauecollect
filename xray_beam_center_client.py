"""
Authors: Friedrich Schotte
Date created: 2022-02-01
Date last modified: 2022-02-01
Revision comment:
"""
__version__ = "1.0"

import logging
from cached_function import cached_function
from PV_record import PV_record


@cached_function()
def xray_beam_center(domain_name): return XRay_Beam_Center(domain_name)


class XRay_Beam_Center(PV_record):
    from PV_property import PV_property
    from numpy import nan

    # Output
    X = PV_property("X", nan)
    Y = PV_property("Y", nan)
    I = PV_property("I", nan)

    # Parameters
    nominal_beam_center_x = PV_property("nominal_beam_center_x", nan)
    nominal_beam_center_y = PV_property("nominal_beam_center_y", nan)
    nominal_image_width = PV_property("nominal_image_width", nan)
    nominal_image_height = PV_property("nominal_image_height", nan)
    ROI_size = PV_property("ROI_size", nan)
    I_min = PV_property("I_min", nan)


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference
    from handler import handler

    domain_name = "BioCARS"
    self = xray_beam_center(domain_name)

    print(f'self.X = {self.X}')
    print(f'self.Y = {self.Y}')
    print(f'self.I = {self.I}')

    @handler
    def report(event): logging.info(f"event={event}")


    # reference(self, "X").monitors.add(report)
    # reference(self, "Y").monitors.add(report)
    reference(self, "I").monitors.add(report)
