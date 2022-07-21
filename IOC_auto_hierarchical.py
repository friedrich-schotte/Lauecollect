"""
EPICS Input/Output Controller
Author: Friedrich Schotte
Date created: 2020-12-02
Date last modified: 2022-07-11
Revision comment: Refactored: driver_base_name
"""
__version__ = "1.3.1"

from logging import debug, exception
from cached_function import cached_function


class IOC:
    name = "example"

    def __init__(self, name=None):
        if name is not None:
            self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def driver(self):
        return example(self.name)

    @property
    @cached_function()
    def prefix(self):
        if self.driver_class_name:
            prefix = f"{self.driver_domain_name}:{self.driver_class_name}.{self.driver_base_name}"
        else:
            prefix = f"{self.driver_domain_name}:{self.driver_base_name}"
        prefix = prefix.strip(".:") + "."
        prefix = prefix.upper()
        return prefix

    @property
    def driver_domain_name(self):
        return self.driver.domain_name

    @property
    def driver_base_name(self):
        driver_base_name = ""
        driver = self.driver
        if hasattr(driver, "base_name"):
            driver_base_name = driver.base_name
        elif hasattr(driver, "name"):
            if driver.name.startswith(self.driver_domain_name+"."):
                driver_base_name = driver.name.replace(self.driver_domain_name+".", "", 1)
        return driver_base_name

    @property
    def driver_class_name(self):
        name = type(self.driver).__name__
        name = name.replace("_Driver", "")
        name = name.replace("_Simulator", "")
        return name

    run_cancelled = False

    def run(self):
        self.run_cancelled = False
        self.start()
        while not self.run_cancelled:
            from time import sleep
            sleep(0.2)
        self.stop()

    from thread_property_2 import thread_property
    running = thread_property(run)

    def start(self):
        debug("IOC %s starting" % self.prefix)
        from handler import handler
        self.cas.casmonitor_record(
            prefix=self.prefix,
            get_exists=self.PV_exists,
            subscribe_handler=handler(self.handle_PV_subscribe),
            get_value=self.PV_value,
            put_handler=handler(self.handle_PV_put),
        )
        self.cas.start()

    def stop(self):
        self.cas.stop()
        debug("IOC %s stopped." % self.prefix)

    def PV_exists(self, PV_name):
        # debug(f"Got discover request for {PV_name}")
        exists = self.attribute_reference(PV_name) is not None
        # debug(f"{PV_name} exists: {exists}")
        return exists

    def handle_PV_subscribe(self, PV_name):
        attribute_reference = self.attribute_reference(PV_name)
        if attribute_reference:
            # debug(f"Accepted subscription request for {PV_name}")
            value = attribute_reference.value
            debug(f"Sending initial value of {PV_name} = {attribute_reference} = {value!r:.80}")
            self.cas.casput(PV_name, value)
            # debug(f"Setting up monitoring of {PV_name} = {attribute_reference}")
            attribute_reference.monitors.add(
                self.attribute_change_handler(PV_name))
            # debug(f"Now monitoring {PV_name} = {attribute_reference}")

    def PV_value(self, PV_name):
        value = None
        attribute_reference = self.attribute_reference(PV_name)
        if attribute_reference:
            debug(f"Accepted read request for {PV_name}")
            value = attribute_reference.value
            debug(f"Returning {PV_name} = {attribute_reference} = {value!r}")
        return value

    def handle_PV_put(self, PV_name, value):
        debug(f"Got write request {PV_name} = {value!r}")
        attribute_reference = self.attribute_reference(PV_name)
        if attribute_reference:
            debug(f"Setting {PV_name} = {attribute_reference} = {value!r}")
            from is_array import is_array
            if is_array(attribute_reference.value) and not is_array(value):
                debug(f"{PV_name} = {attribute_reference} is array. Interpreting {value} as {[value]}")
                value = [value]
            attribute_reference.value = value
            # value = attribute_reference.value
            # debug(f"Read-back: {PV_name} = {attribute_reference} = {value!r}")
            # self.cas.casput(PV_name, value)

    def attribute_change_handler(self, PV_name):
        from handler import handler
        return handler(self.handle_attribute_change, PV_name)

    def handle_attribute_change(self, PV_name, event):
        # debug(f"Sending push notification: {PV_name} = {event.reference} = {event.value!r}")
        self.cas.casput(PV_name, event.value, timestamp=event.time)

    def attribute_reference(self, PV_name):
        reference = None
        if PV_name.startswith(self.prefix):
            name = PV_name[len(self.prefix):]
            # name = translate(name) # "METHOD.MOTOR1.CHOICES" -> "METHOD.CHOICES1"
            # noinspection PyBroadException
            try:
                reference = attribute_reference(self.driver, name)
            except Exception:
                exception("{PV_name!r}")
        return reference

    @property
    @cached_function()
    def attribute_names(self):
        names = dir(self.driver)
        names = dict([(name.upper(), name) for name in names])
        return names

    @property
    def cas(self):
        import EPICS_CA.CAServer_single_threaded_new
        return EPICS_CA.CAServer_single_threaded_new


