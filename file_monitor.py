"""
Author: Friedrich Schotte
Date created: 2019-11-05
Date last modified: 2022-07-01
Revision comment: Cleanup: removed properties no longer needed
"""
__version__ = "1.5.5"

import logging
from traceback import format_exc
import watchdog.events

from time_string import date_time

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO


class monitor(object):
    def __init__(self, filename, handler, *args, **kwargs):
        """filename: pathname
        handler: routine to be called
        """
        self.filename = filename
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        self.file_mtime = file_mtime(self.filename)
        self.file_size = file_size(self.filename)
        # self.monitoring = True

    def call_handler(self):
        self.handler(*self.args, **self.kwargs)

    def __repr__(self):
        return "%s(%r, %s.%s, args=%r, kwargs=%r)" % (
            type(self).__name__,
            self.filename,
            self.handler.__module__,
            self.handler.__name__,
            self.args,
            self.kwargs
        )

    def __eq__(self, other):
        return (
                self.filename == getattr(other, "filename", None) and
                self.handler == getattr(other, "handler", None) and
                self.args == getattr(other, "args", None) and
                self.kwargs == getattr(other, "kwargs", None)
        )

    @property
    def monitoring(self):
        return self._monitoring

    @monitoring.setter
    def monitoring(self, monitoring):
        if bool(monitoring) != self.monitoring:
            if monitoring:
                self.file_mtime = file_mtime(self.filename)
                self.file_size = file_size(self.filename)
        self._monitoring = monitoring

    def update_monitoring(self):
        self._monitoring = False
        self._monitoring = True

    @property
    def _monitoring(self):
        return self.observer and self.observer.is_alive()

    @_monitoring.setter
    def _monitoring(self, monitoring):
        if bool(monitoring) != self.monitoring:
            if monitoring:
                from os.path import exists
                # from watchdog.observers import Observer
                from watchdog.observers.polling import PollingObserver as Observer
                silence_watchdog_messages()

                for directory_name in self.directory_names:
                    if exists(directory_name):
                        # https://stackoverflow.com/questions/18599339/python-watchdog-monitoring-file-for-changes
                        event_handler = Event_Handler(self)
                        self.observer = Observer()
                        self.observer.schedule(event_handler, path=directory_name, recursive=False)
                        logger.debug(f"Started monitoring of {directory_name!r}")
                        # noinspection PyBroadException
                        try:
                            self.observer.start()
                        except Exception:
                            logger.warning(f"{directory_name!r} ({self.observer}): {format_exc()}")
                        else:
                            self.observer.pathname = directory_name
                        break
            else:
                if self.observer:
                    # noinspection PyBroadException
                    try:
                        logger.debug(f"Stopping monitoring of {self.observer.pathname!r}")
                        self.observer.stop()
                    except Exception:
                        logger.debug(f"{self.observer.pathname!r} ({self.observer}): {format_exc()}")
                    self.observer = None

    observer = None

    @property
    def directory_names(self):
        return directory_names(self.filename)

    def handle_event(self, event):
        from os.path import exists

        logger.debug("Got %s" % event_info(event))
        self.last_event = event  # for debugging
        pathname = getattr(self.observer, "pathname", "")
        if not exists(pathname):
            logger.debug(f"Deleted: {pathname!r}")
        subdirectory = filename_subdirectory(pathname, self.filename)
        if exists(subdirectory):
            logger.debug(f"Created: {subdirectory!r}")
        mtime = file_mtime(self.filename)
        size = file_size(self.filename)
        if self.file_mtime != mtime or self.file_size != size:
            logger.debug(f"File {self.filename!r} changed ({date_time(mtime)}, {size} B)")
            self.file_mtime = mtime
            self.file_size = size
            self.call_handler()

        self.update_monitoring()

    last_event = None


class Event_Handler(watchdog.events.FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_any_event(self, event):
        self.monitor.handle_event(event)


def file_mtime(filename):
    from os.path import getmtime
    try:
        mtime = getmtime(filename)
    except OSError:
        mtime = 0
    return mtime


def file_size(filename):
    from os.path import getsize
    try:
        size = getsize(filename)
    except OSError:
        size = 0
    return size


def filename_subdirectory(pathname, filename):
    filename_subdirectory = ""
    for d in directory_names(filename):
        if d.startswith(pathname) and d != pathname:
            filename_subdirectory = d
    return filename_subdirectory


def directory_names(filename):
    from os.path import dirname
    directories = []
    directory = filename
    while directory and directory not in directories:
        directories.append(directory)
        directory = dirname(directory)
    return directories


def event_info(event):
    dest_path = getattr(event, "dest_path", "")
    info = "Event %r, %r, dest=%r" % (event.event_type, event.src_path, dest_path)
    return info


def file_monitor(filename, _events, handler, *args, **kwargs):
    new_monitor = monitor(filename, handler, *args, **kwargs)
    if new_monitor not in monitors:
        monitors.append(new_monitor)
        new_monitor.monitoring = True


def file_monitor_clear(filename, _events, handler, *args, **kwargs):
    monitor_to_remove = monitor(filename, handler, *args, **kwargs)
    for old_monitor in monitors:
        if old_monitor == monitor_to_remove:
            old_monitor.monitoring = False
    while monitor_to_remove in monitors:
        monitors.remove(monitor_to_remove)


def file_monitors(filename):
    return [monitor.handler for monitor in monitors if monitor.filename == filename]


def all_file_monitors():
    from handler import Handler
    all_monitors = {}
    for monitor in monitors:
        filename = monitor.filename
        handler = Handler(monitor.handler, *monitor.args, **monitor.kwargs)
        if filename not in all_monitors:
            all_monitors[filename] = set()
        all_monitors[filename].add(handler)
    return all_monitors


monitors = []


def silence_watchdog_messages():
    # Turn off a deluge of debug messages in "watchdog" module
    # site-packages/watchdog/observers/inotify_buffer.py. line 62:
    # logger.debug("in-event %s", inotify_event)
    import logging
    logging.getLogger("watchdog.observers.inotify_buffer").level = logging.INFO
    logging.getLogger("watchdog.observers.fsevents").level = logging.INFO


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level, format=msg_format)
    logging.getLogger(__name__).level = level

    # from tempfile import gettempdir
    # filename = gettempdir() + "/test.txt"
    # filename = '/tmp/test1/test2/test3.txt'
    filename = '//femto/C/All Projects/APS/Instrumentation/Software/Lauecollect/settings/test_settings.txt'


    def handle_change(filename):
        logging.info(f"{filename!r} changed")


    print('file_monitor(filename, "created,modified,deleted,moved", handle_change, filename)')
    file_monitor(filename, "created,modified,deleted,moved", handle_change, filename)
    # print('open(filename,"a").write("test\\n")')
    # print('from os import remove; remove(filename)')
    # print('file_monitor_clear(filename,"created,modified,deleted,moved",handle_change,filename)')
