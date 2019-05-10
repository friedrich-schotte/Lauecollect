"""
This is a server script that allows the remoly control and monitor a
LeCroy oscilloscope. This script needs to run one the same PC as the
oscilloscope.
This script serves the oscillope up on the network using on TCP port
1860. Multiple concurrent connections are allowed. A client application can
either send send a single command one a TCP connection and then close it,
or kept the connection alive indefinitly and send all commands over than same
connection.
This script works for all of LeCroy's PC-based X-Stream series oscilloscopes,
like WaveSurfer, WaveRunner and WaveMaster series.
Remote control is implemented using the DCOM (Distributes Common Object Model)
interface of the LeCroyXStreamDSO application.
The oscilloscope software has got two remote control interfaces. The classic
GPIB command set is served on TCP port 1861, ecapsulated in packets with binary
VICP (Virtual Instrument Control Protocol) headers. This command set is
described in LeCroy's "WaveRunner 6000A Series Remote Control Manual".
This interterface has the drawback that one one concurret client connection is
supported, there is a two second delay for disconnecting and reconnecting and
some functions of the oscilloscope are not supported, like setting measurement
gates.
The other interface is based on Microsoft's DCOM remote procedure calls. The
command set is documented in LeCroy's "WaveMaster, WavePro Series Automation
Manual", file "Automation Manual.pdf" in "femto.niddk.nih.gov/APS/Laser Hutch/
Laser Oscilloscope".
A command that modifies a setting of the oscilloscope is, for instance,
"Measure.P1.GateStart.Value = 0.95". This sets the low limit of the gate
of measurement P1 to 0.95 divisions. This command generates not reply.
A query that generates a reply would be "Measure.P1.GateStart.Value".
This reads back the low limit of the gate of measurement P1.
Each command needs to be terminated by newline charater when sent to the
server. A carriage return character at the end is allowed, but not required.

A quick way to find a command is to launch the "XStream Browser" application
on the oscilloscope PC and brwoser the command set with the Explorer-like
interface.
Properties listed with type 'Double','Bool','String','Enum' are read by appending
'.Value' to their name and set by appending ' = val' or '.Value = val' to
their name. If 'val' is a string it must be enclosed in double quotes or single
quotes.
Properties list as 'Action' are called by appending ".ActNow()" to their
name, e.g. "ClearSweeps.ActNow()".
Properties listed as 'Method' are called by appending "()" with optional
arguments to their name, e.g. "Sleep(1000)".
Commands are not case-sensitive.

Installation:
Installed Python 2.7.15 (OCt 2018) from python.org in C:/Python27 (default).
Desktop > Computer > Properties > Advanced System Settings > Environment Variables
PATH=...;C:\Python27;C:\Python27\Scripts
C:\> pip install pywin32
C:\> pip install numpy
C:\> pip install wxPython
C:\> pip install psutil
C:\> pip install pyparsing
C:\> pip install pytz

Created a shortcut to \\id14b4\useridb\NIH\Software\lecroy_scope_server.py,
named "LeCroy Scope Server", in the Autostart program group for all users.
Shortcut Properties: Run: Minimized

Example:
Measure.P1.GateStart = 0.95 or Measure.P1.GateStart.Value = 0.95
sets the low limit of the gate of measurement P1 to 0.95 divisions.
Measure.P1.last.Result.Value
Reads the current value of measurement P1
Measure.P1.num.Result.Value
Reads the number of measurement that where averaged.

test:
echo Measure.P1.num.Result.Value | nc -w1 id14l-scope.cars.aps.anl.gov 2000 

Author: Friedrich Schotte,
Date created: 2008-03-28
Date last modified: 2019-05-06
"""
__version__ = "2.5.3" # software version 8.1 still uses trace filename without hypens

from logging import debug,info,warn,error
import traceback

