"""
Save new thread

Authors: Valentyn Stadnytskyi
Date created: Oct 22 2019
Date last modified: 2019-10-22
Python Version: 2.7, 3.6
"""

def new_thread(function, daemon=True,  *args , **kwargs):
    """
    launches the input 'function' in a separate thread with daemon == True.

    Explanation: Some threads do background tasks, like sending keepalive packets, or performing periodic garbage collection, or whatever. These are only useful when the main program is running, and it's okay to kill them off once the other, non-daemon, threads have exited.

    Without daemon threads, you'd have to keep track of them, and tell them to exit, before your program can completely quit. By setting them as daemon threads, you can let them run and forget about them, and when your program quits, any daemon threads are killed automatically.
    @Chris Jester-Young https://stackoverflow.com/a/190017/8436767

    Parameters
    ----------
    function:
        function object
    *args:
        iterable of arguments
    daemon:
        flag, if the thread is daemon(True) or not(False).
    **kwargs:
        dictionary of keywords


    Returns
    -------
    thread:
        thread object

    Examples
    --------
    the example of usage

    >>> def func(*args,**kwargs):
            from time import time,sleep
            t1 = time()
            sleep(N)
            t2 = time()
            print('this thread slept for {} seconds'.format(t2-t1))
            print('input parameters: args = {}, kwargs = {!r}'.format(args[0],kwargs['keyword']))
    >>> start_new_safe_thread(func, 1, keyword = 'this is key 1 value')
    this thread slept for 1.002244234085083 seconds
    input parameters: args = 1, kwargs = 'keywords argument'

    """
    from threading import Thread
    thread = Thread(target=function, args = args, kwargs = kwargs)
    thread.daemon = daemon
    thread.start()
    return thread
