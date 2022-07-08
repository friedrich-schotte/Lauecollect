"""Data Collection diagnostics
Author: Friedrich Schotte
Date created: 2018-10-27
Date last modified: 2022-07-06
Revision comment: Renamed: ...history.time(...)
"""
__version__ = "2.0.15"

import logging

from alias_property import alias_property
from cached_function import cached_function


@cached_function()
def diagnostics(domain_name):
    return Diagnostics(domain_name)


class Diagnostics(object):
    """Data Collection diagnostics"""
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        self.cancelled = False

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    @property
    def db_name(self):
        return "diagnostics/%s" % self.domain_name

    from db_property import db_property
    list = db_property("list", "")
    values = {}
    images = {}

    def get_running(self):
        return self.monitoring_variables

    def set_running(self, value):
        if value and not self.running:
            self.clear()
        self.monitoring_variables = value

    running = property(get_running, set_running)

    def started(self, image_number):
        time = self.image_number_history.time(image_number)
        acquiring = self.image_number_history.value(time)
        if not acquiring == 1:
            start_time = self.acquiring_history.time(1)
            start_image_number = self.acquiring_history.value(start_time)
            if start_image_number == image_number:
                time = start_time
        return time

    def finished(self, image_number):
        time = self.image_number_history.time(image_number + 1)
        return time

    def is_finished(self, image_number):
        from numpy import isfinite
        return isfinite(self.finished(image_number))

    def average_values(self, image_number):
        values = [self.interpolated_average_value(image_number, v) for v in self.variable_names]
        return values

    def interpolated_average_value(self, image_number, variable):
        from numpy import nan, isfinite
        v0 = nan
        t0 = (self.started(image_number) + self.finished(image_number)) / 2
        if isfinite(t0):
            t, v = self.image_timed_samples(image_number, variable)
            v0 = self.interpolate(t, v, t0)
        return v0

    @staticmethod
    def interpolate(t, v, t0):
        from numpy import nan, asarray, unique
        # Needed for InterpolatedUnivariateSpline ('x must be strictly increasing')
        t, v = asarray(t), asarray(v)
        order = unique(t, return_index=True)[1]
        t, v = t[order], v[order]

        v0 = nan
        if len(v) > 1:
            from scipy.interpolate import InterpolatedUnivariateSpline
            try:
                f = InterpolatedUnivariateSpline(t, v, k=1)
                v0 = f([t0])[0]
            except ValueError:
                logging.warning(f"InterpolatedUnivariateSpline: {t}, {v}")
        if len(v) == 1:
            v0 = v[0]
        return v0

    def image_timed_samples(self, image_number, variable):
        from numpy import array, where
        times, values = [], []
        if variable in self.values:
            t1, t2 = self.started(image_number), self.finished(image_number)
            t = array([sample.time for sample in self.values[variable]])
            v = array([sample.value for sample in self.values[variable]])
            i = list(where((t1 <= t) & (t <= t2))[0])
            if len(i) < 1:
                i += list(where(t <= t1)[0][-1:])
            if len(i) < 1:
                i += list(where(t >= t2)[0][0:1])
            if len(i) < 2:
                i += list(where(t >= t2)[0][0:1])
            times, values = t[i], v[i]
        return times, values

    def clear(self):
        logging.debug("Clearing diagnostics")
        self.values = {}
        self.image_number_history.clear()
        self.acquiring_history.clear()

    @property
    def variable_names(self):
        names = self.list.replace(" ", "").split(",")
        while '' in names:
            names.remove('')
        return names

    @property
    def count(self):
        return len(self.variable_names)

    @property
    def monitoring_variables(self):
        return all([handler in reference.monitors
                   for reference, handler in zip(self.variable_references, self.variable_handlers)])

    @monitoring_variables.setter
    def monitoring_variables(self, value):
        if value:
            for reference, handler in zip(self.variable_references, self.variable_handlers):
                reference.monitors.add(handler)
        else:
            for reference, handler in zip(self.variable_references, self.variable_handlers):
                reference.monitors.remove(handler)

    @property
    def vars(self):
        my_vars = []
        import instrumentation
        for variable_name in self.variable_names:
            try:
                var = getattr(instrumentation, variable_name)
            except KeyError:
                logging.error(f"{variable_name!r} not defined in module 'instrumentation'")
                from CA import PV
                var = PV("")
            my_vars += [var]
        return my_vars

    @property
    def variable_references(self):
        from reference import reference
        return [reference(var, "value") for var in self.vars]

    @property
    def variable_handlers(self):
        from handler import handler
        return [handler(self.handle_variable_update, name) for name in self.variable_names]

    def handle_variable_update(self, variable_name, event):
        if variable_name not in self.values:
            self.values[variable_name] = []
        self.values[variable_name] += [self.timestamped_value(event.time, event.value)]

    @property
    def image_number_history(self):
        from event_history_2 import event_history
        return event_history(self.image_number_reference)

    @property
    def acquiring_history(self):
        from event_history_2 import event_history
        return event_history(self.image_number_reference)

    @property
    def image_number_reference(self):
        from reference import reference
        return reference(self.timing_system.registers.image_number, "count")

    def acquiring_reference(self):
        from reference import reference
        return reference(self.timing_system.registers.acquiring, "count")

    timing_system = alias_property("domain.timing_system_client")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    class timestamped_value(object):
        def __init__(self, time, value):
            self.time = time
            self.value = value

        def __repr__(self):
            from date_time import date_time
            return "(%s,%r)" % (date_time(self.time), self.value)

    class interval(object):
        from numpy import inf

        def __init__(self, started=-inf, finished=inf):
            self.started = started
            self.finished = finished

        def matches(self, time):
            return self.started <= time <= self.finished

        def __repr__(self):
            from date_time import date_time
            return "(%s,%s)" % (date_time(self.started), date_time(self.finished))


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = diagnostics(domain_name)
    print('self.domain_name = %r' % self.domain_name)
    print('')

    # from instrumentation import ring_current,bunch_current,temperature
    # variable = "ring_current"

    print("self.running = True")
    print("self.running = False")
    # print("self.variable_names")
    # print("self.values")
    # print("self.image_numbers")
    # print('self.average_values(self.image_numbers[2])')
    # print("self.timing_system.registers.acquiring.count = 1")
    # print("self.timing_system.registers.image_number.count += 1")
    # print("self.timing_system.registers.acquiring.count = 0")
    # print("camonitors(self.timing_system.registers.image_number.PV_name)")
    # print("camonitors(self.timing_system.registers.acquiring.PV_name)")

    # import instrumentation
    # print('instrumentation.BioCARS.diagnostics')
    # print('instrumentation.LaserLab.diagnostics')
