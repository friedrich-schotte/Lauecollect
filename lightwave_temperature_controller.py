"""
ILX Lightwave LDT-5948 Precision Temperature Controller
EPICS client
Author: Friedrich Schotte
Date created: 2009-12-14
Date last modified: 2021-03-31
Revision comment: Testing: monitors
"""
__version__ = "4.5.2"

from EPICS_motor import EPICS_motor


def alias(name):
    """Make property given by name be known under a different name"""

    def fget(self): return getattr(self, name)

    def fset(self, value): setattr(self, name, value)

    return property(fget, fset)


class Lightwave_Temperature_Controller(EPICS_motor):
    """ILX Lightwave LDT-5948 Precision Temperature Controller"""
    port_name = alias("COMM")
    stabilization_threshold = alias("RDBD")
    stabilization_nsamples = alias("NSAM")
    current_low_limit = alias("ILLM")
    current_high_limit = alias("IHLM")
    trigger_enabled = alias("TENA")
    trigger_start = alias("P1SP")
    trigger_stop = alias("P1EP")
    trigger_stepsize = alias("P1SI")
    id = alias("ID")
    setT = alias("command_value")  # for backward compatibility with lauecollect
    readT = alias("value")  # for backward compatibility with lauecollect


lightwave_temperature_controller = Lightwave_Temperature_Controller(prefix="NIH:LIGHTWAVE",
                                                                    name="lightwave_temperature_controller")

if __name__ == "__main__":
    import logging
    from reference import reference

    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = lightwave_temperature_controller

    print(f'self.prefix = {self.prefix}')
    print(f'self.port_name = {self.port_name}')
    print(f'self.command_value = {self.command_value}')

    def report(event):
        logging.info(f"{event}")

    print('reference(self, "value").monitors.add(report)')
    print('reference(self, "P").monitors.add(report)')
    print('reference(self, "I").monitors.add(report)')
    print('reference(self, "enabled").monitors.add(report)')
    print('reference(self, "DMOV").monitors.add(report)')
    print('reference(self, "moving").monitors.add(report)')
