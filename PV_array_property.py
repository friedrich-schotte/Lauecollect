"""
Author: Friedrich Schotte
Date created: 2021-09-27
Date last modified: 2022-06-15
Revision comment: Updated examples
"""
__version__ = "1.0.1"


class PV_array_property(property):
    default_value = ""
    upper_case = True

    def __init__(self, PV_name_template, count,
                 default_value=None, upper_case=None):
        """PV_name_template: e.g. "motor{i+1}.current_position"
        count: e.g. "n_motors"
        default_value: may also be a property object"""
        property.__init__(self, fget=self.get_property, fset=self.set_property)
        self.PV_name_template = PV_name_template
        self.length_PV_name = count
        if default_value is not None:
            self.default_value = default_value
        if upper_case is not None:
            self.upper_case = upper_case

    def __repr__(self):
        return f"{self.class_name}({self.PV_name_template!r}, default_value={self.default_value!r})"

    def get_property(self, instance):
        from PV_array import PV_array
        value = PV_array(
            self.full_PV_name_template(instance),
            count=self.full_length_PV_name(instance),
            default_value=self.default_value,
        )
        return value

    def set_property(self, instance, value):
        self.get_property(instance)[:] = value

    def monitors(self, instance):
        return self.attributes(instance).handlers

    def monitor_setup(self, instance):
        self.reference(instance).monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        self.reference(instance).monitors.remove(self.handler(instance))

    def reference(self, instance):
        from all_items_reference import all_items_reference
        return all_items_reference(self.get_property(instance))

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event):
        from reference import reference
        new_reference = reference(instance, self.get_name(instance))
        from event import event as event_object
        new_event = event_object(time=event.time, value=event.value, reference=new_reference)
        self.monitors(instance).call(event=new_event)

    def full_PV_name_template(self, instance):
        name_template = self.prefix(instance) + self.PV_name_template
        if self.upper_case:
            name_template = name_template.upper()
        return name_template

    def full_length_PV_name(self, instance):
        name = self.prefix(instance) + self.length_PV_name
        if self.upper_case:
            name = name.upper()
        return name

    def prefix(self, instance):
        prefix = ""
        if hasattr(self, "prefix"):
            prefix = instance.prefix
        if hasattr(self, "__prefix__"):
            prefix = instance.__prefix__
        if prefix and not prefix.endswith("."):
            prefix += "."
        return prefix

    def attributes(self, instance):
        attributes_cache = self.attributes_cache(instance)
        name = self.get_name(instance)
        if name not in attributes_cache:
            attributes_cache[name] = self.Attributes(self, instance)
        attributes = attributes_cache[name]
        return attributes

    def attributes_cache(self, instance):
        if not hasattr(instance, self.attributes_cache_name):
            setattr(instance, self.attributes_cache_name, {})
        attributes_cache = getattr(instance, self.attributes_cache_name)
        return attributes_cache

    @property
    def attributes_cache_name(self):
        return f"__{self.class_name}__".lower()

    @property
    def class_name(self):
        class_name = type(self).__name__
        return class_name

    from cached_function import cached_function

    @cached_function()
    def get_name(self, instance):
        class_object = type(instance)
        for name in dir(class_object):
            if getattr(class_object, name) == self:
                break
        else:
            logging.warning(f"Could not find {self} in {class_object}")
            name = "unknown"
        return name

    class Attributes(object):
        def __init__(self, PV_property_object, instance):
            from event_handlers import Event_Handlers
            from functools import partial
            self.handlers = Event_Handlers(
                setup=partial(PV_property_object.monitor_setup, instance),
                cleanup=partial(PV_property_object.monitor_cleanup, instance),
            )

        def __repr__(self):
            name = type(self).__qualname__
            attrs = []
            if self.handlers:
                attrs.append("handlers=%r" % (self.handlers,))
            s = "%s(%s)" % (name, ", ".join(attrs))
            return s


if __name__ == "__main__":
    import logging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # from item_reference import item_reference
    from handler import handler as _handler

    class Configuration(object):
        prefix = "BIOCARS:CONFIGURATION.METHOD"

        def __repr__(self):
            return "%s(prefix=%r)" % (type(self).__name__, self.prefix)

        current_position = PV_array_property("motor{i+1}.current_position", count="n_motors", default_value="")
        positions = PV_array_property("motor{i+1}.positions", count="n_motors", default_value=())


    self = Configuration()

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    print(f"self.positions = {self.positions}")
    print(f"self.positions[0] = {self.positions[0]}")
    print(f"self.positions[:] = {self.positions[:]}")
    # item_reference(self.positions, 0).monitors.add(report)
