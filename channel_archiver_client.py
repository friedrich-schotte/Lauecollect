"""
Author: Friedrich Schotte
Date created: 2019-12-10
Date last modified: 2022-03-10
Revision comment: Cleanup: Renamed: channel_archiver_driver
"""
__version__ = "1.3.1"

from cached_function import cached_function


@cached_function()
def channel_archiver(domain_name):
    return Channel_Archiver(domain_name)


class Channel_Archiver(object):
    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    domain_name = "BioCARS"

    @property
    def prefix(self):
        prefix = ("%s:CHANNEL_ARCHIVER." % self.domain_name).upper()
        return prefix

    @property
    def channel_archiver_driver(self):
        from channel_archiver_driver import channel_archiver_driver
        return channel_archiver_driver(self.domain_name)

    from PV_property import PV_property
    from numpy import nan
    archiving_requested = PV_property("archiving_requested", nan)
    running = archiving_requested
    archiving = PV_property("archiving", nan)

    from alias_property import alias_property
    PVs = alias_property("channel_archiver_driver.PVs")
    directory = alias_property("channel_archiver_driver.directory")
    logfile = alias_property("channel_archiver_driver.logfile")


if __name__ == '__main__':  # for testing
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
                        )

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    self = channel_archiver(domain_name)

    print('self.domain_name = %r' % self.domain_name)
    print('')
    print("self.archiving_requested")
    print("self.directory")
    print("self.PVs")
