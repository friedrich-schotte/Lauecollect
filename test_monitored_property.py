#!/usr/bin/env python
"""
Push notifications
Author: Friedrich Schotte
Date created: 2020-09-17
Date last modified: 2021-03-10
Revision comment: Fixed: monitors.add
"""
__version__ = "1.0.2"

import logging
from logging import info

import pytest

from handler import handler
from monitored_property import monitored_property
from reference import reference

fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=fmt)


def test_fget(example):
    assert example.count == 0


def test_fset(example):
    example.count = 1
    assert example.count == 1


def test_value(example):
    assert example.value == example.count + 1


def test_monitor(example_monitoring_value):
    assert len(reference(example_monitoring_value, "value").monitors) == 1
    assert len(reference(example_monitoring_value, "count").monitors) == 1


def test_monitoring_value_fset_old_style(example_monitoring_value, report):
    report.reset()

    example_monitoring_value.count += 1
    example_monitoring_value.count += 0

    assert report.obj == example_monitoring_value
    assert report.attr == "value"
    assert report.count == 1
    assert report.value == 2


def test_monitoring_value_old_style_fset_old_style(example_monitoring_value_old_style, report):
    report.reset()

    example_monitoring_value_old_style.count += 1
    example_monitoring_value_old_style.count += 0

    assert report.obj == example_monitoring_value_old_style
    assert report.attr == "value_old_style"
    assert report.count == 1
    assert report.value == 2


def test_add_monitor(monitored_value, monitored_count):
    assert len(monitored_value.monitors) == 1
    assert len(monitored_count.monitors) == 2


def test_remove_monitor(monitored_value, monitored_count, report_handler):
    monitored_value.monitors.remove(report_handler)
    monitored_count.monitors.remove(report_handler)
    assert len(monitored_value.monitors) == 0
    assert len(monitored_count.monitors) == 0


def test_monitored_fset_new_style(monitored_value, monitored_count, example, report):
    example.count += 1
    example.count += 0

    assert report.count == 2
    if report.reference == monitored_count:
        assert report.value == 1
    if report.reference == monitored_value:
        assert report.value == 2


def test_monitored_value_old_style_fset_new_style(monitored_value_old_style, monitored_count, example, report):
    example.count += 1
    example.count += 0

    assert report.count == 2
    if report.reference == monitored_count:
        assert report.value == 1
    if report.reference == monitored_value_old_style:
        assert report.value == 2


@pytest.fixture()
def example():
    example = Example()
    yield example


@pytest.fixture()
def value(example):
    value = reference(example, "value")
    yield value


@pytest.fixture()
def value_old_style(example):
    value = reference(example, "value_old_style")
    yield value


@pytest.fixture()
def count(example):
    count = reference(example, "count")
    yield count


@pytest.fixture()
def monitored_value(value, report_handler):
    value.monitors.add(report_handler)
    yield value
    value.monitors.remove(report_handler)


@pytest.fixture()
def monitored_value_old_style(value_old_style, report_handler):
    value_old_style.monitors.add(report_handler)
    yield value
    value_old_style.monitors.remove(report_handler)


@pytest.fixture()
def monitored_count(count, report_handler):
    count.monitors.add(report_handler)
    yield count
    count.monitors.remove(report_handler)


@pytest.fixture()
def report_handler(report):
    report_handler = handler(report_event, report, new_thread=False)
    yield report_handler


@pytest.fixture()
def report(example):
    report = Report()
    yield report


@pytest.fixture()
def example_monitoring_value(example, report):
    reference(example, "value").monitors.add(handler(generate_report, example, "value", report, new_thread=False))
    yield example
    reference(example, "value").monitors.remove(handler(generate_report, example, "value", report, new_thread=False))


@pytest.fixture()
def example_monitoring_value_old_style(example, report):
    reference(example, "value_old_style").monitors.add(handler(generate_report, example, "value_old_style", report, new_thread=False))
    yield example
    reference(example, "value_old_style").monitors.remove(handler(generate_report, example, "value_old_style", report, new_thread=False))


class Example(object):
    def __repr__(self):
        return "%s()" % type(self).__name__

    def reset(self):
        self.count = 0

    from monitored_value_property import monitored_value_property
    count = monitored_value_property(default_value=0)

    def input_references_value(self):
        from reference import reference
        return [reference(self, "count")]

    def calculate_value(self, count):
        value = count + 1
        # debug("calculated value = %r" % value)
        return value

    def set_value(self, value):
        self.count = value - 1

    value = monitored_property(
        input_references=input_references_value,
        calculate=calculate_value,
        fset=set_value,
    )

    def get_value(self):  # for backward compatibility
        value = self.count + 1
        # debug("value = %r" % value)
        return value

    def inputs_value(self):  # for backward compatibility
        return [(self, "count")]

    value_old_style = monitored_property(
        fget=get_value,
        fset=set_value,
        inputs=inputs_value,
    )


class Report:
    def __init__(self):
        self.obj = None
        self.attr = None
        self.value = None
        self.count = 0
        self.reference = None

    def reset(self):
        self.__init__()


def generate_report(obj, attr, report):
    value = getattr(obj, attr)
    info("%r.%s = %r" % (obj, attr, value))
    report.obj = obj
    report.attr = attr
    report.value = value
    report.count += 1


def report_event(report, event=None):
    if event is not None:
        info("event = %r" % event)
        report.value = event.value
        report.reference = event.reference
    report.count += 1