class Lecroy_Scope(object):
    """LeCroy oscilloscope"""
    from cached_property import cached_property
    from persistent_property import persistent_property
    from thread_property_2 import thread_property

    # When the trace count reaches 99999, it goes to 100000, then wraps back
    # to 00000.
    trace_count_wrap_period = 100001
    wrap = trace_count_wrap_period
    
    from numpy import nan,inf
    def value_property(query_string,default_value=nan,timeout=inf):
        """A propery representing a value that can be read and set"""
        def get(self):
            value = self.query(query_string)
            dtype = type(default_value)
            if dtype != str:
                try: value = dtype(eval(value))
                except: value = default_value
            return value
        def set(self,value): self.send("%s = %r" % (query_string,value))
        value_property = property(get,set,doc=query_string)

        from cached_property import cached_property
        value_property = cached_property(value_property,timeout)
        return value_property

    def action_property(command):
        """A propery representing an action that can be executed"""
        def get(self): return 0
        def set(self,value): self.send(command)
        return property(get,set)

    def method_property(method):
        """A property representing an method"""
        def get(self): return False
        def set(self,value):
            if value: method(self)
        return property(get,set)

    trig_count_name = persistent_property("trig_count_name","xosct_trig_count")
    acq_count_name  = persistent_property("acq_count_name", "xosct_acq_count")

    @property
    def trig_count(self):
        """Timing system register object"""
        from timing_system import timing_system
        value = getattr(timing_system,self.trig_count_name)
        return value

    @property
    def acq_count(self):
        """Timing system register object"""
        from timing_system import timing_system
        value = getattr(timing_system,self.acq_count_name)
        return value

    # for trace files
    channel = 1
    trace_filenames = {}
    files_to_save = {}
    save_traces_running = False

    def __init__(self,name="lecroy_scope"):
        self.name = name

    auto_synchronize = persistent_property("auto_synchronize",False)

    @thread_property
    def auto_synchronize_running(self):
        from sleep import sleep
        while not self.auto_synchronize_running_cancelled:
            sleep(10)
            if self.auto_synchronize:
                if self.monitoring_timing:
                    if not self.trace_count_synchronized:
                        self.trace_count_synchronized = True

    def get_trace_count_synchronized(self):
        synchronized = (
            abs(self.trace_count_offset) <= 1 and 
            abs(self.timing_offset) < 0.18 and
            self.timing_jitter < 0.1
        )
        return synchronized
    def set_trace_count_synchronized(self,value):
        if value and not self.trace_count_synchronized:
            self.timing_reset = True
            self.trace_count_offset = 0
    trace_count_synchronized = property(get_trace_count_synchronized,
        set_trace_count_synchronized)

    def trace_count_synchronize(self):
        """Synchronize the timing system's trigger count with the trace
        file count"""
        self.trace_count_offset = 0
    
    def get_trace_count_offset(self):
        offset = self.trace_count - self.timing_system_trigger_count % self.wrap
        return offset
    def set_trace_count_offset(self,offset):
        """Synchronize the timing system's trigger count with the trace
        file count
        offset should be zero"""
        self.timing_system_trigger_count = self.trace_count - offset
    trace_count_offset = property(get_trace_count_offset,set_trace_count_offset)
        
    def get_trace_acquisition_running(self):
        return self.trace_acquisition_monitoring and self.save_traces_running    
    def set_trace_acquisition_running(self,value):
        self.trace_acquisition_monitoring = value
        self.save_traces_running = value
    trace_acquisition_running = \
        property(get_trace_acquisition_running,set_trace_acquisition_running)

    __trace_acquisition_monitoring__ = False

    def get_trace_acquisition_monitoring(self):
        return self.trace_acquisition_monitor in self.acq_count.monitors
    def set_trace_acquisition_monitoring(self,value):
        if bool(value) != self.trace_acquisition_monitoring:
            if bool(value) == True:
                self.acq_count.monitor(self.trace_acquisition_monitor)
            if bool(value) == False:
                self.acq_count.monitor_clear(self.trace_acquisition_monitor)
    trace_acquisition_monitoring = property(get_trace_acquisition_monitoring,
        set_trace_acquisition_monitoring)

    timing_system_was_acquiring = False

    def trace_acquisition_monitor(self):
        """For filenames of trace files to be saved"""
        # First, trig_count updates, immediately followed by acq_count.
        from os.path import basename 
        trig_count = self.timing_system_trigger_count
        acq_count  = self.timing_system_acq_count
        timing_system_acquiring = self.timing_system_acquiring
        # Make sure to get the last trace 
        if timing_system_acquiring or self.timing_system_was_acquiring:
            if acq_count in self.trace_filenames:
                filename = self.trace_filenames[acq_count]
                info("Acquiring %r: trig %r = %r" % (acq_count,trig_count,
                    basename(filename)))
                for i,channel in enumerate(self.enabled_channels):
                    self.files_to_save[trig_count,i] = self.extended_filename(filename,i)
            else: info("Acquiring %r: trig %r (no filename)" % (acq_count,trig_count))
        else: info("trig_count=%r" % (trig_count))

        self.timing_system_was_acquiring = timing_system_acquiring

    def extended_filename(self,filename,i):
        """'test.trc' -> i=0:'test.trc', i=1:'test2.trc',i=2:'test3.trc'"""
        if len(self.trace_sources) > 1:
            from os.path import splitext
            basename,ext = splitext(filename)
            filename = "%s_%s%s" % (basename,self.trace_sources[i],ext)
        return filename

    __save_traces_running__ = False
    from threading import Thread
    save_traces_task = Thread()

    def get_save_traces_running(self):
        return self.save_traces_task.isAlive()
    def set_save_traces_running(self,value):
        if value != self.save_traces_running:
            if value:
                from threading import Thread
                self.save_traces_task = Thread(target=self.save_traces_forever,
                    name="save_traces_forever")
                self.save_traces_task.daemon = True
                self.__save_traces_running__ = True
                self.save_traces_task.start()
            else: self.__save_traces_running__ = False
    save_traces_running = property(get_save_traces_running,set_save_traces_running)

    def save_traces_forever(self):
        from time import sleep
        while self.__save_traces_running__:
            try: self.save_traces_once()
            except Exception,msg: error("%s\n%s",msg,traceback.print_exc())
            sleep(0.1)

    def save_traces_once(self):
        from os.path import exists,basename
        from normpath import normpath
        for count,i in self.files_to_save.keys():
            source = self.trace_filename(i,count)
            if exists(source):
                destination = self.files_to_save[count,i]
                destination = normpath(destination)
                info("Saving %r as %r",basename(source),basename(destination))
                ##info("Saving %r as %r",basename(source),destination)
                copy(source,destination)
                del self.files_to_save[count,i]

    def get_timing_system_acquiring(self):
        from timing_system import timing_system
        value = timing_system.register_count("acquiring")
        return value
    def set_timing_system_acquiring(self,value):
        from timing_system import timing_system
        timing_system.set_register_count("acquiring")
    timing_system_acquiring = property(get_timing_system_acquiring,
        set_timing_system_acquiring)

    def get_timing_system_trigger_count(self):
        return self.trig_count.value
    def set_timing_system_trigger_count(self,value):
        self.trig_count.value = value
    timing_system_trigger_count = property(get_timing_system_trigger_count,
        set_timing_system_trigger_count)
    trigger_count = timing_system_trigger_count

    def get_timing_system_acq_count(self):
        return self.acq_count.count
    def set_timing_system_acq_count(self,value):
        self.acq_count.count = value
    timing_system_acq_count = property(get_timing_system_acq_count,
        set_timing_system_acq_count)

    def get_timing_system_trigger_enabled(self):
        from Ensemble_SAXS import Ensemble_SAXS
        return Ensemble_SAXS.xosct_on
    def set_timing_system_trigger_enabled(self,value):
        from Ensemble_SAXS import Ensemble_SAXS
        Ensemble_SAXS.xosct_on = value
    timing_system_trigger_enabled = property(
        get_timing_system_trigger_enabled,set_timing_system_trigger_enabled)

    def trace_filename(self,i,count):
        """Trace file name on oscilloscope's internal file system
        i: trace number, e.g. 0 = CH1, 1 = CH2
        count: trigger count (starting with 0)"""
        trace_source = self.trace_sources[i]
        format = "%s\\%s%s%05.0f.trc"
        if self.software_version >= "8.2":
            format = "%s\\%s--%s--%05.0f.trc"
        filename = format % (self.trace_directory,trace_source,self.trace_title,count)
        return filename

    def file_trace_count(self,filename):
        from os.path import basename,splitext
        name = basename(filename)
        name = splitext(name)[0]
        if name.startswith("C"): name = name[2:]
        name = name.replace(self.trace_title,"")
        name = name.replace("--","") # for software version 8
        try: count = int(name)
        except Exception,msg:
            warn("%s: %r: %s" % (filename,name,msg))
            count = -1
        return count

    @property
    def software_version(self):
        ID_string = self.ID_string
        software_version = ID_string.split(",")[-1]
        return software_version

    def get_trace_directory_size(self):
        """Number of saved trace files"""
        if not hasattr(self,"__trace_directory_size__"):
            self.__trace_directory_size__ = number_of_files(self.trace_directory)
        return self.__trace_directory_size__
    def set_trace_directory_size(self,value):
        if value == 0: self.emptying_trace_directory = True
    trace_directory_size = property(get_trace_directory_size,set_trace_directory_size)

    trace_count = 0
    
    def value(self,query_string,default_value=nan):
        """Performs a query and returns the result as a specific data type,
        e.g. float, matching the given default value"""
        value = self.query(query_string)
        dtype = type(default_value)
        if dtype != str:
            try: value = dtype(eval(value))
            except: value = default_value
        return value

    def query(self,query_string):
        """Execute a command that generates a reply"""
        if not query_string.startswith("LeCroy.XStreamDSO."):
            query_string = "LeCroy.XStreamDSO."+query_string
        debug("Evaluating query: '%.800s'" % query_string)
        try:
            LeCroy = self.COM_object
            reply = eval(query_string)
        except Exception,x:
            if self.report(query_string): error("%r: %s" % (query_string,x))
            reply = ""
        if reply is not None:
            try: reply = str(reply)
            except: reply = repr(reply)                 
        else: reply = ""
        if self.report(query_string): info("%s? %.800s" % (query_string,reply))
        return reply

    def send(self,command):
        """Excute a command that does not generate a reply"""
        if not command.startswith("LeCroy.XStreamDSO."):
            command = "LeCroy.XStreamDSO."+command
        LeCroy = self.COM_object
        info("Executing command: %.800s" % command) 
        try: exec(command)
        except Exception,x: error("%r: %s" % (command,x))

    report_filter = [
        "last.Result.Value",
        "SaveRecall.Waveform.AutoSave",
        ".View",
        "SaveRecall.Setup.PanelFilename",
        "SaveRecall.Waveform.SaveSource",
    ]

    def report(self,query_string):
        """Generate a diagnostics message for this command?"""
        self.report_count[query_string] = self.report_count.get(query_string,0)+1
        report = True
        matches = False
        for string in self.report_filter:
            if string in query_string: matches = True
        if matches and self.report_count[query_string] > 3: report = False
        return report
    
    report_count = {}

    @property
    def COM_object(self):
        """'LeCroy.XStreamDSO' COM object"""
        import pythoncom,win32com.client # need to install pywin32
        pythoncom.CoInitialize() # needed only when run in a thread
        class LeCroy: XStreamDSO = win32com.client.Dispatch("LeCroy.XStreamDSO")
        return LeCroy
    ##COM_object = cached_property(COM_object,inf)

    def get_setup(self):
        return self.setup_name
    def set_setup(self,name):
        self.setup_name = name
        if self.setup_name != "": self.setup_recall = True
    setup = property(get_setup,set_setup)

    @property
    def setup_choices(self):
        from os import listdir
        dirname = self.local_setup_dirname
        try: files = listdir(dirname)
        except Exception,msg: files = []; warn("%s: %s" % (dirname,msg))
        files = [file for file in files if not file.startswith(".")]
        files = [file for file in files if file.endswith(".lss")]
        names = [file.replace(".lss","") for file in files]
        return names
    setups = setup_choices
    
    def get_setup_name(self):
        from os.path import basename
        name = basename(self.setup_filename).replace(".lss","")
        return name
    def set_setup_name(self,name):
        self.setup_filename = self.local_setup_filename(name)
    setup_name = property(get_setup_name,set_setup_name)

    def get_setup_filename(self):
        filename = self.setup_dirname+"/"+self.setup_basename
        from normpath import normpath
        filename = normpath(filename)
        return filename
    def set_setup_filename(self,filename):
        from normpath import normpath
        filename = Windows_pathname(normpath(filename))
        from os.path import dirname,basename
        dir,file = dirname(filename),basename(filename)
        self.setup_dirname = dir
        self.setup_basename = file
    setup_filename = property(get_setup_filename,set_setup_filename)

    setup_dirname = value_property("SaveRecall.Setup.PanelDir","")
    setup_basename = value_property("SaveRecall.Setup.PanelFilename","",timeout=10)

    setup_save = action_property("SaveRecall.Setup.DoSavePanel.ActNow()")
    setup_recall = action_property("SaveRecall.Setup.DoRecallPanel.ActNow()")

    trace_directory = value_property("SaveRecall.Waveform.WaveformDir","")
    trace_title = value_property("SaveRecall.Waveform.TraceTitle","")
    trace_source = value_property("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveSource","",timeout=10)

    @property
    def trace_sources(self):
        sources = []
        source = self.trace_source
        if source == "AllDisplayed": sources = self.enabled_channels
        elif source != "": sources = [source]
        return sources

    channels = "C1","C2","C3","C4"

    for channel in channels:
        exec('%s_on = value_property("LeCroy.XStreamDSO.Acquisition.%s.View",False,timeout=10)'
             % (channel,channel))

    @property
    def enabled_channels(self):
        names = []
        for name in self.channels:
            if getattr(self,name+"_on",False): names += [name]
        return names

    measurements = ["P%d" % (i+1) for i in range(0,4)] # may be up to 8

    for measurement in measurements:
        exec('%s_on = value_property("LeCroy.XStreamDSO.Measure.%s.View",False,timeout=inf)'
             % (measurement,measurement))

    @property
    def enabled_measurements(self):
        names = []
        for name in self.measurements:
            if getattr(self,name+"_on",False): names += [name]
        return names

    ID_string = value_property("InstrumentID","")    
    id = ID_string

    @property
    def local_setup_dirname(self):
        from module_dir import module_dir
        return module_dir(self)+"/lecroy_scope/"+self.name

    def local_setup_filename(self,name):
        if name != "": filename = self.local_setup_dirname+"/"+name+".lss"
        else: filename = ""
        return filename

    @thread_property
    def emptying_trace_directory(self):
        """Erase all temporary trace files"""
        directory = self.trace_directory
        filenames = listdir(directory)
        self.__trace_directory_size__ = len(filenames)
        from os import remove
        for i,filename in enumerate(filenames):
            if self.emptying_trace_directory_cancelled: break
            pathname = directory+"/"+filename
            try:
                remove(pathname)
            except Exception,msg: info("%s: %s" % (pathname,msg))
        filenames = listdir(directory)
        self.__trace_directory_size__ = len(filenames)

    auto_acquire = persistent_property("auto_acquire",False)

    @thread_property
    def auto_acquire_running(self):
        from sleep import sleep
        while not self.auto_acquire_running_cancelled:
            sleep(10)
            if self.auto_acquire:
                if not self.acquiring_waveforms: self.acquiring_waveforms = True

    def get_acquiring_waveforms(self):
        """Are trace currently being auto-saved?"""
        return self.waveform_autosave != "Off"
    def set_acquiring_waveforms(self,value):
        if value:
            mkdir(self.trace_directory)
            self.waveform_autosave = "Wrap"
        else: self.waveform_autosave = "Off"
    acquiring_waveforms = property(get_acquiring_waveforms,set_acquiring_waveforms)

    waveform_autosave = value_property("SaveRecall.Waveform.AutoSave","",timeout=10)

    def get_monitoring_timing(self):
        """Collecting information to check that trace acquisistion is
        synchronized?"""
        return self.monitoring_trace_count and self.monitoring_trig_count
    def set_monitoring_timing(self,value):
        if self.monitoring_trace_count_allowed: self.monitoring_trace_count = value
        self.monitoring_trig_count = value
    monitoring_timing = property(get_monitoring_timing,set_monitoring_timing)

    @method_property
    def timing_reset(self):
        self.trace_counts_reset = True
        self.trigger_counts_reset = True

    @thread_property
    def monitoring_trace_count(self):
        """Watch trace directory for new files"""
        while self.monitoring_trace_count_allowed and not self.monitoring_trace_count_cancelled:
            directory = self.trace_directory
            from os.path import exists
            from time import sleep
            if not exists(directory): sleep(1)
            else:
                # http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
                import os
                import win32file,win32con

                ACTIONS = {
                    1 : "Created",
                    2 : "Deleted",
                    3 : "Updated",
                    4 : "Renamed from something",
                    5 : "Renamed to something"
                }
                FILE_LIST_DIRECTORY = 0x0001
                hDir = win32file.CreateFile (
                    directory,
                    FILE_LIST_DIRECTORY,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_FLAG_BACKUP_SEMANTICS,
                    None,
                )
                while self.monitoring_trace_count_allowed and not self.monitoring_trace_count_cancelled:
                    # ReadDirectoryChangesW takes a previously-created handle to a
                    # directory, a buffer size for results, a flag to indicate whether
                    # to watch subtrees and a filter of what changes to notify.
                    #
                    # Need to up the buffer size to be sure of picking up all events when
                    # a large number of files were deleted at once.
                    results = win32file.ReadDirectoryChangesW (
                        hDir,
                        1024,
                        True,
                        win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                        win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                        win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                        win32con.FILE_NOTIFY_CHANGE_SIZE |
                        win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                        win32con.FILE_NOTIFY_CHANGE_SECURITY,
                        None,
                        None,
                    )
                    for action_code,filename in results:
                        action = ACTIONS.get(action_code,"Unknown")
                        if action != "Deleted": debug("%s: %s" % (filename,action))
                        if action == "Updated": self.trace_counts_handle(filename)
                        if action == "Created": self.__trace_directory_size__ += 1
                        if action == "Deleted": self.__trace_directory_size__ -= 1

    def trace_counts_handle(self,filename):
        from time import time
        t = time()
        n = self.file_trace_count(filename)
        if n>=0:
            debug("Trace count %d" % n)
            self.trace_counts_add(n,t)
            self.trace_count = n
    
    monitoring_trace_count_allowed = True
    
    trace_counts_dict = {}

    @method_property
    def trace_counts_reset(self):
        self.trace_counts_dict = {}

    def trace_counts_add(self,n,t):
        self.trace_counts_limit()
        self.trace_counts_dict[n] = t

    @property
    def trace_counts_history(self):
        """list of timestamps plus list of trace counts"""
        nt_pairs = self.trace_counts_dict.items()
        ts = [t for n,t in nt_pairs]
        ns = [n for n,t in nt_pairs]
        return ts,ns

    def trace_counts_limit(self):
        dt = 60
        from time import time
        t = time()
        # Work with a copy, in case the dictionary changes.
        trace_counts = dict(self.trace_counts_dict)
        for n in trace_counts.keys():
            if trace_counts[n] < t-dt: del trace_counts[n]
        self.trace_counts_dict = trace_counts

    def get_monitoring_trig_count(self):
        return self.trigger_counts_handle in self.trig_count.monitors
    def set_monitoring_trig_count(self,value):
        if bool(value) != self.monitoring_trig_count:
            if bool(value) == True:
                self.trig_count.monitor(self.trigger_counts_handle)
            if bool(value) == False:
                self.trig_count.monitor_clear(self.trigger_counts_handle)
    monitoring_trig_count = property(get_monitoring_trig_count,set_monitoring_trig_count)

    def trigger_counts_handle(self):
        from time import time
        t = time()
        n = self.trig_count.count
        self.trigger_counts_add(n,t)
        debug("Trigger count %r" % n)

    trigger_counts_dict = {}

    @method_property
    def trigger_counts_reset(self):
        self.trigger_counts_dict = {}

    def trigger_counts_add(self,n,t):
        self.trigger_counts_limit()
        self.trigger_counts_dict[n] = t

    @property
    def trigger_counts_history(self):
        """list of timestamps plus list of trigger counts"""
        nt_pairs = self.trigger_counts_dict.items()
        ts = [t for n,t in nt_pairs]
        ns = [n for n,t in nt_pairs]
        return ts,ns

    def trigger_counts_limit(self):
        dt = 60
        from time import time
        t = time()
        # Work with a copy, in case the dictionary changes.
        trigger_counts = dict(self.trigger_counts_dict)
        for n in trigger_counts.keys():
            if trigger_counts[n] < t-dt: del trigger_counts[n]
        self.trigger_counts_dict = trigger_counts

    @property
    def timing_differences(self):
        self.monitoring_timing = True
        self.auto_acquire_running = True
        self.auto_synchronize_running = True
        t,n = self.trace_counts_history; trace_nt = dict(zip(n,t))
        t,n = self.trigger_counts_history; trigger_nt = dict(zip(n,t))
        dt = []
        for trigger_count in trigger_nt:
            trace_count = trigger_count % self.wrap
            if trace_count in trace_nt:
                dt += [trace_nt[trace_count] - trigger_nt[trigger_count]]
        return dt

    @property
    def timing_jitter(self):
        # Supress "RuntimeWarning: Degrees of freedom <= 0 for slice."
        import numpy; numpy.warnings.filterwarnings('ignore')
        from numpy import std
        return std(self.timing_differences)

    @property
    def timing_offset(self):
        # Supress "RuntimeWarning: Mean of empty slice"
        import numpy; numpy.warnings.filterwarnings('ignore')
        from numpy import mean
        return mean(self.timing_differences)

    class measurement_object(object):
        """For automated measurements, including averageing and statistics"""

        def __init__(self,scope,n=1,type="value"):
            """n=1,2...6 is the waveform parameter number.
            The parameter is defined from the "Measure" menu, e.g. P1:delay(C3).
            The optional 'type' can by "value","min","max","stdev",or "count".
            """
            self.scope = scope; self.n = n; self.type = type
        
        def __repr__(self):
            return repr(self.scope)+".measurement("+str(self.n)+")."+self.type

        def get_value(self):
            n = self.n
            if self.type == "value":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.last.Result.Value" % n)
            if self.type == "average": return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":     return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value"  % n)
            if self.type == "max":     return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value"  % n)
            if self.type == "stdev":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value"  % n)
            return nan
        value = property(get_value,doc="last sample (without averaging)")

        def get_average(self): 
            n = self.n
            if self.type == "value":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "average": return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":     return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value"  % n)
            if self.type == "max":     return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value"  % n)
            if self.type == "stdev":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":   return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value"  % n)
            return nan
        average = property(get_average,doc="accumulated average")

        def get_max(self): return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value" % self.n)
        max = property(get_max,doc="maximum value contributing to average")

        def get_min(self): return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value" % self.n)
        min = property(get_min,doc="minimum value contributing to average")

        def get_stdev(self): return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % self.n)
        stdev = property(get_stdev,doc="standard deviation of individuals sample")

        def get_count(self): return self.scope.value("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value" % self.n)
        count = property(get_count,doc="number of measurement averaged")
        
        def get_name(self): 
            return self.scope.query("LeCroy.XStreamDSO.Measure.P%d.Equation.Value" % self.n)+"."+self.type
        name = property(get_name,doc="string representation of the measurement")

        def get_unit(self):
            return self.scope.query("LeCroy.XStreamDSO.Measure.P%d.num.Result.VerticalUnits.Value")
        unit = property(get_unit,doc="unit symbol of measurement (if available)")

        def start(self): self.scope.start()
        def stop(self): self.scope.stop()

        def clear_sweeps(self): self.scope.clear_sweeps()
        reset_average = clear_sweeps
        reset_statistics = clear_sweeps

        def get_gate(self): return self.scope.gate(self.n)
        gate = property(get_gate,doc="start of measurement gate")

        def get_enabled(self): return self.scope.measurement_enabled
        def set_enabled(self,value): self.scope.measurement_enabled = value
        enabled = property(get_enabled,set_enabled)

    def measurement(self,n=1,type="value"): return lecroy_scope.measurement_object(self,n,type)

    @property
    def P1(self):
        from numpy import nan
        return self.measurement(1).value if self.P1_on else nan
    @property
    def P2(self):
        from numpy import nan
        return self.measurement(2).value if self.P2_on else nan
    @property
    def P3(self):
        from numpy import nan
        return self.measurement(3).value if self.P3_on else nan
    @property
    def P4(self):
        from numpy import nan
        return self.measurement(4).value if self.P4_on else nan

    def update_period(self,name):
        """How often is it recommended to refresh a certein property?"""
        from numpy import inf
        period = inf
        if name in self.enabled_measurements: period = self.min_update_period
        if name == "waveform_autosave": period = 10
        if name == "trace_sources": period = 10
        return period
    
    min_update_period = 0.024


