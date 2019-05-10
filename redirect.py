"""
Redirect statdard output and standard error output
Author: Friedrich Schotte
Data created: 2017-11-14
Date last modified: 2019-03-16
"""
__version__ = "1.1.1" # Issue: self.output.write exception 

class redirector(object):
    """Saves a copy of standard output or standard error output to a file and
    Adds a timestamp if needed.
    Usage: sys.stderr = redirector(sys.stderr)"""
    lock = {}
    def __init__(self,output,filename):
        """output: sys.stdout or sys.stderr
        filename: absolute pathname
        """
        from thread import allocate_lock
        self.filename = filename
        self.output = output
        self.name = filename # for compatibility with "stream" objects
        if not filename in self.lock: self.lock[filename] = allocate_lock()

    def write(self,message):
        if not hasattr(self.output,"output"):
            try: self.output.write(message)
            except: pass # printing an error message could cause a loop
        if message not in ["","\n"]:
            log_message = message
            if not log_message.endswith("\n"): log_message += "\n"
            if not has_timestamp(message):
                if self.output_name: log_message = self.output_name+" "+log_message
                log_message = timestamp()+" "+log_message
            try:
                with self.lock[self.filename]:
                    try: file(self.filename,"ab").write(log_message)
                    except: pass # printing an error message could cause a loop
            except:
                try: file(self.filename,"ab").write(log_message)
                except: pass # printing an error message could cause a loop
                

    @property
    def output_name(self):
        """'<stdout>' or '<stderr>'"""
        output_name = getattr(self.output,"name","")
        output_name = output_name.strip("<>")
        output_name = output_name.upper()
        return output_name

    def __repr__(self):
        return "redirector(%r,%r)" % (self.output,self.filename)

def redirect1(logfile_basename):
    """Redirect stdout and stderr to a file
    logfile_basename: filename without directort, extension ".log" will be added"""
    import sys
    sys.stdout = file(stdout_filename(logfile_basename),"ab")
    sys.stderr = file(stderr_filename(logfile_basename),"ab")

def redirect(logfile_basename,level="DEBUG",
    format="%(asctime)s %(levelname)s: %(message)s"):
    """Redirect stdout and stderr to a file
    logfile_basename: filename without directort, extension ".log" will be added"""
    import sys
    sys.stdout = redirector(sys.stdout,log_filename(logfile_basename))
    sys.stderr = redirector(sys.stderr,log_filename(logfile_basename))
    from logging_filename import log_to_file,suppress_logging_to_stderr
    suppress_logging_to_stderr()
    log_to_file(
        filename=sys.stderr,
        level=level,
        format=format,
    )

def log_filename(logfile_basename):
    from tempfile import gettempdir
    filename = gettempdir()+"/"+logfile_basename+".log"
    return filename

def stdout_filename(logfile_basename):
    from tempfile import gettempdir
    filename = gettempdir()+"/"+logfile_basename+"_stdout.log"
    return filename

def stderr_filename(logfile_basename):
    from tempfile import gettempdir
    filename = gettempdir()+"/"+logfile_basename+"_stderr.log"
    return filename

def has_timestamp(message):
    """"""
    return message.startswith("20")
    
def timestamp():
    """Current date and time as string in ISO format"""
    from datetime import datetime
    return str(datetime.now())


if __name__ == "__main__":
    from logging import debug,info,warn,error
    import logging
    import sys
    from logging_filename import * # for testing
    print('logging.basicConfig(level=logging.DEBUG)')
    print('logging.getLoggerClass().root.level = logging.DEBUG')
    print('redirect("test")')
    print('print("test")')
    print('debug("debug")')
    print('info("info")')
    print('warn("warn")')
    print('id(sys.stderr)')
