"""
Author: Friedrich Schotte
Date created: 2021-06-03
Date last modified: 2021-06-04
Revision comment: Issue:
    line 15, in PV_name
    return eval("self.timing_system.%s.PV_name" % name)
    NameError: name 'self' is not defined
"""
__version__ = "1.0.1"


def timing_system_monitor_property(name):
    def monitor_property(callback):
        from CA import camonitors, camonitor, camonitor_clear, caget

        def fget(self):
            return bind(self, callback) in camonitors(PV_name(self))

        def fset(self, value):
            if value != fget(self):
                if value:
                    from CA_history import CA_history_init
                    CA_history_init(PV_name(self))
                    caget(PV_name(self))  # suppresses first motor callback
                    camonitor(PV_name(self), callback=bind(self, callback))
                else:
                    camonitor_clear(PV_name(self), callback=bind(self, callback))

        def PV_name(self):
            return register(self).PV_name

        def register(self):
            return getattr(self.timing_system, name)

        def bind(self, callback):
            return callback.__get__(self, self.__class__)

        return property(fget, fset)

    return monitor_property
