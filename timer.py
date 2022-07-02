#!/usr/bin/env python
"""
Authors: Friedrich Schotte
Date created: 2021-01-29
Date last modified: 2021-01-29
Revision comment:
"""
__version__ = "1.0"


class timer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def get_running(self):
        return self._timer is not None

    def set_running(self, value):
        if value:
            self.start()
        else:
            self.stop()

    running = property(get_running, set_running)

    def start(self):
        if not self.running:
            self._start()

    def stop(self):
        if self._timer:
            self._timer.cancel()
        self._timer = None

    def _start(self):
        from threading import Timer
        self._timer = Timer(self.interval, self._run)
        self._timer.start()

    def _run(self):
        self.function(*self.args, **self.kwargs)
        self._timer = None


if __name__ == "__main__":
    def hello(name): print("Hello %s!" % name)


    timer = timer(1, hello, "World")
    print('timer.start()')
    print('timer.stop()')
    print('')
    print('timer.running = True')
    print('timer.running')
    print('timer.running = False')
