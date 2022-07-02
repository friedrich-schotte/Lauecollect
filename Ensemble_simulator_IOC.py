"""
Author: Friedrich Schotte
Date created: 2022-03-25
Date last modified: 2022-03-25
Revision comment:
"""
__version__ = "1.0"


class Ensemble_Simulator_IOC(object):
    name = "Ensemble_simulator_IOC"

    motor_names = [
        "SampleX", "SampleY", "SampleZ", "PumpA",
    ]

    from sim_motor import sim_EPICS_motor as motor

    SampleX = motor("NIH:SAMPLEX", name="SampleX", description="X")
    SampleY = motor("NIH:SAMPLEY", name="SampleY", description="Y")
    SampleZ = motor("NIH:SAMPLEZ", name="SampleZ", description="Z")
    PumpA = motor("NIH:PUMPA", name="PumpA", description="PumpA")

    def get_motors(self):
        return [getattr(self, n) for n in self.motor_names]

    motors = property(get_motors)

    def get_running(self):
        return any([motor.EPICS_enabled for motor in self.motors])

    def set_running(self, value):
        if value:
            for motor in self.motors:
                motor.EPICS_enabled = True
        else:
            for motor in self.motors:
                motor.EPICS_enabled = False

    running = property(get_running, set_running)

    def run(self):
        self.running = True
        from time import sleep
        try:
            while True:
                sleep(0.25)
        except KeyboardInterrupt:
            pass
        self.running = False


Ensemble_simulator_IOC = Ensemble_Simulator_IOC()


def run(): Ensemble_simulator_IOC.run()


if __name__ == "__main__":
    self = Ensemble_simulator_IOC  # for debugging
    print("Ensemble_simulator_IOC.running = True")
    print("Ensemble_simulator_IOC.running = False")
    print("run()")
    print("self.PumpA.EPICS_enabled")
