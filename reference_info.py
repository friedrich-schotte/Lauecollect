"""
Author: Friedrich Schotte
Date created: 2022-06-23
Date last modified: 2022-06-23
Revision comment:
"""
__version__ = "1.0"
 
import logging
from threading import Lock


def reference_info(reference, payload_type, *args, **kwargs):
    container = attribute_or_item_reference_container(reference)
    payload_name = payload_type.__name__.lower()
    if not hasattr(container, payload_name):
        with container.lock:
            if not hasattr(container, payload_name):
                new_payload = payload_type(*args, **kwargs)
                setattr(container, payload_name, new_payload)
    payload = getattr(container, payload_name)
    return payload


def attribute_or_item_reference_container(reference):
    if hasattr(reference, "attribute_name"):
        attribute_info_base = attribute_reference_container(reference)
    elif hasattr(reference, "index"):
        attribute_info_base = item_reference_container(reference)
    else:
        raise AttributeError(f"{reference} is missing attributes 'attribute_name' or 'index'")
    return attribute_info_base


def attribute_reference_container(reference):
    obj = reference.object
    attribute_name = f"__{reference.attribute_name}__info__"
    if not hasattr(obj, attribute_name):
        with attribute_info_lock(obj):
            if not hasattr(obj, attribute_name):
                # logging.debug(f"{obj}.{attribute_name} = {Container()}")
                setattr(obj, attribute_name, Container())
    container = getattr(obj, attribute_name)
    return container


def item_reference_container(reference):
    obj = reference.object
    item = reference.index
    container_dict_name = "__item_info__"
    if not hasattr(obj, container_dict_name):
        with item_info_lock(obj):
            if not hasattr(obj, container_dict_name):
                setattr(obj, container_dict_name, {})
    container_dict = getattr(obj, container_dict_name)
    if item not in container_dict:
        with item_info_lock(obj):
            if item not in container_dict:
                # logging.debug(f"{obj}.{container_dict_name}.[{item}] = {Container()}")
                container_dict[item] = Container()
    container = container_dict[item]
    return container


def attribute_info_lock(obj):
    return object_lock(obj, "attribute_info")


def item_info_lock(obj):
    return object_lock(obj, "item_info")


def object_lock(obj, name):
    attribute_name = f"__{name}_lock__"
    if not hasattr(obj, attribute_name):
        with global_lock:
            if not hasattr(obj, attribute_name):
                lock = Lock()
                # logging.debug(f"{reference}.{attribute_name} = {lock}")
                setattr(obj, attribute_name, lock)
    lock = getattr(obj, attribute_name)
    return lock


global_lock = Lock()


class Container:
    def __init__(self):
        self.lock = Lock()

    def __repr__(self):
        return f"{self.class_name}()"

    @property
    def class_name(self):
        return type(self).__name__


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from timing_system_client import timing_system_client
    from reference import reference as _reference

    domain_name = "BioCARS"
    timing_system = timing_system_client(domain_name)
    reference = _reference(timing_system.channels.xdet.trig_count, "count")

    self = attribute_or_item_reference_container(reference)
