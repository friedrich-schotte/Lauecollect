"""
Author: Friedrich Schotte
Date created: 2022-04-30
Date last modified: 2022-04-30
Revision comment:
"""
__version__ = "1.0"

from threading import Thread

try:
    from console_thrift import KeyboardInterruptException
except ImportError:
    KeyboardInterruptException = KeyboardInterrupt


def keyboard_input():
    global input_buffer, read_input_thread

    keyboard_input = ""

    if input_buffer:
        keyboard_input = input_buffer
        input_buffer = ""
    else:
        if not read_input_thread.is_alive():
            read_input_thread = Thread(target=read_input, daemon=True)
            read_input_thread.start()

    return keyboard_input


def read_input():
    global input_buffer
    try:
        input_buffer += input()+"\n"
    except KeyboardInterruptException:
        pass


input_buffer = ""
read_input_thread = Thread()


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    print("keyboard_input()")
