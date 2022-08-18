"""
Author: Friedrich Schotte
Date created: 2021-01-17
Date last modified: 2022-08-07
Revision comment: Using silence_watchdog_messages
"""
__version__ = "1.0.8"

import logging

from cached_function import cached_function
from event_handlers import Event_Handlers

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO


class Directory_Files_Property(property):
    def __init__(self):
        super().__init__(fget=self.get_property, fset=self.set_property)

    def __repr__(self):
        return f"{self.class_name}()"

    def get_property(self, directory):
        return directory_files_monitors(directory.name).files

    def set_property(self, directory, files):
        directory_files_monitors(directory.name).files = files

    def monitors(self, directory):
        return directory_files_monitors(directory.name)

    @property
    def class_name(self):
        return type(self).__name__


@cached_function()
def directory(name):
    return Directory(name)


class Directory(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    files = Directory_Files_Property()

    @property
    def class_name(self):
        return type(self).__name__.lower()


@cached_function()
def directory_files_monitors(name):
    return Directory_Files_Monitors(name)


class Directory_Files_Monitors(Event_Handlers):
    from thread_property_2 import thread_property

    def __init__(self, directory):
        self.directory_name = directory
        super().__init__(
            setup=self.setup,
            cleanup=self.cleanup,
        )

    def __repr__(self):
        return f"{self.class_name}({self.directory_name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    def setup(self):
        self.monitoring = True

    def cleanup(self):
        self.monitoring = False

    @property
    def monitoring(self):
        return self.monitoring_if_exists

    @monitoring.setter
    def monitoring(self, value):
        from os.path import exists

        if value:
            if exists(self.directory_name):
                self.monitoring_if_exists = True
            self.monitoring_parent_directory = True
        else:
            self.monitoring_if_exists = False
            self.monitoring_parent_directory = False

    @property
    def monitoring_parent_directory(self):
        return self.parent_directory_handler in self.parent_directory_monitors

    @monitoring_parent_directory.setter
    def monitoring_parent_directory(self, value):
        if value:
            self.parent_directory_monitors.add(self.parent_directory_handler)
        else:
            self.parent_directory_monitors.remove(self.parent_directory_handler)

    @property
    def parent_directory_monitors(self):
        from reference import reference
        return reference(self.parent_directory, "files").monitors

    @property
    def parent_directory_handler(self):
        from handler import handler
        return handler(self.handle_parent_directory_update)

    def handle_parent_directory_update(self):
        from os.path import exists
        if exists(self.directory_name):
            if not self.monitoring_if_exists:
                self.call(event=self.event)
            self.monitoring_if_exists = True
        else:
            if self.monitoring_if_exists:
                self.call(event=self.event)
            self.monitoring_if_exists = False

    @property
    def directory(self):
        return directory(self.directory_name)

    @property
    def parent_directory(self):
        return directory(self.parent_directory_name)

    @property
    def parent_directory_name(self):
        from pathlib import Path
        name = str(Path(self.directory_name).parent.absolute())
        return name

    @property
    def monitoring_if_exists(self):
        return getattr(self, self.monitoring_property)

    @monitoring_if_exists.setter
    def monitoring_if_exists(self, value):
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
                from silence_watchdog_messages import silence_watchdog_messages
                silence_watchdog_messages()
                # https://stackoverflow.com/questions/18599339/python-watchdog-monitoring-file-for-changes
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler

                class MyHandler(FileSystemEventHandler):
                    def __init__(self, monitors):
                        super().__init__()
                        self.monitors = monitors

                    def on_modified(self, _event):
                        # logger.debug(f"{self.monitors.directory_name!r} changed")
                        self.monitors.call(event=self.monitors.event)

                event_handler = MyHandler(self)
                self.observer = Observer()
                # logger.debug(f"Monitoring {self.directory_name!r}")
                self.observer.schedule(event_handler, path=self.directory_name, recursive=False)
                try:
                    self.observer.start()
                except OSError as x:
                    logger.warning(f"{self.directory_name!r}: {x}")
            else:
                if self.observer:
                    logger.debug(f"Ending monitoring of {self.directory_name!r}")
                    try:
                        self.observer.stop()
                    except Exception as x:
                        # logger.debug(f"{self.directory_name}: stop: {x}")
                        pass
                    self.observer = None

    observer = None

    @thread_property
    def monitoring_win32(self):
        """Watch trace directory for new files (Windows only)"""
        while not self.monitoring_win32_cancelled:
            from os.path import exists
            from time import sleep
            if not exists(self.directory_name):
                sleep(1)
            else:
                # watchdog: "Failed to import read_directory_changes. Fall back to polling"
                # http://code.activestate.com/recipes/156178-watching-a-directory-under-win32/
                import win32file
                import win32event
                import win32con
                import win32api
                flags = 0 \
                    | win32con.FILE_NOTIFY_CHANGE_FILE_NAME \
                    | win32con.FILE_NOTIFY_CHANGE_DIR_NAME \
                    | win32con.FILE_NOTIFY_CHANGE_SIZE \
                    # | win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES\
                # | win32con.FILE_NOTIFY_CHANGE_SECURITY
                # | win32con.FILE_NOTIFY_CHANGE_LAST_WRITE\
                change_handle = win32file.FindFirstChangeNotification(self.directory_name, 0, flags)
                try:
                    while not self.monitoring_win32_cancelled:
                        result = win32event.WaitForSingleObject(change_handle, 500)
                        if result == win32con.WAIT_OBJECT_0:
                            self.call(event=self.event)
                            try:
                                win32file.FindNextChangeNotification(change_handle)
                            except win32api.error as x:
                                logger.warning(f"{self.directory_name}: {x}")

                finally:
                    win32file.FindCloseChangeNotification(change_handle)

    monitoring_win32_cancelled = False

    @property
    def event(self):
        from event import event as event
        event = event(
            time=self.time,
            value=self.files,
            reference=self.reference,
        )
        return event

    @property
    def reference(self):
        from reference import reference
        return reference(directory(self.directory_name), "files")

    @property
    def time(self):
        from os.path import getmtime
        try:
            t = getmtime(self.directory_name)
        except OSError:
            from time import time
            t = time()
        return t

    @property
    def files(self):
        from os import listdir
        try:
            files = listdir(self.directory_name)
        except OSError:
            files = []
        return files

    @files.setter
    def files(self, files):
        if len(files) > 0:
            create_directory(self.directory_name)
        for existing_file in self.files:
            if existing_file not in files:
                remove(self.directory_name + "/" + existing_file)
        existing_files = self.files
        for file in files:
            if file not in existing_files:
                create_file(self.directory_name + "/" + file)


def create_directory(directory):
    from os.path import isdir
    if not isdir(directory):
        from os import makedirs
        try:
            makedirs(directory)
        except OSError as x:
            logger.warning(f"Cannot create directory {directory!r}: {x}")


def remove(pathname):
    from os.path import isfile
    if isfile(pathname):
        from os import remove
        try:
            remove(pathname)
        except OSError as x:
            logger.warning(f"remove: {pathname!r}: {x}")
    from os.path import isdir
    if isdir(pathname):
        from shutil import rmtree
        try:
            rmtree(pathname)
        except OSError as x:
            logger.warning(f"rmtree: {pathname!r}: {x}")


def create_file(pathname):
    from os.path import exists
    if not exists(pathname):
        try:
            open(pathname, "a").write("")
        except OSError as x:
            logger.warning(f"Cannot create {pathname!r}: {x}")


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from tempfile import gettempdir as _gettempdir
    from handler import handler as _handler
    from reference import reference as _reference

    # self = directory(_gettempdir() + "/test")
    self = directory("/net/mx340hs/data/tmp")
    # self = directory('//femto/C/All Projects/APS/Experiments/2019.12/Test/Logfiles')
    filename = self.name + '/test.log'


    @_handler
    def report(event):
        logging.info(f"{event}")


    _reference(self, "files").monitors.add(report)

    print("self.files = %r" % self.files)
    print("self.files = ['test.txt']")
    print("self.files = []")

    # print('from file import file; file(filename).content = "test\\n"')
    # print('from file import file; file(filename).content = ""')
    # print('from os import remove; remove(filename)')
    print('from shutil import rmtree; remove(self.name)')