lecroy_scope = Lecroy_Scope()
scope = lecroy_scope

# listen port number of this server script
port = 2000 

def run_server():
    lecroy_scope_IOC.running = True
    # make a threaded server, listen/handle clients forever 
    server = ThreadingTCPServer(("",port),ClientHandler)
    info("Server version %s started, listening on port %d" % (__version__,port))
    try: server.serve_forever()
    except KeyboardInterrupt: pass

# By default, the "ThreadingTCPServer" class binds to the sever port
# without the option SO_REUSEADDR. The consequence of this is that
# when the server terminates you have to let 60 seconds pass, for the
# socket to leave to "CLOSED_WAIT" state before it can be restarted,
# otherwise the next bind call would generate the error
# 'Address already in use'.
# Setting allow_reuse_address to True makes "ThreadingTCPServer" use to
# SO_REUSEADDR option when calling "bind".

import SocketServer

class ThreadingTCPServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True

class ClientHandler(SocketServer.BaseRequestHandler):
     def handle(self):
         """Called when a client connects. 'self.request' is the client socket""" 
         info("Accepted connection from "+self.client_address[0])
         input_queue = ""
         while 1:
             # Commands from a client are not necessarily received as one packet
             # but each command is terminated by a newline character.
             # If 'recv' returns an empty string it means client closed the
             # connection.
             while input_queue.find("\n") == -1:
                 try: received = self.request.recv(2*1024*1024)
                 except Exception,x:
                     error("%r %r" % (x,str(x)))
                     received = ""
                 if received == "": info("Client disconnected"); break
                 debug("received %8d+%8d = %8d bytes" % (len(input_queue),
                    len(received),len(input_queue)+len(received)))
                 input_queue += received
             if input_queue == "": break
             if input_queue.find("\n") != -1:
                 end = input_queue.index("\n")
                 query = input_queue[0:end]
                 input_queue = input_queue[end+1:]
             else: query = input_queue; input_queue = ""
             ##debug("Command length: %r bytes" % len(query))
             query = query.strip("\r ")
             LeCroy = scope.COM_object
             # Is this a query of a command? Try "eval" first, then "exec". 
             info("Evaluating query: %.800s" % repr(query))
             try: reply = eval(query)
             except Exception,x:
                 error_message = "eval: %r\n%s" % (x,traceback.format_exc())
                 info("Executing command: '%.800s'" % query)
                 try: exec(query)
                 except Exception,x:
                     error_message += "\nexec: %r\n%s" % (x,traceback.format_exc())
                     error(error_message)
                 info("Completed command: '%.800s'" % query)
                 reply = None
             if reply is not None:
                 try: reply = str(reply)
                 except: reply = repr(reply)                 
                 reply += "\n"
                 info("Sending reply: %s (%r bytes)" % (repr(reply),len(reply)))
                 self.request.sendall(reply)
             else: info("Command completed. No reply needed.")
         info("Closing connection to "+self.client_address[0])
         self.request.close()


