"""
Author: Friedrich Schotte
Date created: 2018-01-25
Date last modified: 2021-09-21
Revision comment: Suppressing debug messages from "watchdog" module
"""
__version__ = "0.0.4"


class monitor(object):
    """For Linux and MacOS
    Is compatible with Windows XP, but has poor performance:
    "Failed to import read_directory_changes. Fall back to polling"
    """
    from thread_property_2 import thread_property

    def __init__(self, directory, handler, *args, **kwargs):
        """directory: pathname
        handler: routine to be called
        """
        self.directory = directory
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        # self.monitoring = True

    def __repr__(self):
        return f"{self.class_name}({self.directory}, {self.handler}, {self.args}, {self.kwargs})"

    @property
    def class_name(self):
        return type(self).__name__

    def __eq__(self, other):
        return (self.directory == other.directory and
                self.handler == other.handler and
                self.args == other.args and
                self.kwargs == other.kwargs)

    @property
    def monitoring(self):
        return getattr(self, self.monitoring_property)

    @monitoring.setter
    def monitoring(self, value):
        setattr(self, self.monitoring_property, value)

    @property
    def monitoring_property(self):
        from sys import platform
        return "monitoring_win32" if platform == "win32" else "monitoring_posix"

    @property
    def monitoring_posix(self):
        """Watching trace directory for new files?"""
        return self.observer and self.observer.is_alive()

    @monitoring_posix.setter
    def monitoring_posix(self, value):
        if bool(value) != self.monitoring_posix:
            if value:
                # Turn off a deluge of debug messages in "watchdog" module
                # site-packages/watchdog/observers/inotify_buffer.py. line 62:
                # logger.debug("in-event %s", inotify_event)
                import logging
                logging.getLogger("watchdog.observers.inotify_buffer").level = logging.INFO
                logging.getLogger("watchdog.observers.fsevents").level = logging.INFO
                # https://stackoverflow.com/questions/18599339/python-watchdog-monitoring-file-for-changes
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler

                class MyHandler(FileSystemEventHandler):
                    def on_modified(handler, _event):
                        self.handler(*self.args, **self.kwargs)

                event_handler = MyHandler()
                self.observer = Observer()
                self.observer.schedule(event_handler, path=self.directory, recursive=False)
                self.observer.start()
            else:
                if self.observer:
                    self.observer.stop()

    observer = None

    @thread_property
    def monitoring_win32(self):
        """Watch trace directory for new files (Windows only)"""
        while not self.monitoring_win32_cancelled:
            from os.path import exists
            from time import sleep
            if not exists(self.directory):
                sleep(1)
            else:
                # watchdog: "Failed to import read_directory_changes. Fall back to polling"
                # http://code.activestate.com/recipes/156178-watching-a-directory-under-win32/
                import win32file
                import win32event
                import win32con
                flags = 0 \
                    | win32con.FILE_NOTIFY_CHANGE_FILE_NAME \
                    | win32con.FILE_NOTIFY_CHANGE_DIR_NAME \
                    | win32con.FILE_NOTIFY_CHANGE_SIZE \
                    # | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES\
                # | win32con.FILE_NOTIFY_CHANGE_SECURITY
                # | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE\
                change_handle = win32file.FindFirstChangeNotification(directory, 0, flags)
                try:
                    while not self.monitoring_win32_cancelled:
                        result = win32event.WaitForSingleObject(change_handle, 500)
                        if result == win32con.WAIT_OBJECT_0:
                            self.handler(*self.args, **self.kwargs)
                            win32file.FindNextChangeNotification(change_handle)
                finally:
                    win32file.FindCloseChangeNotification(change_handle)

    monitoring_win32_cancelled = False


def directory_monitor(directory, handler, *args, **kwargs):
    new_monitor = monitor(directory, handler, *args, **kwargs)
    if new_monitor not in monitors:
        monitors.append(new_monitor)
        new_monitor.monitoring = True


def directory_monitor_clear(directory, handler, *args, **kwargs):
    monitor_to_remove = monitor(directory, handler, *args, **kwargs)
    for old_monitor in monitors:
        if old_monitor == monitor_to_remove:
            old_monitor.monitoring = False
    while monitor_to_remove in monitors:
        monitors.remove(monitor_to_remove)


def directory_monitors(directory):
    return [monitor.handler for monitor in monitors if monitor.directory == directory]


monitors = []

if __name__ == "__main__":
    import logging
    from tempfile import gettempdir as _gettempdir
    from file import file as _file
    from os import remove as _remove

    directory = _gettempdir()+"/test"
    # directory = "/net/mx340hs/data/tmp"
    # directory = '//femto/C/All Projects/APS/Experiments/2019.12/Test/Logfiles'
    filename = directory + '/test.log'


    def handle_change(directory):
        logging.warning("%r changed" % directory)


    # print('monitors.append(monitor(directory,handle_change,directory))')
    # print('directory_monitor(filename,handle_change,filename)')
    print('directory_monitor(directory,handle_change,directory)')
    print('directory_monitor_clear(directory,handle_change,directory)')
    print('directory_monitors(directory)')
    print('')
    print('_file(filename).content = "test\\n"')
    print('_file(filename).content = ""')
    print('_remove(filename)')
