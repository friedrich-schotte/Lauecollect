"""Which file is the logging module currently writing to?
Author: Friedrich Schotte
Date created: 2016-11-12
Date last modified: 2019-01-27
"""
__version__ = "1.0.1" # log_to_file: pass on format, adjust root level

def logging_filenames():
    """Which file is the logging module currently writing to?"""
    import logging
    filenames = []
    handlers = logging.getLogger('').handlers
    for handler in handlers:
        if hasattr(handler.stream,"name"): filename = handler.stream.name
        else: filename = repr(handler.stream)
        filenames += [filename]
    return filenames

def log_to_file(
    filename=None,
    level="DEBUG",
    format="%(asctime)s %(levelname)s: %(message)s",
    ):
    """Save debug, info, warn, and error messages to a file"""
    level = level_number(level)
    stream = stream_object(filename)
    import logging
    console = logging.StreamHandler(stream)
    console.setLevel(level)
    # Set a format which is simpler for console use.
    console.setFormatter(logging.Formatter(format))
    # Add the handler to the root logger.
    logging.getLogger('').addHandler(console)
    # Make sure messages are not intercepted a a higher level
    root_level = logging.getLogger('').level
    if root_level > level: logging.getLoggerClass().root.level = level

def suppress_logging_to_stderr():
    import logging,sys
    filenames = []
    logger = logging.getLogger('')
    handlers = logger.handlers
    for handler in handlers:
        if getattr(handler.stream,"name","") == "<stderr>":
            logger.removeHandler(handler)

def stream_object(file):
    """Makre sure file is a writable stream object,
    meaning it has a 'write' method"""
    if file is None: stream = None
    elif file in ["<stderr>","stderr"]:
        import sys; stream = sys.stderr
    elif type(file) == str: stream = open(file,"a")
    elif hasattr(file,"write"): stream = file
    else: stream = None
    return stream

def level_number(level):
    """Level: string or number e.g. 'DEBUG'=10,'INFO'=20,'WARN'=30,'ERROR'=40"""
    if type(level) is str:
        import logging
        try: level_number = getattr(logging,level)
        except: level_number = logging.DEBUG
    else: level_number = level
    return level_number


if __name__ == "__main__":
    import logging
    from logging import debug,info,warn,error

    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    ##    filename="/tmp/test.log")
    ##log_to_file("/tmp/test.log")
    print(logging_filenames())

    # The first time a message is logging the logger logs to the terminal.
    # After that the messages cannot be redirected to a file anymore.
    logging.basicConfig(level=logging.DEBUG)
    print(logging_filenames())
    ##log_to_file()
    debug("debug")
    info("info")
    warn("warn")
    error("error")
    print(logging_filenames())

    # The filename argument is ignored if one of debug,warn,info,error was
    # already called.
    ##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s",
    ##    filename="/tmp/test.log")
    print(logging_filenames())

    log_to_file("/tmp/test.log","DEBUG")
    print(logging_filenames())
    debug("debug")
    info("info")
    warn("warn")
    error("error")