class Lecroy_Scope_IOC(object):
    @property
    def name(self): return scope.name
    @property
    def prefix(self): return "NIH:"+self.name.upper()+"."

    from persistent_property import persistent_property
    scan_period = persistent_property("scan_period",2.0)

    property_names = [
        "P1",
        "P2",
        "P3",
        "P4",
        "trace_count",
        "trace_sources",
        "timing_system_trigger_count",
        "trace_count_offset",
        "trace_directory_size",
        "emptying_trace_directory",
        "acquiring_waveforms",
        "auto_acquire",
        "timing_offset",
        "timing_jitter",
        "timing_reset",
        "auto_synchronize",
        "trace_count_synchronized",
        "trace_acquisition_running",
        "setup",
        "setups",
        "setup_name",
        "setup_filename",
        "setup_filename",
        "setup_save",
        "setup_recall",
    ]
    
    from thread_property_2 import thread_property
    
    @thread_property
    def running(self):
        info("Starting IOC: Prefix: %s ..." % self.prefix)
        from CAServer import casget,casput,casdel
        from time import time
        from sleep import sleep

        self.monitors_setup()
        
        while not self.running_cancelled:
            t = time()
            for name in self.property_names:
                if time() - self.last_updated(name) > self.update_period(name):
                    PV_name = self.prefix+name.upper()
                    value = getattr(scope,name)
                    ##info("Update: %s=%r" % (PV_name,value))
                    casput(PV_name,value,update=False)
                    self.set_update_time(name)
            if not self.running_cancelled: sleep(t+self.min_update_period-time())
        casdel(self.prefix)

    last_updated_dict = {}
    def set_update_time(self,name):
        from time import time
        self.last_updated_dict[name] = time()
    def last_updated(self,name): return self.last_updated_dict.get(name,0)
    
    def update_period(self,name):
        period = scope.update_period(name)
        period = min(period,self.scan_period)
        return period

    @property
    def min_update_period(self): return scope.min_update_period

    def monitors_setup(self):
        """Monitor client-writable PVs."""
        from CAServer import casmonitor,casput
        for name in self.property_names:
            PV_name = self.prefix+name.upper()
            casmonitor(PV_name,callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from CAServer import casput
        for name in self.property_names:
            if PV_name == self.prefix+name.upper():
                setattr(scope,name,value)
                casput(PV_name,getattr(scope,name))

lecroy_scope_IOC = Lecroy_Scope_IOC()


def number_of_files(directory):
    number_of_files = len(listdir(directory))
    info("Number of files in %r: %r" % (directory,number_of_files))
    return number_of_files

def monitor_directory(directory):
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    class MyHandler(FileSystemEventHandler):
        def on_modified(self, event):
            info("%s: %d files" % (directory,number_of_files(directory)))
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler,path=directory,recursive=False)
    observer.start()