@cached_function()
def example(name): return Example(name)


def attribute_reference(obj, name):
    # debug(f"{obj}, {name!r}")
    name = name.upper()
    if "." in name:
        attribute_name, remaining_part = name.split(".", 1)
    else:
        attribute_name, remaining_part = name, ""

    if attribute_name in attribute_names(obj):
        attribute_name = attribute_names(obj)[attribute_name]
        if remaining_part:
            child_object = getattr(obj, attribute_name)
            ref = attribute_reference(child_object, remaining_part)
        else:
            from reference import reference
            ref = reference(obj, attribute_name)
    elif index_suffix(attribute_name) is not None:
        indexable_attribute_name, index = name_without_index(attribute_name), index_suffix(attribute_name)
        # debug(f"attribute_name = {indexable_attribute_name!r}, index = {index}")
        if indexable_attribute_name in attribute_names(obj):
            indexable_attribute_name = attribute_names(obj)[indexable_attribute_name]
            obj = getattr(obj, indexable_attribute_name)
            if hasattr(obj, "__getitem__"):
                if remaining_part:
                    child_object = obj[index]
                    ref = attribute_reference(child_object, remaining_part)
                else:
                    from item_reference import item_reference
                    ref = item_reference(obj, index)
            else:
                debug(f"{name}: {obj}[{index}]: {obj} is not indexable")
                ref = None
        else:
            debug(f"{name}: {obj} has no attribute '{attribute_name}' or '{indexable_attribute_name}'")
            ref = None
    else:
        debug(f"{name}: {obj} has no attribute '{attribute_name}'")
        ref = None
    return ref


def index_suffix(attribute_name):
    if attribute_name[-1:].isdigit():
        end = -1
        while attribute_name[:end-1] and attribute_name[end-1:].isdigit():
            end -= 1
        index = attribute_name[end:]
        index = int(index) - 1
        if index < 0:
            index = None
    else:
        index = None
    return index


def name_without_index(attribute_name):
    if attribute_name[-1:].isdigit():
        end = -1
        while attribute_name[:end-1] and attribute_name[end-1:].isdigit():
            end -= 1
        attribute_name = attribute_name[:end]
    return attribute_name


def translate(name):
    # "LASERLAB:CONFIGURATION.METHOD.MOTOR1.CURRENT_POSITION"
    # "LASERLAB:CONFIGURATION.METHOD.CURRENT_POSITION1"
    from re import sub
    name = sub(r"(.*)[.]MOTOR([0-9]+)[.]([A-Z_]+)", r"\1.\3\2", name)
    return name


def attribute_names(obj):
    names = dir(obj)
    names = dict([(name.upper(), name) for name in names])
    return names


class Example:
    name = "example"
    from monitored_value_property import monitored_value_property

    def __init__(self, name=None):
        if name is not None:
            self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    value = monitored_value_property(default_value=0.0)


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler


    class Configuration_IOC(IOC):
        name = "BioCARS.power_configuration"

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
        def driver(self):
            from configuration_driver import configuration_driver
            return configuration_driver(self.name)


    self = Configuration_IOC("BioCARS.power_configuration")


    @_handler
    def report(event):
        logging.info(f"event={event}")


    # print('self.attribute_reference("LASERLAB:CONFIGURATION.CONFIGURATION_NAMES")')
    # print('attribute_reference(self.driver, "METHOD.MOTOR1.CURRENT_POSITION")')
    # print('self.attribute_reference("LASERLAB:CONFIGURATION.METHOD.MOTOR1.CURRENT_POSITION")')
    # print('')
    # print('self.start()')
    # self.start()

    # print('import CA; CA.PV("LASERLAB:CONFIGURATION.CONFIGURATION_NAMES").value')
    # print('import CA; CA.PV("LASERLAB:CONFIGURATION.METHOD.TITLE").value')
    # print('import CA; CA.PV("LASERLAB:CONFIGURATION.METHOD.MOTOR1.CURRENT_POSITION").value')

    # print("from domain import domain")
    # print('attribute_reference(domain.BioCARS.timing_system.composer,"T0")')
