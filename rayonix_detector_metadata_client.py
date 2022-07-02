"""
Authors: Friedrich Schotte
Date created: 2022-06-14
Date last modified: 2022-06-14
Revision comment:
"""
__version__ = "1.0"

import logging
from cached_function import cached_function
from PV_record import PV_record
from PV_property import PV_property


@cached_function()
def rayonix_detector_metadata_client(domain_name):
    return Rayonix_Detector_Metadata_Client(domain_name)


class Rayonix_Detector_Metadata_Client(PV_record):
    xtal_to_detector = PV_property(dtype=float)
    phi = PV_property(dtype=float)
    beam_x = PV_property(dtype=float)
    beam_y = PV_property(dtype=float)
    source_wavelength = PV_property(dtype=float)


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference as _reference
    from handler import handler as _handler

    domain_name = "BioCARS"
    self = rayonix_detector_metadata_client(domain_name)

    print(f'self.xtal_to_detector = {self.xtal_to_detector}')
    print(f'self.phi = {self.phi}')
    print(f'self.beam_x = {self.beam_x}')
    print(f'self.beam_y = {self.beam_y}')
    print(f'self.source_wavelength = {self.source_wavelength}')

    @_handler
    def report(event): logging.info(f"event={event}")


    _reference(self, "xtal_to_detector").monitors.add(report)
