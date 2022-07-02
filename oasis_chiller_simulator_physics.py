"""
Author: Friedrich Schotte
Date created: 2021-12-04
Date last modified: 2021-12-04
Revision comment:
"""
__version__ = "1.0"

import logging


class Oasis_Chiller_Simulator_Physics:
    from thread_property_2 import thread_property
    from persistent_property import persistent_property

    def __init__(self):
        self.running = False

    set_temperature = persistent_property("set_temperature", 20.0)
    enabled = persistent_property("enabled", True)

    @thread_property
    def running(self):
        from thread_property_2 import cancelled
        from time import time, sleep

        self.time = time()
        while not cancelled():
            self.update_temperature()
            sleep(0.25)

    def update_temperature(self):
        from time import time
        from numpy import exp

        t = time()
        t0 = self.time
        T0 = self.temperature
        T_target = self.set_temperature if self.enabled else self.heat_sink_temperature
        dt = t - t0
        dT0 = T0 - T_target
        dT = dT0 * exp(-dt / self.time_constant)
        T = T_target + dT
        self.time = t
        self.temperature = T

    time = 0
    temperature = 20.0
    heat_sink_temperature = 20.0
    time_constant = 120.0  # heat dissipation time constant [in seconds]


oasis_chiller_simulator_physics = Oasis_Chiller_Simulator_Physics()

if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = oasis_chiller_simulator_physics
    self.running = True

    print(f"self.set_temperature = {self.set_temperature}")
    print(f"self.temperature = {self.temperature}")
    print(f"self.running = {self.running}")