def listdir(directory):
    info("Reading directory %r..." % (directory,))
    from os import listdir
    try: files = listdir(directory)
    except Exception,msg:
        debug("%r: %s" % (directory,msg))
        files = []
    info("Reading directory %r done." % (directory,))
    return files

from os.path import exists

def getmtime(pathname):
    """The last modification time of a file in seconds since Jan 1, 2015"""
    from os.path import exists,getmtime
    if not exists(pathname): return 0.0
    return getmtime(pathname)

def mtimes(pathnames):
    """The last modification time of a list of files,
    in seconds since Jan 1, 2015"""
    return [getmtime(f) for f in pathnames]

def rename(source,destination):
    """Rename of move a file."""
    if destination == source: return
    from os import rename,remove
    from os.path import exists,dirname
    if exists(destination): remove(destination)
    directory = dirname(destination)
    if directory and not exists(directory): mkdir(directory)
    rename(source,destination)

def copy_files(source_files,destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'."""
    from thread import start_new_thread
    start_new_thread(__copy_files__,(source_files,destination_files))
    
def __copy_files__(source_files,destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'."""
    for s,d in zip(source_files,destination_files): copy(s,d)

def migrate_files(source_files,destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'.
    source_files: list of strings
    destination_files: list of strings"""
    from thread import start_new_thread
    start_new_thread(__migrate_files__,(source_files,destination_files))

def __migrate_files__(source_files,destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files' and remove the source.
    source_files: list of strings
    destination_files: list of strings"""
    from time import sleep
    from os.path import dirname

    directory = dirname(source_files[0]) if len(source_files) > 0 else ""
    global migrate_directory; migrate_directory = directory

    copied = [False]*len(source_files)
    while directory == migrate_directory and not all(copied): 
        for i in range(0,len(source_files)):
            if copied[i]: continue
            if not exists(source_files[i]):
                sleep(1); break # Copying caught up with collection.
            copy(source_files[i],destination_files[i])
            if exists(destination_files[i]): copied[i] = True
    # Make one last attempt after acquisition finished.
    for i in range(0,len(source_files)):
        if not copied[i]:
            copy(source_files[i],destination_files[i])
            if exists(destination_files[i]): copied[i] = True
    # Clean up.
    for i in range(0,len(source_files)):
        if copied[i]: remove(source_files[i])
    from os import rmdir
    rmdir(directory)

migrate_directory = ""

def repr(x,nchars=80):
    """limit string length using ellipses (...)"""
    s = __builtins__.repr(x)
    if len(s) > nchars: s = s[0:nchars-10-3]+"..."+s[-10:]
    return s

migration_in_progress = False
copied = []
count = 0

def copy(source,destination):
    """Create a copy of a file with the same timestamp"""
    if destination == source: return
    from os import remove
    from shutil import copy2
    from os.path import exists,dirname
    if not exists(source): return
    if exists(destination): remove(destination)
    directory = dirname(destination)
    if directory and not exists(directory): mkdir(directory)
    try: copy2(source,destination)
    except Exception,msg:
        error("Error copying %r to %r: %s" % (source,destination,msg))

def remove(pathname):
    """Delete a file."""
    from os.path import exists
    if not exists(pathname): return
    from os import remove
    remove(pathname)

def mkdir(directory):
    """Create a directory"""
    from os import makedirs
    from os.path import exists
    if not exists(directory):
        try:
            makedirs(directory)
            info("Created directory %r" % directory)
        except Exception,msg: error("Cannot create %r: %s" % (directory,msg))

def rmdir(pathname):
    """Remove a directory and its contents"""
    from os.path import exists
    if not exists(pathname): return
    from shutil import rmtree
    try: rmtree(pathname)
    except Exception,msg: debug("%s: %s" % (pathname,msg))

def symlink(filename,linkname):
    """Create a symbolic link.
    filename: target name of symblic link. Should be an existing filename.
    linkename: name of new symblic link to be created."""
    from os import remove
    from os.path import exists
    if exists(linkname): remove(linkname)
    # Replacememnt for os.symlink that is platform independent. 
    try:
        from os import symlink
        symlink(filename,linkname)
    except ImportError:
        import win32file
        win32file.CreateSymbolicLink(linkname,filename,0)
    # flag 0 = filename

# for backward compatibility with Python 2.4
def any(list):
    """Is any of the elements of the list true?"""
    for x in list:
        if x: return True
    return False

def version():
    import lecroy_scope_server
    return lecroy_scope_server.__version__

def Windows_pathname(pathname):
    """Translate between UNIX-style to Windows-style pathnames
    E.g. "//id14bxf/data" to "\\id14bxf\data"""
    pathname = pathname.replace("/","\\")
    return pathname


if __name__ == "__main__":
    import logging
    from tempfile import gettempdir
    format = "%(asctime)s %(levelname)s: %(message)s"
    logfile = gettempdir()+"/lecroy_scope_server.log"
    logging.basicConfig(level=logging.INFO,format=format)
    from logging_filename import log_to_file
    log_to_file(logfile,"INFO")

    scope.name = "xray_scope"
    from sys import argv
    if len(argv) >= 2: scope.name = argv[1]
    info("scope.trig_count_name = %r" % scope.trig_count_name)
    info("scope.acq_count_name = %r" % scope.acq_count_name)

    ##import autoreload
    
    self = scope # for debugging
    run_server()
