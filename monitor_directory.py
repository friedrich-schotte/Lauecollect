"""
Author: Friedrich Schotte
Date created: 2018-01-25
Date last modified: 2018-01-25
"""
__version__ = "0.0"

from logging import debug,info,warn,error

class monitor(object):
    """For Linux and MacOS
    Is compatible with Windows XP, but has poor performance:
    "Failed to import read_directory_changes. Fall back to polling"
    """
    def __init__(self,directory,handler,*args,**kwargs):
        """directory: pathname
        handler: routine to be called
        """
        self.directory = directory
        self.handler = handler
        self.args = args
        self.kwargs = kwargs
        ##self.monitoring = True

    def __repr__(self):
        return "monitor(%r,%r,%r,%r)" % \
            (self.directory,self.handler,self.args,self.kwargs)

    def __eq__(self,other):
        return (self.directory == other.directory and
                self.handler   == other.handler and
                self.args      == other.args and
                self.kwargs    == other.kwargs)

    def get_monitoring(self): return getattr(self,self.monitoring_property)
    def set_monitoring(self,value): setattr(self,self.monitoring_property,value)
    monitoring = property(get_monitoring,set_monitoring)
        
    @property
    def monitoring_property(self):
        from sys import platform
        return "monitoring_win32" if platform == "win32" else "monitoring_posix"
        
    def get_monitoring_posix(self):
        """Watching trace directory for new files?"""
        return hasattr(self,"observer") and self.observer.is_alive()
    def set_monitoring_posix(self,value):
        if bool(value) != self.monitoring_posix:
            if bool(value) == True:
                # https://stackoverflow.com/questions/18599339/python-watchdog-monitoring-file-for-changes
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
                class MyHandler(FileSystemEventHandler):
                    def on_modified(handler,event):
                        self.handler(*self.args,**self.kwargs)
                event_handler = MyHandler()
                self.observer = Observer()
                self.observer.schedule(event_handler,path=self.directory,recursive=False)
                self.observer.start()
            if bool(value) == False:
                if hasattr(self,"observer"): self.observer.stop()
    monitoring_posix = property(get_monitoring_posix,set_monitoring_posix)                     

    from thread_property import thread_property

    @thread_property
    def monitoring_win32(self):
        """Watch trace directory for new files
        (Windows only)"""
        while not self.monitoring_win32_cancelled:
            from os.path import exists
            from time import sleep
            if not exists(self.directory): sleep(1)
            else:
                # watchdog: "Failed to import read_directory_changes. Fall back to polling"
                # http://code.activestate.com/recipes/156178-watching-a-directory-under-win32/
                import win32file,win32event,win32con
                change_handle = win32file.FindFirstChangeNotification(directory,0,
                    win32con.FILE_NOTIFY_CHANGE_FILE_NAME)
                try:
                    while self.monitoring_win32_cancelled:
                        result = win32event.WaitForSingleObject(change_handle, 500)
                        if result == win32con.WAIT_OBJECT_0:
                            self.handler(*self.args,**self.kwargs)
                            win32file.FindNextChangeNotification(change_handle)
                finally: win32file.FindCloseChangeNotification(change_handle)

def directory_monitor(directory,handler,*args,**kwargs):
    new_monitor = monitor(directory,handler,*args,**kwargs)
    if not new_monitor in monitors:
        monitors.append(new_monitor)
        new_monitor.monitoring = True

def directory_monitor_clear(directory,handler,*args,**kwargs):
    monitor_to_remove = monitor(directory,handler,*args,**kwargs)
    for old_monitor in monitors:
        if old_monitor == monitor_to_remove: old_monitor.monitoring = False
    while monitor_to_remove in monitors: monitors.remove(monitor_to_remove)

def directory_monitors(directory):
    return [monitor.handler for monitor in monitors if monitor.directory == directory]

monitors = []


if __name__ == "__main__":
    from pdb import pm
    directory = "/net/mx340hs/data/tmp"
    ##directory = "/tmp"
    def handle_change(directory): warn("%r changed" % directory)
    print('monitors.append(monitor(directory,handle_change,directory))')
    print('directory_monitor(directory,handle_change,directory)')
    print('directory_monitor_clear(directory,handle_change,directory)')
    print('directory_monitors(directory)')
