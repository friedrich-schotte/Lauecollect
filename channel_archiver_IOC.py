"""
EPICS Input/Output Controller

Author: Friedrich Schotte
Date created: 2022-03-04
Date last modified: 2022-03-10
Revision comment: import channel_archiver_driver
"""
__version__ = "1.0.1"

from cached_function import cached_function
from IOC_auto_hierarchical import IOC


@cached_function()
def channel_archiver_IOC(name): return Channel_Archiver_IOC(name)


class Channel_Archiver_IOC(IOC):
    name = "BioCARS"

    def __init__(self, name):
        super().__init__()
        if name is not None:
            self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    def start(self):
        self.object.start()
        super().start()

    def stop(self):
        self.object.stop()
        super().stop()

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def object(self):
        from channel_archiver_driver import channel_archiver_driver
        return channel_archiver_driver(self.name)


def run(name): channel_archiver_IOC(name).run()


def start(name): channel_archiver_IOC(name).start()


def stop(name): channel_archiver_IOC(name).stop()


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from CA import PV

    name = "BioCARS"

    self = channel_archiver_IOC(name)


    @_handler
    def report(event): logging.info(f"event={event}")


    pv = PV(f"{self.prefix}ARCHIVING_REQUESTED")

    print('start(name)')
    # start(name)

    print(f'pv.value')
