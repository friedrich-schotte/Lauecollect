"""
Author: Friedrich Schotte
Date created: 2020-11-11
Date last modified: 2020-12-01
Revision comment: Refactored: Top-level imports
"""
__version__ = "1.0.2"

from logging import info

from cached_function import cached_function


@cached_function()
def dynamic_reference(reference, attribute_name):
    return Dynamic_Reference(reference, attribute_name)


class Dynamic_Reference:
    def __init__(self, reference, attribute_name):
        self.reference = reference
        self.attribute_name = attribute_name
        from event_handlers import Event_Handlers
        self.monitors = Event_Handlers(
            setup=self.setup,
            cleanup=self.cleanup,
        )
        self.reference_to_monitor = None
        
    def __repr__(self):
        name = type(self).__name__.lower()
        return "%s(%r,%r)" % (name, self.reference, self.attribute_name,)

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.reference == getattr(other, "reference", None),
            self.attribute_name == getattr(other, "attribute_name", None),
        ])

    def __hash__(self): return hash(repr(self))

    @property
    def object(self):
        return self.reference.value

    def setup(self):
        from reference import reference
        self.reference_to_monitor = reference(self.object, self.attribute_name)
        from handler import handler
        self.reference_to_monitor.monitors.add(handler(self.handle_change))
        self.reference.monitors.add(handler(self.handle_reference_change))
    
    def cleanup(self):
        from handler import handler
        if self.reference_to_monitor:
            self.reference_to_monitor.monitors.remove(handler(self.handle_change))
            self.reference_to_monitor = None
        self.reference.monitors.remove(handler(self.handle_reference_change))

    def handle_change(self, event):
        from event import event as event_object
        new_event = event_object(time=event.time, value=event.value, reference=self)
        self.monitors.call(new_event)

    def handle_reference_change(self, event):
        self.reference_to_monitor.monitors.remove(self.handle_change)
        from reference import reference
        self.reference_to_monitor = reference(self.object, self.attribute_name)
        self.reference_to_monitor.monitors.add(self.handle_change)
        from event import event as event_object
        new_event = event_object(time=event.time, value=self.value, reference=self.object)
        self.handle_change(new_event)

    def get_value(self):
        return getattr(self.object, self.attribute_name)

    def set_value(self, value):
        setattr(self.object, self.attribute_name, value)

    value = property(get_value, set_value)


if __name__ == "__main__":
    # from pdb import pm
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    from reference import reference as _reference
    from handler import handler as _handler

    class Example:
        from db_property import db_property
        from monitored_property import monitored_property

        filename = db_property("filename", "/tmp/test.txt")

        def __repr__(self):
            return f"{type(self).__name__}()"

        def inputs_file(self):
            from reference import reference
            return [reference(self, "filename")]

        def calculate_file(self, filename):
            from file import file
            return file(filename)

        file = monitored_property(
            inputs=inputs_file,
            calculate=calculate_file,
        )

        def inputs_file_content(self):
            from reference import reference
            return [dynamic_reference(reference(self, "file"), "content")]

        def calculate_file_content(self, content):
            return content

        file_content = monitored_property(
            inputs=inputs_file_content,
            calculate=calculate_file_content,
        )

    example = Example()


    @_handler
    def report(event=None):
        info(f"event={event}")

    _reference(example, "filename").monitors.add(report)
    _reference(example, "file").monitors.add(report)
    _reference(example, "file_content").monitors.add(report)
    print(f"example.filename = {example.filename!r}")
    print(f"example.file_content = {example.file_content!r}")
