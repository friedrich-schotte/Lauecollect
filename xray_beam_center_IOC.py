"""
EPICS Input/Output Controller

Author: Friedrich Schotte
Date created: 2022-01-31
Date last modified: 2022-01-31
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function
from IOC_auto_hierarchical import IOC


@cached_function()
def xray_beam_center_IOC(name): return XRay_Beam_Center_IOC(name)


class XRay_Beam_Center_IOC(IOC):
    name = "BioCARS"

    def __init__(self, name):
        super().__init__()
        if name is not None:
            self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def object(self):
        from xray_beam_center_driver import xray_beam_center
        return xray_beam_center(self.name)


def run(name): xray_beam_center_IOC(name).run()


def start(name): xray_beam_center_IOC(name).start()


def stop(name): xray_beam_center_IOC(name).stop()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from CA import PV

    name = "BioCARS"

    self = xray_beam_center_IOC(name)


    @_handler
    def report(event): logging.info(f"event={event}")


    pv = PV(f"{self.prefix}X")

    print('start(name)')
    # start(name)

    print(f'pv.value')
