#!/bin/env python
"""
Start servers automatically

Author: Friedrich Schotte,
Date created: 2017-10-23
Date last modified: 2019-03-21
"""
__version__ = "1.0.5" # proc.cmdline exception (psutil.NoSuchProcess, was: psutil.ProcessZombie)

from logging import debug,info,warn,error
import traceback

class Server(object):
    from persistent_property import persistent_property
    label = persistent_property("servers.{name}.label","")
    command = persistent_property("servers.{name}.command","")
    logfile_basename = persistent_property("servers.{name}.logfile_basename","servers")
    enabled = persistent_property("servers.{name}.enabled",True)
    value_code = persistent_property("servers.{name}.value_code","True")
    format_code = persistent_property("servers.{name}.format_code","str(value)")
    test_code = persistent_property("servers.{name}.test_code","value")
    
    def __init__(self,name,command=None):
        self.name = name
        if command is not None: self.command = command
        
    def get_running(self):
        return process_running(self.command_line)
    def set_running(self,value):
        if value != self.running:
            if value: self.start()
            else: self.stop()
    running = property(get_running,set_running)

    def start(self):
        """Execute the command in a subprocess.
        The standard ouput and standard error output are redirected to a
        logfile."""
        from subprocess import Popen
        Popen(self.command_line,stdin=None,stdout=None,stderr=None,
            close_fds=True)

    def stop(self):
        terminate_process(self.command_line)

    @property
    def command_line(self):
        from sys import executable as python
        command = "from redirect import *; redirect(%r); %s" % \
            (self.logfile_basename,self.command)
        command_line = [python,"-c",command]
        return command_line

    def get_log(self):
        try: value = file(self.log_filename,"rb").read()
        except IOError: value = ""
        return value
    def set_log(self,value):
        file(self.log_filename,"wb").write(value)
    log = property(get_log,set_log)

    def get_stdout(self):
        try: value = file(self.stdout_filename,"rb").read()
        except IOError: value = ""
        return value
    def set_stdout(self,value):
        file(self.stdout_filename,"wb").write(value)
    stdout = property(get_stdout,set_stdout)

    def get_stderr(self):
        try: value = file(self.stderr_filename,"rb").read()
        except IOError: value = ""
        return value
    def set_stderr(self,value):
        file(self.stderr_filename,"wb").write(value)
    stderr = property(get_stderr,set_stderr)

    @property
    def log_filename(self):
        from redirect import log_filename
        return log_filename(self.logfile_basename)

    @property
    def stdout_filename(self):
        from redirect import stdout_filename
        return stdout_filename(self.logfile_basename)

    @property
    def stderr_filename(self):
        from redirect import stderr_filename
        return stderr_filename(self.logfile_basename)

    @property
    def test_code_OK(self):
        """Is the code for this test executable?"""
        exec("from instrumentation import *")
        from numpy import nan,isnan
        value = self.value
        try: eval(self.test_code); OK = True
        except Exception,msg:
            warn("value: %s: %s\n%s" % (self.test_code,msg,traceback.format_exc()))
            OK = False
        return OK

    @property
    def value(self):
        """Current value of diagnostic"""
        exec("from instrumentation import *")
        from numpy import nan,isnan
        try: value = eval(self.value_code)
        except Exception,msg:
            warn("value: %s: %s\n%s" % (self.value_code,msg,traceback.format_exc()))
            value = ""
        return value

    @property
    def formatted_value(self):
        """Current value of diagnostic as string"""
        value = self.value
        from numpy import nan,isnan
        try: text = eval(self.format_code)
        except Exception,msg:
            warn("value: %s with value=%r: %s\n%s" % (self.format_code,value,msg,
                traceback.format_exc()))
            text = str(value)
        return text

    @property
    def OK(self):
        """Did this test pass OK?"""
        exec("from instrumentation import *")
        from numpy import nan,isnan
        value = self.value
        try: passed = eval(self.test_code)
        except: passed = True
        return passed


class Servers(object):
    """Collection of Server objects"""
    name = "servers"
    from persistent_property import persistent_property
    N = persistent_property("N",0)

    servers = {}

    def __getitem__(self,i):
        if not i in self.servers: self.servers[i] = Server("%d" % (i+1))
        return self.servers[i]

    def __len__(self): return self.N

    def __iter__(self):
        for i in range(0,len(self)):
            if i < len(self): yield self[i]

    def get_running(self):
        return all([server.running for server in self if server.enabled])
    def set_running(self,value):
        for server in self:
            if server.enabled:
                if value != server.running: server.running = value
    running = property(get_running,set_running)

    def get_Nrunning(self):
        return sum([server.running for server in self if server.enabled])
    Nrunning = property(get_Nrunning)

servers = Servers()

def process_running(command_line):
    """Is there at least one process running matching command_line somewhere in
    the pathname or comand line arguments?
    command_line: string or list of strings
    """
    import psutil
    if not isinstance(command_line,basestring):
        command_line = " ".join(command_line)
    running = False
    for proc in psutil.process_iter():
        try: arg_list = proc.cmdline()
        except: arg_list = []
        if command_line in " ".join(arg_list): running = True; break
    return running

def terminate_process(command_line):
    """Terminate all running processes, matching command_line somewhere in
    the pathname or comand line arguments
    command_line: string or list of strings
    """
    import psutil
    if not isinstance(command_line,basestring):
        command_line = " ".join(command_line)
    for proc in psutil.process_iter():
        try: arg_list = proc.cmdline()
        except psutil.AccessDenied: arg_list = []
        except psutil.ZombieProcess: arg_list = []
        if command_line in " ".join(arg_list): proc.kill()

if __name__ == "__main__":
    """"for testing"""
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s %(levelname)s: %(message)s")
    from time import time
    self = server = servers[0]
    print('servers.N = %r' % servers.N)
    for i in range(0,len(servers)):
        print('servers[%d].label = %r' % (i,servers[i].label))
        print('servers[%d].command = %r' % (i,servers[i].command))
    ##print('')
    ##for i in range(0,len(servers)):
    ##    print('servers[%d].running = %r' % (i,servers[i].running))
    ##print('servers.Nrunning = %r' % servers.Nrunning)
    print('print servers[5].log')

