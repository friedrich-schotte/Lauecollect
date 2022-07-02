"""
Redirect standard output and standard error output
Author: Friedrich Schotte
Data created: 2017-11-14
Date last modified: 2021-09-21
Revision comment: Changed: default format
"""
__version__ = "1.5.4"

from cached_function import cached_function


def redirect(
        logfile_basename,
        level=None,
        format="%(asctime)s %(levelname)s: %(module)s.%(funcName)s: %(message)s",
):
    """Redirect stdout and stderr to a file
    logfile_basename: filename without directory, extension ".log" will be added"""
    if level is not None:
        set_log_level(logfile_basename, level)
    import sys
    sys.stdout = redirector(sys.stdout, logfile_basename)
    sys.stderr = redirector(sys.stderr, logfile_basename)
    suppress_logging_to_stderr()
    level = log_level(logfile_basename)
    log_to_file(
        sys.stderr,
        level=level,
        format=format,
    )


class redirector(object):
    """Saves a copy of standard output or standard error output to a file and
    Adds a timestamp if needed.
    Usage: sys.stderr = redirector(sys.stderr)"""
    lock = {}

    def __init__(self, output, basename):
        """output: sys.stdout or sys.stderr
        filename: absolute pathname
        """
        self.basename = basename
        self.output = output

    @property
    def filename(self):
        return log_filename(self.basename)

    name = filename  # for compatibility with "stream" objects

    def write(self, message):
        if not hasattr(self.output, "output"):
            if hasattr(self.output, "write"):
                try:
                    self.output.write(message)
                except OSError:
                    pass  # printing an error message could cause a loop
        if message not in ["", "\n"]:
            log_message = message
            if not log_message.endswith("\n"):
                log_message += "\n"
            if not has_timestamp(message):
                if self.output_name:
                    log_message = self.output_name + " " + log_message
                log_message = timestamp() + " " + log_message

            if self.filename not in self.lock:
                from threading import Lock
                self.lock[self.filename] = Lock()

            try:
                with self.lock[self.filename]:
                    try:
                        open(self.filename, "a").write(log_message)
                    except OSError:
                        pass  # printing an error message could cause a loop
            except Exception:
                try:
                    open(self.filename, "a").write(log_message)
                except OSError:
                    pass  # printing an error message could cause a loop

    def flush(self):
        pass

    @property
    def output_name(self):
        """'<stdout>' or '<stderr>'"""
        output_name = getattr(self.output, "name", "")
        output_name = output_name.strip("<>")
        output_name = output_name.upper()
        return output_name

    def __repr__(self):
        return "redirector(%r,%r)" % (self.output, self.basename)


def log_to_file(
        stream,
        level="DEBUG",
        format="%(asctime)s %(levelname)s: %(message)s",
):
    """Save debug, info, warn, and error messages to a file"""
    level = level_number(level)
    import logging
    console = logging.StreamHandler(stream)
    console.setLevel(level)
    # Set a format which is simpler for console use.
    console.setFormatter(logging.Formatter(format))
    # Add the handler to the root logger.
    logging.root.addHandler(console)
    # Make sure messages are not intercepted a a higher level
    root_level = logging.root.level
    if root_level > level:
        logging.root.level = level


def suppress_logging_to_stderr():
    import logging
    logger = logging.root
    handlers = logger.handlers
    for handler in handlers:
        if getattr(handler.stream, "name", "") == "<stderr>":
            logger.removeHandler(handler)


@cached_function()
def logger(name):
    return Logger(name)


class Logger(object):
    from monitored_property import monitored_property

    domain_name = ""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        name = type(self).__name__.lower()
        return "%s(%r)" % (name, self.name)

    def get_name(self):
        if self.domain_name:
            name = "%s.%s" % (self.domain_name, self.logfile_basename)
        else:
            name = self.logfile_basename
        return name

    def set_name(self, name):
        if "." in name:
            self.domain_name = name.split(".", 1)[0]
            self.logfile_basename = name.split(".", 1)[1]
        else:
            self.logfile_basename = name

    name = property(get_name, set_name)

    from db_property import db_property
    directory_string = db_property("directory", "/net/mx340hs/data/anfinrud_1911/Logfiles")

    def calculate_directory(self, directory_string):
        directory = directory_string
        from normpath import normpath
        directory = normpath(directory)
        from os.path import exists
        if not exists(directory):
            from os import makedirs
            try:
                makedirs(directory)
            except OSError:
                pass
        if not exists(directory):
            from tempfile import gettempdir
            directory = gettempdir()
        return directory

    def set_directory(self, value):
        self.directory_string = value

    def inputs_directory(self):
        from reference import reference
        return [reference(self, "directory_string")]

    directory = monitored_property(
        calculate=calculate_directory,
        inputs=inputs_directory,
        fset=set_directory,
    )

    @property
    def db_name(self):
        if self.domain_name:
            name = "%s/logging" % self.domain_name
        else:
            name = "logging"
        return name

    def calculate_filename(self, directory):
        filename = directory + "/" + self.logfile_basename + ".log"
        return filename

    def inputs_filename(self):
        from reference import reference
        return [reference(self, "directory")]

    filename = monitored_property(
        calculate=calculate_filename,
        inputs=inputs_filename,
    )


def log_filename(logfile_basename):
    filename = logger(logfile_basename).filename
    return filename


def logfile_directory(domain_name=""):
    directory = logger(domain_name + ".test").directory
    return directory


def set_logfile_directory(directory, domain_name=""):
    logger(domain_name + ".test").directory = directory
    # from DB import dbset
    # dbset("logging.directory",directory)


def log_level(logfile_basename):
    """'DEBUG,'INFO','WARNING', or 'ERROR'
    """
    from DB import db
    return db("logging.%s.log_level" % logfile_basename, 'DEBUG')


def set_log_level(logfile_basename, level):
    """level:'DEBUG,'INFO','WARNING',or 'ERROR'
    """
    from DB import dbset
    dbset("logging.%s.log_level" % logfile_basename, level)


def has_timestamp(message):
    """"""
    return message.startswith("20")


def timestamp():
    """Current date and time as string in ISO format"""
    from datetime import datetime
    return str(datetime.now())


def level_number(level):
    """Level: string or number e.g. 'DEBUG'=10,'INFO'=20,'WARN'=30,'ERROR'=40"""
    if type(level) is str:
        import logging
        level_number = getattr(logging, level, logging.DEBUG)
    else:
        level_number = level
    return level_number


if __name__ == "__main__":
    from logging import debug, info, warning, error  # for testing
    import logging
    import sys
    # from logging_filename import *  # for testing

    name = "'BioCARS.WideFieldCamera_simulator'"
    # name = "LaserLab.Channel_Archiver_Viewer"

    self = logger(name)

    print('logging.basicConfig(level=logging.DEBUG)')
    print('logging.root.level = logging.DEBUG')
    print('logger(name).directory')
    print('logger(name).filename')
    print('logfile_directory()')
    print('set_logfile_directory("//femto-data2/C/Data/2020.10/Test/Logfiles")')
    print('log_filename(name)')
    print('redirect(name)')
    print('print("test")')
    print('debug("debug")')
    print('info("info")')
    print('warning("warning")')
    print('id(sys.stderr)')
    print('set_log_level(name,"INFO")')
    print('log_level(name)')
