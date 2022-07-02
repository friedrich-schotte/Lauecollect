#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-17
Date last modified: 2020-12-23
Revision comment: Fixed item_reference; shortened __repr__
"""
__version__ = "1.1.3"

from logging import warning, error


class indexable_property(property):
    parameter_names = [
        "get_all_function",
        "set_all_function",
        "getitem_function",
        "setitem_function",
        "get_count_function",
    ]

    def __init__(
            self,
            get_all_function=None,
            set_all_function=None,
            getitem_function=None,
            setitem_function=None,
            get_count_function=None,
    ):
        self.get_all_function = get_all_function
        self.set_all_function = set_all_function
        self.getitem_function = getitem_function
        self.setitem_function = setitem_function
        self.get_count_function = get_count_function
        property.__init__(
            self,
            fget=self.get_value,
            fset=self.set_value,
        )

    def __repr__(self):
        return f"{self.class_name}({self.parameter_repr})"

    def getter(self, get_all_function):
        """Intended to be used as decorator"""
        self.get_all_function = get_all_function
        return self

    def setter(self, set_all_function):
        """Intended to be used as decorator"""
        # Issue: PyCharm: "Getter signature should be (self)"
        self.set_all_function = set_all_function
        return self

    def get_all(self, get_all_function):
        """Intended to be used as decorator"""
        self.get_all_function = get_all_function
        return self

    def set_all(self, set_all_function):
        """Intended to be used as decorator"""
        self.set_all_function = set_all_function
        return self

    def getitem(self, getitem_function):
        """Intended to be used as decorator"""
        self.getitem_function = getitem_function
        return self

    def setitem(self, setitem_function):
        """Intended to be used as decorator"""
        self.setitem_function = setitem_function
        return self

    def count(self, get_count_function):
        """Intended to be used as decorator"""
        self.get_count_function = get_count_function
        return self

    def get_value(self, instance):
        return self.attributes(instance)

    def set_value(self, instance, value):
        self.get_value(instance)[:] = value

    def monitors(self, instance):
        return self.get_value(instance).monitors

    @property
    def class_name(self):
        return type(self).__name__

    def get_name(self, instance):
        if not self.__property_name__:
            class_object = type(instance)
            for name in dir(class_object):
                if getattr(class_object, name) == self:
                    break
            else:
                warning(f"Could not find {self} in {class_object}")
                name = "unknown"
            self.__property_name__ = name
        return self.__property_name__

    __property_name__ = ""

    @property
    def parameter_repr(self):
        parameter_list = []
        for name in self.parameter_names:
            if getattr(self, name):
                parameter_list.append(f"{name}={func_repr(getattr(self, name))}")
        parameter_repr = ", ".join(parameter_list)
        return parameter_repr

    def attributes(self, instance):
        attributes_cache = self.attributes_cache(instance)
        name = self.get_name(instance)
        if name not in attributes_cache:
            attributes_cache[name] = self.new_attributes_object(instance)
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

    def new_attributes_object(self, instance):
        return Indexable_Object(
            obj=instance,
            get_count_function=self.get_count_function,
            getitem_function=self.getitem_function,
            setitem_function=self.setitem_function,
            get_all_function=self.get_all_function,
            set_all_function=self.set_all_function,
            name=self.get_name(instance),
        )


class Indexable_Object:
    parameter_names = [
        "object",
        "get_all_function",
        "set_all_function",
        "getitem_function",
        "setitem_function",
        "get_count_function",
        "name",
    ]

    def __init__(
            self,
            obj,
            get_all_function=None,
            set_all_function=None,
            getitem_function=None,
            setitem_function=None,
            get_count_function=None,
            name="unknown",
    ):
        self.object = obj
        self.get_all_function = get_all_function
        self.set_all_function = set_all_function
        self.getitem_function = getitem_function
        self.setitem_function = setitem_function
        self.get_count_function = get_count_function
        self.name = name

        self.cached_values = []
        self.cached_input_value_dict = {}

        self.item_monitors = {}

        from event_handlers import Event_Handlers
        self.monitors = Event_Handlers(setup=self.monitor_setup)

        if self.getitem_function and self.get_all_function:
            warning(f"{self}: If 'get_all' is defined 'getitem' will never be called.")

    def __repr__(self):
        return f"{self.object}.{self.name}"
        # return f"{self.class_name}({self.parameter_repr})"

    def __getitem__(self, i):
        if type(i) == slice:
            value = self.get_all()
        else:
            value = self.getitem(i)
        return value

    def __setitem__(self, i, value):
        if type(i) == slice:
            self.set_all(value)
        elif value != self[i]:
            self.setitem(i, value)

    def __getitem_monitors__(self, i):
        if type(i) == slice:
            monitors = self.monitors
        else:
            monitors = self.get_item_monitors(i)
        return monitors

    @property
    def __all_items_monitors__(self):
        return self.monitors

    def __len__(self):
        return self.count

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def getitem(self, i):
        self.monitor_setup()
        if self.caching_values and self.monitoring_inputs:
            value = self.getitem_cached(i)
        else:
            value = self.getitem_live(i)
        return value

    def getitem_cached(self, i):
        value = self.get_cached_item(i)
        return value

    def getitem_live(self, i):
        if self.get_all_function:
            value = self.get_all()[i]
        elif self.getitem_function:
            value = self.calculate_item(i, *self.getitem_input_values)
        else:
            error(f"{self}: Neither 'get_all' not 'getitem' are defined.")
            value = None
        return value

    def get_all(self):
        self.monitor_setup()
        if self.caching_values and self.monitoring_inputs:
            values = self.get_all_cached()
        else:
            values = self.get_all_live()
        return values

    def get_all_cached(self):
        values = self.get_cached_values()
        return values

    def get_all_live(self):
        if self.get_all_function:
            values = self.calculate_all(*self.get_all_input_values)
        elif self.getitem_function:
            values = [self.getitem(i) for i in range(0, len(self))]
        else:
            error(f"{self}: Neither 'get_all' not 'getitem' are defined.")
            values = []
        return values

    def calculate_item(self, i, *getitem_input_values):
        value = self.getitem_function(self.object, i, *getitem_input_values)
        # debug(f'{self.getitem_function.__qualname__}({self.object}, {i}, {getitem_input_values}): {value}')
        return value

    def calculate_all(self, *get_all_input_values):
        values = self.get_all_function(self.object, *get_all_input_values)
        # debug(f'{self.get_all_function.__qualname__}({self.object},{get_all_input_values}): {values}')
        return values

    def setitem(self, i, value):
        if self.setitem_function:
            # debug(f'Calling {self.setitem_function.__qualname__}({self.object}, {i}, {value})')
            self.setitem_function(self.object, i, value)
        elif self.set_all_function:
            values = self[:]
            values[i] = value
            # debug(f'Calling {self.set_all_function.__qualname__}({self.object}, {values})')
            self.set_all_function(self.object, values)
        else:
            error(f"{self}[{i}] cannot be changed.")

    def set_all(self, values):
        if self.set_all_function:
            # debug(f'Calling {self.set_all_function.__qualname__}({self.object}, {values})')
            self.set_all_function(self.object, values)
        else:
            for i in range(0, len(values)):
                self[i] = values[i]

    def get_item_monitors(self, i):
        from event_handlers import Event_Handlers
        if i not in self.item_monitors:
            self.item_monitors[i] = Event_Handlers(setup=self.monitor_setup)
        monitors = self.item_monitors[i]
        return monitors

    @property
    def count(self):
        if self.get_count_function:
            count = self.get_count_function(self.object, *self.count_input_values)
        elif self.get_all_function:
            values = self.get_all_function(self.object, *self.get_all_input_values)
            count = len(values)
        else:
            error(f"{self}: 'get_count_function' is not defined")
            count = 0
        return count

    @property
    def getitem_input_values(self):
        if self.monitoring_getitem_inputs:
            values = self.getitem_cached_input_values
        else:
            values = self.getitem_live_input_values
        return values

    @property
    def get_all_input_values(self):
        if self.monitoring_get_all_inputs:
            values = self.get_all_cached_input_values
        else:
            values = self.get_all_live_input_values
        return values

    @property
    def getitem_live_input_values(self):
        return [getattr(self.object, name) for name in self.getitem_input_names]

    @property
    def get_all_live_input_values(self):
        return [getattr(self.object, name) for name in self.get_all_input_names]

    @property
    def getitem_cached_input_values(self):
        return self.get_cached_input_values(self.getitem_input_names)

    @getitem_cached_input_values.setter
    def getitem_cached_input_values(self, values):
        self.set_cached_input_values(self.getitem_input_names, values)

    @property
    def get_all_cached_input_values(self):
        return self.get_cached_input_values(self.get_all_input_names)

    @get_all_cached_input_values.setter
    def get_all_cached_input_values(self, values):
        self.set_cached_input_values(self.get_all_input_names, values)

    def get_cached_input_values(self, input_names):
        values = []
        for name in input_names:
            if name in self.cached_input_value_dict:
                value = self.cached_input_value_dict[name]
            else:
                warning(f"{self.object}.{name} not cached")
                value = getattr(self.object, name)
            values.append(value)
        return values

    def set_cached_input_values(self, input_names, values):
        if len(values) == 0:
            for name in input_names:
                if name in self.cached_input_value_dict:
                    del self.cached_input_value_dict[name]
        else:
            for name, value in zip(input_names, values):
                self.cached_input_value_dict[name] = value

    @property
    def count_input_values(self):
        return [getattr(self.object, name) for name in self.count_input_names]

    @property
    def getitem_input_names(self):
        if self.getitem_function:
            from inspect import signature
            names = list(signature(self.getitem_function).parameters)
            names = names[2:]
        else:
            names = []
        return names

    @property
    def get_all_input_names(self):
        if self.get_all_function:
            from inspect import signature
            names = list(signature(self.get_all_function).parameters)
            names = names[1:]
        else:
            names = []
        return names

    @property
    def count_input_names(self):
        if self.get_count_function:
            from inspect import signature
            names = list(signature(self.get_count_function).parameters)
            names = names[1:]
        else:
            names = []
        return names

    def monitor_setup(self):
        self.caching_values = True
        self.monitoring_inputs = True

    @property
    def monitoring_inputs(self):
        if self.get_all_function:
            monitoring = self.monitoring_get_all_inputs
        elif self.getitem_function:
            monitoring = self.monitoring_getitem_inputs
        else:
            error(f"{self}: Neither 'get_all' not 'getitem' are defined.")
            monitoring = False
        return monitoring

    @monitoring_inputs.setter
    def monitoring_inputs(self, monitoring):
        if self.get_all_function:
            self.monitoring_get_all_inputs = monitoring
        elif self.getitem_function:
            self.monitoring_getitem_inputs = monitoring
        else:
            error(f"{self}: Neither 'get_all' not 'getitem' are defined.")

    @property
    def caching_values(self):
        return self.is_cached_values()

    @caching_values.setter
    def caching_values(self, caching_values):
        if caching_values != self.caching_values:
            if caching_values:
                self.set_cached_values(self.get_all_live())
            else:
                self.clear_cached_values()

    @property
    def monitoring_getitem_inputs(self):
        all_monitoring = []
        for i, input_reference in enumerate(self.getitem_input_references):
            monitoring = self.getitem_input_handler(i) in input_reference.monitors
            all_monitoring.append(monitoring)
        return any(all_monitoring)

    @monitoring_getitem_inputs.setter
    def monitoring_getitem_inputs(self, value):
        if self.monitoring_getitem_inputs != value:
            if value:
                self.getitem_cached_input_values = self.getitem_live_input_values
                for i, input_reference in enumerate(self.getitem_input_references):
                    from handler import handler
                    input_reference.monitors.add(self.getitem_input_handler(i))
            else:
                for i, input_reference in enumerate(self.getitem_input_references):
                    input_reference.monitors.remove(self.getitem_input_handler(i))
                self.getitem_cached_input_values = []

    @property
    def monitoring_get_all_inputs(self):
        all_monitoring = []
        for i, input_reference in enumerate(self.get_all_input_references):
            monitoring = self.get_all_input_handler(i) in input_reference.monitors
            all_monitoring.append(monitoring)
        return any(all_monitoring)

    @monitoring_get_all_inputs.setter
    def monitoring_get_all_inputs(self, value):
        if self.monitoring_get_all_inputs != value:
            if value:
                self.get_all_cached_input_values = self.get_all_live_input_values
                for i, input_reference in enumerate(self.get_all_input_references):
                    from handler import handler
                    input_reference.monitors.add(self.get_all_input_handler(i))
            else:
                for i, input_reference in enumerate(self.get_all_input_references):
                    input_reference.monitors.remove(self.get_all_input_handler(i))
                self.get_all_cached_input_values = []

    def getitem_input_handler(self, i_input):
        from handler import handler
        return handler(self.handle_getitem_input_change, i_input)

    def get_all_input_handler(self, i_input):
        from handler import handler
        return handler(self.handle_get_all_input_change, i_input)

    def handle_getitem_input_change(self, i_input, event):
        getitem_input_values = self.getitem_cached_input_values
        getitem_input_values[i_input] = event.value
        self.getitem_cached_input_values = getitem_input_values

        values = [self.calculate_item(i, *getitem_input_values)
                  for i in range(0, len(self))]

        self.generate_events(event, values)
        self.set_cached_values(values)

    def handle_get_all_input_change(self, i_input, event):
        # debug(f"{self}: {i_input}, {event}")
        get_all_input_values = self.get_all_cached_input_values
        get_all_input_values[i_input] = event.value
        self.get_all_cached_input_values = get_all_input_values

        values = self.calculate_all(*get_all_input_values)

        self.generate_events(event, values)
        self.set_cached_values(values)

    def generate_events(self, event, values):
        from same import same
        property_object = getattr(self.object, self.name)
        for i in list(self.item_monitors):
            if not same(values[i], self.get_cached_item(i)):
                from event import event as event_object
                from item_reference import item_reference
                new_event = event_object(
                    time=event.time,
                    value=values[i],
                    reference=item_reference(property_object, i),
                )
                # debug(f"new_event={new_event}")
                self.item_monitors[i].call(event=new_event)
        if not same(values, self.get_cached_values()):
            from event import event as event_object
            from reference import reference
            new_event = event_object(
                time=event.time,
                value=values,
                reference=reference(self.object, self.name),
            )
            # debug(f"new_event={new_event}")
            self.monitors.call(event=new_event)

    @property
    def getitem_input_references(self):
        from reference import reference
        return [reference(self.object, name) for name in self.getitem_input_names]

    @property
    def get_all_input_references(self):
        from reference import reference
        return [reference(self.object, name) for name in self.get_all_input_names]

    def set_cached_values(self, values):
        self.cached_values = list(values)

    def get_cached_values(self):
        return list(self.cached_values)

    def clear_cached_values(self):
        self.cached_values = []

    def is_cached_values(self):
        return all([
            len(self.cached_values) > 0,
            not any([value is None for value in self.cached_values]),
        ])

    def set_cached_item(self, i, value):
        while not i < len(self.cached_values):
            self.cached_values.append([None])
        self.cached_values[i] = value

    def get_cached_item(self, i):
        if i < len(self.cached_values):
            value = self.cached_values[i]
        else:
            value = None
        return value

    def clear_cached_item(self, i):
        if i < len(self.cached_values):
            self.cached_values[i] = None


def func_repr(f):
    if hasattr(f, "__qualname__"):
        s = getattr(f, "__qualname__")
    else:
        s = repr(f)
    return s
