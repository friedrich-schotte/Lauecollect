#!/usr/bin/env python
"""
Simply use "@run_async" as a decorator for the function you want to run 
asynchronously. A call to that function will return immediately but the 
function itself will run in parallel.

https://code.activestate.com/recipes/576684-simple-threading-decorator/

Author: David Gaarenstroom 
Date created: 2009-03-08
Date last modified: 2022-05-02
Revision comment: Formatting, spelling
"""
__version__ = "1.0.1"


def run_async(func):
    """
    function decorator, intended to make "func" run in a separate
    thread (asynchronously).
    Returns the created Thread object

    E.g.:
    @run_async
    def task1():
        do_something

    @run_async
    def task2():
        do_something_too

    t1 = task1()
    t2 = task2()
    ...
    t1.join()
    t2.join()
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    return async_func


if __name__ == '__main__':
    from time import sleep


    @run_async
    def print_some_data():
        print('starting print_some_data')
        sleep(2)
        print('print_some_data: 2 sec passed')
        sleep(2)
        print('print_some_data: 2 sec passed')
        sleep(2)
        print('finished print_some_data')


    def main():
        print_some_data()
        print('back in main')
        print_some_data()
        print('back in main')
        print_some_data()
        print('back in main')


    print("main()")
