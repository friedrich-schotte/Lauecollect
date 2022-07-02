"""
Author: Friedrich Schotte
Date created: 2022-06-14
Date last modified: 2022-06-14
Revision comment:
"""
__version__ = "1.0"

import logging

from cached_function import cached_function
from db_property import db_property
from alias_property import alias_property
from handler_method import handler_method


@cached_function()
def rayonix_detector_metadata_driver(domain_name):
    return Rayonix_Detector_Metadata_Driver(domain_name)


class Rayonix_Detector_Metadata_Driver:

    def __init__(self, domain_name):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def running(self):
        return self.handle_filename in self.filename_handlers

    @running.setter
    def running(self, running):
        if running:
            self.filename_handlers.add(self.handle_filename)
        else:
            self.filename_handlers.remove(self.handle_filename)

    @handler_method
    def handle_filename(self, event):
        image_filename = event.value
        logging.debug(f"Updating {image_filename!r}")
        from rayonix_image import rayonix_image
        image = rayonix_image(image_filename)
        image.xtal_to_detector = self.xtal_to_detector
        image.start_xtal_to_detector = self.xtal_to_detector
        image.end_xtal_to_detector = self.xtal_to_detector
        image.start_phi = self.phi
        image.end_phi = self.phi
        image.beam_x = self.beam_x / 3840 * image.width
        image.beam_y = self.beam_y / 3840 * image.height
        image.source_wavelength = self.source_wavelength

    @property
    def filename_handlers(self):
        from reference import reference
        return reference(self, "image_filename").monitors

    xtal_to_detector = alias_property("domain.DetZ.value")
    phi = alias_property("domain.HuberPhi.value")
    beam_x = db_property("beam_x", 1986)
    beam_y = db_property("beam_y", 1973)
    source_wavelength = db_property("source_wavelength", 1.0)

    image_filename = alias_property("rayonix_detector.last_filename")
    acquiring = alias_property("rayonix_detector.acquiring")

    @property
    def rayonix_detector(self):
        from rayonix_detector import rayonix_detector
        return rayonix_detector(self.domain_name)

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/{self.class_name}"

    @property
    def class_name(self):
        return type(self).__name__.lower()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = rayonix_detector_metadata_driver(domain_name)

    # from reference import reference
    from handler import handler

    @handler
    def report(event): logging.info(f"{event}")


    print('self.running = True')
    # reference(self, "image_filename").monitors.add(report)
