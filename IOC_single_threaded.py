"""EPICS IOC prototype
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2020-01-11
Revision comment: Added: default_scan_period
"""
__version__ = "2.5"

from logging import debug, info


class IOC(object):
    name = "sample"
    prefix = "NIH:SAMPLE."

    default_scan_period = 1.0
    from persistent_property_new import persistent_property
    scan_period = persistent_property("scan_period", "self.default_scan_period")

    property_names = []

    @property
    def all_property_names(self):
        return self.property_names + ["scan_period"]

    def start(self):
        if not self.running:
            from threading import Thread
            name = type(self).__name__ + ".run"
            self.run_thread = Thread(target=self.run, name=name)
            self.run_thread.daemon = True
            self.run_thread.start()

    def stop(self):
        if hasattr(self, "run_thread"):
            self.run_thread.cancelled = True

    @classmethod
    def stop_all(cls):
        from threading import enumerate
        for thread in enumerate():
            if thread.name == cls.__name__ + ".run":
                thread.cancelled = True
                thread.join()

    def get_running(self):
        return hasattr(self, "run_thread") and self.run_thread.is_alive()

    def set_running(self, value):
        if bool(value) is True:
            self.start()
        if bool(value) is False:
            self.stop()

    running = property(get_running, set_running)

    def run(self):
        info("IOC starting (Prefix: %s)..." % self.prefix)

        self.start_monitoring()
        self.update_PVs()
        self.start_monitoring_PVs()
        self.add_idle_handler(self.scan_period, self.timed_update)
        from CAServer_single_threaded import run
        run()
        self.stop_monitoring()
        info("IOC shut down (Prefix: %s)" % self.prefix)

    def add_idle_handler(self, period, handler):
        from CAServer_single_threaded import add_idle_handler
        add_idle_handler(period, handler)

    def timed_update(self):
        from CAServer_single_threaded import casget, casput
        from same import same
        for property_name in self.all_property_names:
            value = getattr(self, property_name)
            PV_name = self.PV_name(property_name)
            old_value = casget(PV_name)
            if not same(value, old_value):
                debug("Timed update: %s=%r" % (PV_name, value))
                casput(PV_name, value, update=False)

    EPICS_enabled = running  # for backward compatibility

    def start_monitoring(self):
        from handler import handler
        from reference import reference
        for property_name in self.property_names:
            event_handler = handler(self.handle_change, property_name)
            reference(self, property_name).monitors.add(event_handler)

    def update_PVs(self):
        from CAServer_single_threaded import casput
        for property_name in self.all_property_names:
            value = getattr(self, property_name)
            PV_name = self.PV_name(property_name)
            casput(PV_name, value, update=False)

    def start_monitoring_PVs(self):
        # Monitor client-writable PVs.
        from CAServer_single_threaded import casmonitor
        for property_name in self.all_property_names:
            PV_name = self.PV_name(property_name)
            casmonitor(PV_name, callback=self.handle_PV_change, new_thread=False)

    def stop_monitoring(self):
        from handler import handler
        from reference import reference
        for property_name in self.property_names:
            event_handler = handler(self.handle_change, property_name)
            reference(self, property_name).monitors.remove(event_handler)

    def handle_change(self, property_name):
        PV_name = self.PV_name(property_name)
        value = getattr(self, property_name)
        from CAServer_single_threaded import casput
        debug("Triggered update: %s=%r" % (PV_name, value))
        casput(PV_name, value)

    def handle_PV_change(self, PV_name, value, _char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name, value))
        from CAServer_single_threaded import casput
        for property_name in self.all_property_names:
            if PV_name == self.PV_name(property_name):
                setattr(self, property_name, value)
                value = getattr(self, property_name)
                info("%s = %r" % (PV_name, value))
                casput(PV_name, value)

    def PV_name(self, property_name):
        return self.prefix + property_name.upper()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


if __name__ == "__main__":
    import logging

    logger = logging.getLogger()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    ioc = IOC()
    print("ioc.start()")

    print("caget('NIH:SAMPLE.SCAN_PERIOD')")
    print("caput('NIH:SAMPLE.SCAN_PERIOD',2)")
