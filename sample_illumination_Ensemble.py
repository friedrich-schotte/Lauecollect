"""
Sample illumination for the high-speed diffractometer.
A white LED with a 90-Ohm prtective resistor is driven by an analog output
of the Aerotech Ensemble Controller
with a voltage of 0 to 5 V
Cabing: Ensemble X, AOUT pin 4 -> 90 Ohm resistor -> LED (Lumex SSL-LX5093WC/A)
-> AOUT pin 1 (ground)
F. Schotte, 26 Jun 2013 - 5 Jul 2014
"""
__version__ = "1.1"
from Ensemble import ensemble

class IlluminatorVoltage(object):
    def get_value(self): return ensemble.analog_output
    def set_value(self,value): ensemble.analog_output = value
    value = property(get_value,set_value)

illuminator_voltage = IlluminatorVoltage()


class IlluminatorOn(object):
    def get_value(self): return illuminator_voltage.value > 0
    def set_value(self,value):
        if value: illuminator_voltage.value = self.voltage
        else: illuminator_voltage.value = 0
    value = property(get_value,set_value)

    def get_voltage(self):
        """Operation voltage"""
        from DB import dbget
        value = dbget("Ensemble.illuminator.voltage")
        try: value = float(value)
        except ValueError: value = 3.3
        return value
    def set_voltage(self,value):
        from DB import dbput
        dbput("Ensemble.illuminator.voltage",str(value))
    voltage = property(get_voltage,set_voltage)

    moving = False

illuminator_on = IlluminatorOn()

illuminator_inserted = illuminator_on # for backward compatibility


if __name__ == '__main__': # test program
    print "illuminator_on.value"
    print "illuminator_on.value = True"
    print "illuminator_on.value = False"
