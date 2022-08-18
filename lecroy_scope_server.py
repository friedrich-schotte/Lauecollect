"""
This is a server module that allows to remote control and monitor a
LeCroy oscilloscope. This module needs to run one the same PC as the
oscilloscope.
This module serves the oscilloscope up on the network using on TCP port
1860. Multiple concurrent connections are allowed. A client application can
either send a single command one a TCP connection and then close it,
or kept the connection alive indefinitely and send all commands over than same
connection.
This module works for all of LeCray's PC-based X-Stream series oscilloscopes,
like WaveSurfer, WaveRunner and WaveMaster series.
Remote control is implemented using the DCOM (Distributes Common Object Model)
interface of the LeCroyXStreamDSO application.
The oscilloscope software has got two remote control interfaces. The classic
GPIB command set is served on TCP port 1861, encapsulated in packets with binary
VICP (Virtual Instrument Control Protocol) headers. This command set is
described in LeCroy's "WaveRunner 6000A Series Remote Control Manual".
This interface has the drawback that one concurrent client connection is
supported, there is a two-second delay for disconnecting and reconnecting and
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
Each command needs to be terminated by newline character when sent to the
server. A carriage return character at the end is allowed, but not required.

A quick way to find a command is to launch the "XStream Browser" application
on the oscilloscope PC and browser the command set with the Explorer-like
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

Example:
Measure.P1.GateStart = 0.95 or Measure.P1.GateStart.Value = 0.95
sets the low limit of the gate of measurement P1 to 0.95 divisions.
Measure.P1.last.Result.Value
Reads the current value of measurement P1
Measure.P1.num.Result.Value
Reads the number of measurement that where averaged.

Author: Friedrich Schotte
Date created: 2008-03-28
Date last modified: 2022-08-03
Revision comment: Issue:
    line 363, in scope_trace_filename
    filename = self.file_basenames[i]
    IndexError: list index out of range
"""
__version__ = "2.15.11"

import traceback
import logging
from logging import debug, info, warning, error

from numpy import nan, inf

from cached_function import cached_function
from handler_method import handler_method


def value_property(query_string, default_value=nan, timeout=inf):
    """A property representing a value that can be read and set"""

    def fget(self):
        value = self.query(query_string)
        dtype = type(default_value)
        if dtype != str:
            # noinspection PyBroadException
            try:
                value = dtype(eval(value))
            except Exception:
                value = default_value
        return value

    def fset(self, value):
        self.send("%s = %r" % (query_string, value))

    prop = property(fget, fset)

    from cached_property import cached_property
    prop = cached_property(prop, timeout)
    return prop


def action_property(command, setup=None):
    """A property representing an action that can be executed"""

    def fget(_self):
        return 0

    def fset(self, value):
        if value:
            if setup:
                getattr(self, setup)()
            self.send(command)

    return property(fget, fset)


def method_property(method):
    """A property representing a method"""

    def fget(_self): return False

    def fset(self, value):
        if value:
            method(self)

    return property(fget, fset)


class Lecroy_Scope(object):
    from db_property import db_property
    from thread_property_2 import thread_property
    from numpy import nan
    from cached_property import cached_property
    from alias_property import alias_property
    from threading import Lock

    def __init__(self, name=None):
        """name: "domain_name.basename" e.g. "BioCARS.xray_scope" """
        if name:
            self.name = name

        self.timing_reset = True
        self.trace_counts_reset = True
        self.trigger_counts_reset = True

        self.emptying_trace_directory = False
        self.monitoring_trace_count = False
        self.auto_acquire_running = False
        self.auto_synchronize_running = False

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)

    domain_name = "BioCARS"
    base_name = "lecroy_scope"

    def get_name(self):
        return self.domain_name + "." + self.base_name

    def set_name(self, value):
        if "." in value:
            self.domain_name, self.base_name = value.split(".", 1)
        else:
            self.domain_name, self.base_name = "BioCARS", value
        self.server.ip_address_and_port_db = self.name + ".ip_address"

    name = property(get_name, set_name)

    @property
    def db_name(self):
        return "lecroy_scope/%s/%s" % (self.domain_name, self.base_name)

    @cached_property
    @property
    def IOC(self):
        return Lecroy_Scope_IOC(self)

    @cached_property
    @property
    def server(self):
        from tcp_server import tcp_server
        instrument = self  # needed for locals()
        scope = self  # needed for locals()
        LeCroy = self  # needed for locals()? backward compatibility?
        server = tcp_server(globals=globals(), locals=locals())
        server.ip_address_and_port_db = self.name + ".ip_address"
        return server

    @property
    def server_port(self):
        return self.server.listening_port

    recorded_events = {}
    recorded_events_lock = Lock()

    def limit_recorded_events(self):
        keys_to_discard = sorted(self.recorded_events.keys())[0:-20]
        for key in keys_to_discard:
            del self.recorded_events[key]

    @property
    def monitoring_timing_system_acquisition(self):
        return all([
            self.trig_count_handler in self.trig_count_reference.monitors,
            self.acq_count_handler in self.acq_count_reference.monitors,
        ])

    @monitoring_timing_system_acquisition.setter
    def monitoring_timing_system_acquisition(self, value):
        if bool(value) != self.monitoring_timing_system_acquisition:
            if value:
                self.trig_count_reference.monitors.add(self.trig_count_handler)
                self.acq_count_reference.monitors.add(self.acq_count_handler)
            else:
                self.trig_count_reference.monitors.remove(self.trig_count_handler)
                self.acq_count_reference.monitors.remove(self.acq_count_handler)

    @property
    def trig_count_reference(self):
        from reference import reference
        return reference(self.trig_count_reg, "count")

    @property
    def acq_count_reference(self):
        from reference import reference
        return reference(self.acq_count_reg, "count")

    @property
    def trig_count_handler(self):
        from handler import handler
        return handler(self.handle_timing_system_update, "trig_count")

    @property
    def acq_count_handler(self):
        from handler import handler
        return handler(self.handle_timing_system_update, "acq_count")

    def handle_timing_system_update(self, name, event):
        with self.recorded_events_lock:
            self.limit_recorded_events()
            if event.time not in self.recorded_events:
                self.recorded_events[event.time] = {}
            recorded_event = self.recorded_events[event.time]
            recorded_event[name] = event.value
            if "trig_count" in recorded_event and "acq_count" in recorded_event:
                acq_count = recorded_event["acq_count"]
                trig_count = recorded_event["trig_count"]
                self.register_acq_count_as_trig_count(acq_count, trig_count)

    def register_acq_count_as_trig_count(self, acq_count, trig_count):
        from os.path import basename
        for channel_index, channel_name in enumerate(self.enabled_channels):
            filename = self.save_filename(acq_count, channel_name)
            if filename:
                info("Acquiring %r: trig %r: %s" % (acq_count, trig_count, basename(filename)))
                self.files_to_save[trig_count, channel_index] = filename

    # When the trace count reaches 99999, it goes to 100000, then wraps back
    # to 00000.
    trace_count_wrap_period = 100001
    wrap = trace_count_wrap_period

    @property
    def default_timing_system_channel_mnemonic(self):
        mnemonic = self.base_name
        if self.base_name == "xray_scope":
            mnemonic = "xosct"
        if self.base_name == "laser_scope":
            mnemonic = "losct"
        return mnemonic

    timing_system_channel_mnemonic = db_property(
        "timing_system_channel_mnemonic",
        default_timing_system_channel_mnemonic
    )

    @property
    def timing_system_channel(self):
        return getattr(self.timing_system.channels,
                       self.timing_system_channel_mnemonic)

    @property
    def trig_count_reg(self):
        """Timing system register object"""
        return self.timing_system_channel.trig_count

    @property
    def acq_count_reg(self):
        """Timing system register object"""
        return self.timing_system_channel.acq_count

    # for trace files
    channel = 1
    trace_filenames = {}
    files_to_save = {}
    filenames = []
    times = []

    auto_synchronize = db_property("auto_synchronize", False)

    @thread_property
    def auto_synchronize_running(self):
        from thread_property_2 import cancelled
        from sleep import sleep
        while not cancelled():
            sleep(10)
            if self.auto_synchronize:
                if self.monitoring_timing:
                    if not self.trace_count_synchronized:
                        self.trace_count_synchronized = True

    def get_trace_count_synchronized(self):
        synchronized = (
                abs(self.trace_count_offset) <= 1 and
                abs(self.timing_offset) < 0.3 and
                self.timing_jitter < 0.1
        )
        return synchronized

    def set_trace_count_synchronized(self, value):
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

    def set_trace_count_offset(self, offset):
        """Synchronize the timing system's trigger count with the trace
        file count
        offset should be zero"""
        self.timing_system_trigger_count = self.trace_count - offset

    trace_count_offset = property(get_trace_count_offset, set_trace_count_offset)

    def get_trace_acquisition_running(self):
        return self.monitoring_timing_system_acquisition and self.save_traces_running

    def set_trace_acquisition_running(self, value):
        self.monitoring_timing_system_acquisition = value
        self.save_traces_running = value

    trace_acquisition_running = \
        property(get_trace_acquisition_running, set_trace_acquisition_running)

    def save_filename(self, acq_count, channel_name):
        """
        acq_count: 1-based index
        channel_name: "C1", "C2", ..."""
        filename = self.scope_trace_filename(self.base_name, acq_count - 1, channel_name)
        return filename

    def scope_trace_filename(self, name, acq_count, channel_name):
        """
        name: "xray_scope" or "laser_scope"
        acq_count: 0-based index
        channel_name: "C1", "C2", ...
        """
        N = self.sequences_per_scan_point
        i = acq_count // N
        if i < len(self.file_basenames):
            filename = self.file_basenames[i]
            suffix = "_%02.0f" % (acq_count % N + 1)
            filename = filename + suffix
            filename = filename + "_" + channel_name
            subdir = name.replace("_scope", "") + "_traces"
            filename = self.directory + "/" + subdir + "/" + filename + ".trc"
        else:
            logging.warning(f"{name}: Dataset has no filename for acq_count={acq_count}")
            filename = ""
        return filename

    file_basenames = alias_property("acquisition_client.file_basenames")
    directory = alias_property("acquisition_client.directory")
    sequences_per_scan_point = alias_property("acquisition_client.sequences_per_scan_point")

    acquisition_driver = alias_property("domain.acquisition_driver")
    acquisition_client = alias_property("domain.acquisition_client")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    __save_traces_running__ = False
    from threading import Thread
    save_traces_task = Thread()

    def get_save_traces_running(self):
        return self.save_traces_task.is_alive()

    def set_save_traces_running(self, value):
        if value != self.save_traces_running:
            if value:
                from threading import Thread
                self.save_traces_task = Thread(target=self.save_traces_forever,
                                               name="save_traces_forever")
                self.save_traces_task.daemon = True
                self.__save_traces_running__ = True
                self.save_traces_task.start()
            else:
                self.__save_traces_running__ = False

    save_traces_running = property(get_save_traces_running, set_save_traces_running)

    def save_traces_forever(self):
        from time import sleep
        while self.__save_traces_running__:
            try:
                self.save_traces_once()
            except Exception as msg:
                error("%s\n%s", msg, traceback.print_exc())
            sleep(0.1)

    def save_traces_once(self):
        from os.path import exists
        from normpath import normpath
        for count, i in list(self.files_to_save.keys()):
            source = self.trace_filename(i, count)
            if exists(source):
                destination = self.files_to_save[count, i]
                if destination:
                    destination = normpath(destination)
                    # from os.path basename
                    # info("Saving %r as %r", basename(source), basename(destination))
                    info("Saving %r as %r", source, destination)
                    copy(source, destination)
                del self.files_to_save[count, i]
            else:
                info(f"File {source!r} not found")

    timing_system_acquiring = alias_property("timing_system.registers.acquiring.count")

    def get_timing_system_trigger_count(self):
        return self.trig_count_reg.value

    def set_timing_system_trigger_count(self, value):
        self.trig_count_reg.value = value

    timing_system_trigger_count = property(get_timing_system_trigger_count,
                                           set_timing_system_trigger_count)
    trigger_count = timing_system_trigger_count

    def get_timing_system_acq_count(self):
        return self.acq_count_reg.count

    def set_timing_system_acq_count(self, value):
        self.acq_count_reg.count = value

    timing_system_acq_count = property(get_timing_system_acq_count,
                                       set_timing_system_acq_count)

    def trace_filename(self, i, count):
        """Trace file name on oscilloscope's internal file system
        i: trace number, e.g. 0 = CH1, 1 = CH2
        count: trigger count (starting with 0)"""
        filename = ""
        if i < len(self.trace_source):
            trace_source = self.trace_sources[i]
            format_str = "%s\\%s%s%05.0f.trc"
            if self.software_version >= "8.2":
                format_str = "%s\\%s--%s--%05.0f.trc"
            filename = format_str % (self.trace_directory, trace_source, self.trace_title, count)
        return filename

    def file_trace_count(self, filename):
        from os.path import basename, splitext
        name = basename(filename)
        name = splitext(name)[0]
        if name.startswith("C"):
            name = name[2:]
        name = name.replace(self.trace_title, "")
        name = name.replace("--", "")  # for software version 8
        try:
            count = int(name)
        except Exception as msg:
            warning("%s: %r: %s" % (filename, name, msg))
            count = -1
        return count

    @property
    def software_version(self):
        ID_string = self.ID_string
        software_version = ID_string.split(",")[-1]
        return software_version

    def get_trace_directory_size(self):
        """Number of saved trace files"""
        if self.__trace_directory_size__ is None:
            self.__trace_directory_size__ = number_of_files(self.trace_directory)
        return self.__trace_directory_size__

    __trace_directory_size__ = None

    def set_trace_directory_size(self, value):
        if value == 0:
            self.emptying_trace_directory = True

    trace_directory_size = property(get_trace_directory_size, set_trace_directory_size)

    trace_count = 0

    def value(self, query_string, default_value=nan):
        """Performs a query and returns the result as a specific data type,
        e.g. float, matching the given default value"""
        value = self.query(query_string)
        dtype = type(default_value)
        if dtype != str:
            # noinspection PyBroadException
            try:
                value = dtype(eval(value))
            except Exception:
                value = default_value
        return value

    def query(self, query_string):
        """Execute a command that generates a reply"""
        if not query_string.startswith("LeCroy.XStreamDSO."):
            query_string = "LeCroy.XStreamDSO." + query_string
        debug("Evaluating query: '%.800s'" % query_string)
        try:
            # noinspection PyUnusedLocal
            LeCroy = self.COM_object  # needed for eval
            reply = eval(query_string)
        # noinspection PyBroadException
        except Exception as x:
            if self.report(query_string):
                error("%r: %s" % (query_string, x))
            reply = ""
        if reply is not None:
            # noinspection PyBroadException
            try:
                reply = str(reply)
            except Exception:
                reply = shortened_repr(reply)
        else:
            reply = ""
        if self.report(query_string):
            info("%s? %.800s" % (query_string, reply))
        return reply

    def send(self, command):
        """Execute a command that does not generate a reply"""
        if not command.startswith("LeCroy.XStreamDSO."):
            command = "LeCroy.XStreamDSO." + command
        # noinspection PyUnusedLocal
        LeCroy = self.COM_object  # for exec
        info("Executing command: %.800s" % command)
        try:
            exec(command)
        except Exception as x:
            error("%r: %s" % (command, x))

    report_filter = [
        "last.Result.Value",
        "SaveRecall.Waveform.AutoSave",
        ".View",
        "SaveRecall.Setup.PanelFilename",
        "SaveRecall.Waveform.SaveSource",
    ]

    def report(self, query_string):
        """Generate a diagnostics message for this command?"""
        self.report_count[query_string] = self.report_count.get(query_string, 0) + 1
        report = True
        matches = False
        for string in self.report_filter:
            if string in query_string:
                matches = True
        if matches and self.report_count[query_string] > 3:
            report = False
        return report

    report_count = {}

    class COM_Object:
        """'LeCroy.XStreamDSO' COM object"""

        def __init__(self):
            try:
                from pythoncom import CoInitialize  # need to install pywin32
            except ImportError:
                def CoInitialize():
                    pass
            CoInitialize()  # needed only when run in a thread

            try:
                from win32com.client import Dispatch  # need to install pywin32
            except ImportError:
                def Dispatch(_name):
                    return object()

            self.XStreamDSO = Dispatch("LeCroy.XStreamDSO")

    @property
    def COM_object(self):
        """'LeCroy.XStreamDSO' COM object"""
        return self.COM_Object()

    # COM_object = cached_property(COM_object, inf)

    @property
    def XStreamDSO(self):
        return self.COM_object.XStreamDSO

    def get_setup(self):
        return self.setup_name

    def set_setup(self, name):
        self.setup_name = name
        if self.setup_name != "":
            self.setup_recall = True

    setup = property(get_setup, set_setup)

    @property
    def setup_choices(self):
        from os import listdir
        dirname = self.local_setup_dirname
        try:
            files = listdir(dirname)
        except Exception as msg:
            files = []
            warning("%s: %s" % (dirname, msg))
        files = [file for file in files if not file.startswith(".")]
        files = [file for file in files if file.endswith(".lss")]
        names = [file.replace(".lss", "") for file in files]
        return names

    setups = setup_choices

    def get_setup_name(self):
        from os.path import basename
        name = basename(self.setup_filename).replace(".lss", "")
        return name

    def set_setup_name(self, name):
        self.setup_filename = self.local_setup_filename(name)

    setup_name = property(get_setup_name, set_setup_name)

    def get_setup_filename(self):
        filename = self.setup_dirname + "/" + self.setup_basename
        from normpath import normpath
        filename = normpath(filename)
        return filename

    def set_setup_filename(self, filename):
        from normpath import normpath
        filename = Windows_pathname(normpath(filename))
        from os.path import dirname, basename
        directory, file = dirname(filename), basename(filename)
        self.setup_dirname = directory
        self.setup_basename = file

    setup_filename = property(get_setup_filename, set_setup_filename)

    setup_dirname = value_property("SaveRecall.Setup.PanelDir.Value", "")
    setup_basename = value_property("SaveRecall.Setup.PanelFilename.Value", "", timeout=10)

    def update_setup_name(self):
        self.setup_filename = self.local_setup_filename(self.setup_name)

    setup_save = action_property("SaveRecall.Setup.DoSavePanel.ActNow()", setup="update_setup_name")
    setup_recall = action_property("SaveRecall.Setup.DoRecallPanel.ActNow()", setup="update_setup_name")

    trace_directory = value_property("SaveRecall.Waveform.WaveformDir.Value", "")
    trace_title = value_property("SaveRecall.Waveform.TraceTitle.Value", "")
    trace_source = value_property("SaveRecall.Waveform.SaveSource.Value", "", timeout=10)

    ntp_servers = value_property("Utility.DateTimeSetup.NTPServers", "")
    set_time_from_SNTP = action_property("Utility.DateTimeSetup.SetFromSNTP.ActNow()")
    sync_timestamp_generator = action_property("Utility.DateTimeSetup.SyncTimeStampGenerator.ActNow()")

    def timestamp_generator_setup(self):
        # self.ntp_servers = "femto.niddk.nih.gov"
        # self.set_time_from_SNTP = True
        self.sync_timestamp_generator = True

    @property
    def trace_sources(self):
        sources = []
        source = self.trace_source
        if source == "AllDisplayed":
            sources = self.enabled_channels
        elif source != "":
            sources = [source]
        return sources

    channels = "C1", "C2", "C3", "C4"

    for channel in channels:
        exec('%s_on = value_property("Acquisition.%s.View.Value",False,timeout=10)'
             % (channel, channel))

    @property
    def enabled_channels(self):
        names = []
        for name in self.channels:
            if getattr(self, name + "_on", False):
                names += [name]
        return names

    measurements = ["P1", "P2", "P3", "P4"]

    P1_on = value_property("Measure.P1.View.Value", False, timeout=inf)
    P2_on = value_property("Measure.P2.View.Value", False, timeout=inf)
    P3_on = value_property("Measure.P3.View.Value", False, timeout=inf)
    P4_on = value_property("Measure.P4.View.Value", False, timeout=inf)

    @property
    def enabled_measurements(self):
        names = []
        for name in self.measurements:
            if getattr(self, name + "_on", False):
                names += [name]
        return names

    ID_string = value_property("InstrumentID.Value", "")
    id = ID_string

    @property
    def local_setup_dirname(self):
        from module_dir import module_dir
        directory = "%s/lecroy_scope/%s/%s" % \
                    (module_dir(self), self.domain_name, self.base_name)
        # debug("local_setup_dirname: %r" % directory)
        return directory

    def local_setup_filename(self, name):
        if name != "":
            filename = self.local_setup_dirname + "/" + name + ".lss"
        else:
            filename = ""
        return filename

    @thread_property
    def emptying_trace_directory(self):
        """Erase all temporary trace files"""
        from thread_property_2 import cancelled
        directory = self.trace_directory
        filenames = listdir(directory)
        self.__trace_directory_size__ = len(filenames)
        from os import remove
        for i, filename in enumerate(filenames):
            if cancelled():
                break
            pathname = directory + "/" + filename
            try:
                remove(pathname)
            except Exception as msg:
                info("%s: %s" % (pathname, msg))
        filenames = listdir(directory)
        self.__trace_directory_size__ = len(filenames)

    auto_acquire = db_property("auto_acquire", False)

    @thread_property
    def auto_acquire_running(self):
        from thread_property_2 import cancelled
        from sleep import sleep
        while not cancelled():
            sleep(10)
            if self.auto_acquire:
                if not self.acquiring_waveforms:
                    self.acquiring_waveforms = True

    def get_acquiring_waveforms(self):
        """Are trace currently being auto-saved?"""
        return self.waveform_autosave != "Off"

    def set_acquiring_waveforms(self, value):
        if value:
            self.timestamp_generator_setup()
            self.trace_directory = "D:\\Waveforms\\"
            mkdir(self.trace_directory)
            self.waveform_autosave = "Wrap"
        else:
            self.waveform_autosave = "Off"

    acquiring_waveforms = property(get_acquiring_waveforms, set_acquiring_waveforms)

    waveform_autosave = value_property("SaveRecall.Waveform.AutoSave.Value", "", timeout=10)

    def get_monitoring_timing(self):
        """Collecting information to check that trace acquisition is
        synchronized?"""
        return self.monitoring_trace_count and self.monitoring_trig_count

    def set_monitoring_timing(self, value):
        if self.monitoring_trace_count_allowed:
            self.monitoring_trace_count = value
        self.monitoring_trig_count = value

    monitoring_timing = property(get_monitoring_timing, set_monitoring_timing)

    @method_property
    def timing_reset(self):
        self.trace_counts_reset = True
        self.trigger_counts_reset = True

    @thread_property
    def monitoring_trace_count(self):
        """Watch trace directory for new files"""
        from thread_property_2 import cancelled
        while self.monitoring_trace_count_allowed and not cancelled():
            directory = self.trace_directory
            from os.path import exists
            from time import sleep
            if not exists(directory):
                sleep(1)
            else:
                # http://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
                import win32file
                import win32con

                ACTIONS = {
                    1: "Created",
                    2: "Deleted",
                    3: "Updated",
                    4: "Renamed from something",
                    5: "Renamed to something"
                }
                FILE_LIST_DIRECTORY = 0x0001
                hDir = win32file.CreateFile(
                    directory,
                    FILE_LIST_DIRECTORY,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_FLAG_BACKUP_SEMANTICS,
                    None,
                )
                while self.monitoring_trace_count_allowed and not cancelled():
                    # ReadDirectoryChangesW takes a previously-created handle to a
                    # directory, a buffer size for results, a flag to indicate whether
                    # to watch subtrees and a filter of what changes to notify.
                    #
                    # Need to up the buffer size to be sure of picking up all events when
                    # a large number of files were deleted at once.
                    results = win32file.ReadDirectoryChangesW(
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
                    for action_code, filename in results:
                        action = ACTIONS.get(action_code, "Unknown")
                        if action != "Deleted":
                            debug("%s: %s" % (filename, action))
                        if action == "Updated":
                            self.trace_counts_handle(filename)
                        if action == "Created":
                            self.__trace_directory_size__ += 1
                        if action == "Deleted":
                            self.__trace_directory_size__ -= 1

    def trace_counts_handle(self, filename):
        from time import time
        t = time()
        n = self.file_trace_count(filename)
        if n >= 0:
            debug("Trace count %d" % n)
            self.trace_counts_add(n, t)
            self.trace_count = n

    monitoring_trace_count_allowed = True

    trace_counts_dict = {}

    @method_property
    def trace_counts_reset(self):
        self.trace_counts_dict = {}

    def trace_counts_add(self, n, t):
        self.trace_counts_limit()
        self.trace_counts_dict[n] = t

    @property
    def trace_counts_history(self):
        """list of timestamps plus list of trace counts"""
        nt_pairs = self.trace_counts_dict.items()
        ts = [t for n, t in nt_pairs]
        ns = [n for n, t in nt_pairs]
        return ts, ns

    def trace_counts_limit(self):
        dt = 60
        from time import time
        t = time()
        # Work with a copy, in case the dictionary changes.
        trace_counts = dict(self.trace_counts_dict)
        for n in list(trace_counts.keys()):
            if trace_counts[n] < t - dt:
                del trace_counts[n]
        self.trace_counts_dict = trace_counts

    @property
    def monitoring_trig_count(self):
        return self.trigger_counts_handle in self.trig_count_reference.monitors

    @monitoring_trig_count.setter
    def monitoring_trig_count(self, value):
        if bool(value) != self.monitoring_trig_count:
            if value:
                self.trig_count_reference.monitors.add(self.trigger_counts_handle)
            else:
                self.trig_count_reference.monitors.remove(self.trigger_counts_handle)

    @handler_method
    def trigger_counts_handle(self, event):
        self.trigger_counts_add(event.value, event.time)
        debug(f"Trigger count {event.value}")

    trigger_counts_dict = {}

    @method_property
    def trigger_counts_reset(self):
        self.trigger_counts_dict = {}

    def trigger_counts_add(self, n, t):
        self.trigger_counts_limit()
        self.trigger_counts_dict[n] = t

    @property
    def trigger_counts_history(self):
        """list of timestamps plus list of trigger counts"""
        nt_pairs = self.trigger_counts_dict.items()
        ts = [t for n, t in nt_pairs]
        ns = [n for n, t in nt_pairs]
        return ts, ns

    def trigger_counts_limit(self):
        dt = 60
        from time import time
        t = time()
        # Work with a copy, in case the dictionary changes.
        trigger_counts = dict(self.trigger_counts_dict)
        for n in list(trigger_counts.keys()):
            if trigger_counts[n] < t - dt:
                del trigger_counts[n]
        self.trigger_counts_dict = trigger_counts

    @property
    def timing_differences(self):
        self.monitoring_timing = True
        self.auto_acquire_running = True
        self.auto_synchronize_running = True
        t, n = self.trace_counts_history
        trace_nt = dict(zip(n, t))
        t, n = self.trigger_counts_history
        trigger_nt = dict(zip(n, t))
        dt = []
        for trigger_count in trigger_nt:
            trace_count = trigger_count % self.wrap
            if trace_count in trace_nt:
                dt += [trace_nt[trace_count] - trigger_nt[trigger_count]]
        return dt

    @property
    def timing_jitter(self):
        # Suppress "RuntimeWarning: Degrees of freedom <= 0 for slice."
        import numpy
        numpy.warnings.filterwarnings('ignore')
        from numpy import std
        return std(self.timing_differences)

    @property
    def timing_offset(self):
        # Suppress "RuntimeWarning: Mean of empty slice"
        import numpy
        numpy.warnings.filterwarnings('ignore')
        from numpy import mean
        return mean(self.timing_differences)

    class measurement_object(object):
        """For automated measurements, including averaging and statistics"""

        def __init__(self, instrument, n=1, measurement_type="value"):
            """n=1,2...6 is the waveform parameter number.
            The parameter is defined from the "Measure" menu, e.g. P1:delay(C3).
            The optional 'type' can be "value","min","max","stdev",or "count".
            """
            self.instrument = instrument
            self.n = n
            self.type = measurement_type

        def __repr__(self):
            return repr(self.instrument) + ".measurement(" + str(self.n) + ")." + self.type

        def get_value(self):
            n = self.n
            if self.type == "value":
                return self.instrument.value("Measure.P%d.last.Result.Value" % n)
            if self.type == "average":
                return self.instrument.value("Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":
                return self.instrument.value("Measure.P%d.min.Result.Value" % n)
            if self.type == "max":
                return self.instrument.value("Measure.P%d.max.Result.Value" % n)
            if self.type == "stdev":
                return self.instrument.value("Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":
                return self.instrument.value("Measure.P%d.num.Result.Value" % n)
            from numpy import nan
            return nan

        value = property(get_value, doc="last sample (without averaging)")

        def get_average(self):
            n = self.n
            if self.type == "value":
                return self.instrument.value("Measure.P%d.mean.Result.Value" % n)
            if self.type == "average":
                return self.instrument.value("Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":
                return self.instrument.value("Measure.P%d.min.Result.Value" % n)
            if self.type == "max":
                return self.instrument.value("Measure.P%d.max.Result.Value" % n)
            if self.type == "stdev":
                return self.instrument.value("Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":
                return self.instrument.value("Measure.P%d.num.Result.Value" % n)
            from numpy import nan
            return nan

        average = property(get_average, doc="accumulated average")

        def get_max(self):
            return self.instrument.value("Measure.P%d.max.Result.Value" % self.n)

        max = property(get_max, doc="maximum value contributing to average")

        def get_min(self):
            return self.instrument.value("Measure.P%d.min.Result.Value" % self.n)

        min = property(get_min, doc="minimum value contributing to average")

        def get_stdev(self):
            return self.instrument.value("Measure.P%d.sdev.Result.Value" % self.n)

        stdev = property(get_stdev, doc="standard deviation of individuals sample")

        def get_count(self):
            return self.instrument.value("Measure.P%d.num.Result.Value" % self.n)

        count = property(get_count, doc="number of measurement averaged")

        def get_name(self):
            return self.instrument.query("Measure.P%d.Equation.Value" % self.n) + "." + self.type

        name = property(get_name, doc="string representation of the measurement")

        def get_unit(self):
            return self.instrument.query("Measure.P%d.num.Result.VerticalUnits.Value")

        unit = property(get_unit, doc="unit symbol of measurement (if available)")

        def start(self):
            self.instrument.start()

        def stop(self):
            self.instrument.stop()

        def clear_sweeps(self):
            self.instrument.clear_sweeps()

        reset_average = clear_sweeps
        reset_statistics = clear_sweeps

        def get_gate(self):
            return self.instrument.gate(self.n)

        gate = property(get_gate, doc="start of measurement gate")

        def get_enabled(self):
            return self.instrument.measurement_enabled

        def set_enabled(self, value):
            self.instrument.measurement_enabled = value

        enabled = property(get_enabled, set_enabled)

    def measurement(self, n=1, measurement_type="value"):
        return self.measurement_object(self, n, measurement_type)

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

    def update_period(self, name):
        """How often to refresh a certain property?"""
        from numpy import inf
        period = inf
        if name in self.enabled_measurements:
            period = self.min_update_period
        if name == "waveform_autosave":
            period = 10
        if name == "trace_sources":
            period = 10
        return period

    min_update_period = 0.024

    @property
    def timing_system(self):
        return self.domain.timing_system_client

    timing_system_name = "BioCARS"


class Lecroy_Scope_IOC(object):
    def __init__(self, instrument):
        self.instrument = instrument

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.instrument)

    @property
    def name(self):
        return self.instrument.name

    @property
    def prefix(self):
        class_name = 'lecroy_scope'
        prefix = f"{self.instrument.domain_name}:{class_name}.{self.instrument.base_name}."
        prefix = prefix.upper()
        return prefix

    @property
    def db_name(self):
        return self.instrument.db_name

    from db_property import db_property
    scan_period = db_property("scan_period", 2.0)

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
        "server_port",
    ]

    from thread_property_2 import thread_property

    @thread_property
    def running(self):
        info("Starting IOC: Prefix: %s ..." % self.prefix)
        from thread_property_2 import cancelled
        from CAServer import casput, casdel
        from time import time
        from sleep import sleep

        self.monitors_setup()

        while not cancelled():
            t = time()
            for name in self.property_names:
                if time() - self.last_updated(name) > self.update_period(name):
                    PV_name = self.prefix + name.upper()
                    value = getattr(self.instrument, name)
                    # info("Update: %s=%r" % (PV_name,value))
                    casput(PV_name, value, update=False)
                    self.set_update_time(name)
            if not cancelled():
                sleep(t + self.min_update_period - time())
        casdel(self.prefix)

    last_updated_dict = {}

    def set_update_time(self, name):
        from time import time
        self.last_updated_dict[name] = time()

    def last_updated(self, name):
        return self.last_updated_dict.get(name, 0)

    def update_period(self, name):
        period = self.instrument.update_period(name)
        period = min(period, self.scan_period)
        return period

    @property
    def min_update_period(self):
        return self.instrument.min_update_period

    def monitors_setup(self):
        """Monitor client-writable PVs."""
        from CAServer import casmonitor
        for name in self.property_names:
            PV_name = self.prefix + name.upper()
            casmonitor(PV_name, callback=self.monitor)

    def monitor(self, PV_name, value, _char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name, value))
        from CAServer import casput
        for name in self.property_names:
            if PV_name == self.prefix + name.upper():
                setattr(self.instrument, name, value)
                casput(PV_name, getattr(self.instrument, name))


def number_of_files(directory):
    n_files = len(listdir(directory))
    info("Number of files in %r: %r" % (directory, n_files))
    return n_files


def monitor_directory(directory):
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class MyHandler(FileSystemEventHandler):
        def on_modified(self, event):
            info("%s: %d files" % (directory, number_of_files(directory)))

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=False)
    observer.start()


def listdir(directory):
    info("Reading directory %r..." % (directory,))
    from os import listdir
    try:
        files = listdir(directory)
    except Exception as msg:
        debug("%r: %s" % (directory, msg))
        files = []
    info("Reading directory %r done." % (directory,))
    return files


def getmtime(pathname):
    """The last modification time of a file in seconds since Jan 1, 2015"""
    from os.path import exists, getmtime
    if not exists(pathname):
        return 0.0
    return getmtime(pathname)


def mtimes(pathnames):
    """The last modification time of a list of files,
    in seconds since Jan 1, 2015"""
    return [getmtime(f) for f in pathnames]


def rename(source, destination):
    """Rename of move a file."""
    if destination == source:
        return
    from os import rename, remove
    from os.path import exists, dirname
    if exists(destination):
        remove(destination)
    directory = dirname(destination)
    if directory and not exists(directory):
        mkdir(directory)
    rename(source, destination)


def copy_files(source_files, destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'."""
    from threading import Thread
    Thread(target=__copy_files__, args=(source_files, destination_files), daemon=True).start()


def __copy_files__(source_files, destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'."""
    for s, d in zip(source_files, destination_files):
        copy(s, d)


def migrate_files(source_files, destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files'.
    source_files: list of strings
    destination_files: list of strings"""
    from threading import Thread
    Thread(target=__migrate_files__, args=(source_files, destination_files), daemon=True).start()


def __migrate_files__(source_files, destination_files):
    """Copy each file in the list 'source_files' to the corresponding file
    in 'destination_files' and remove the source.
    source_files: list of strings
    destination_files: list of strings"""
    from time import sleep
    from os.path import dirname, exists

    directory = dirname(source_files[0]) if len(source_files) > 0 else ""
    global migrate_directory
    migrate_directory = directory

    copied = [False] * len(source_files)
    while directory == migrate_directory and not all(copied):
        for i in range(0, len(source_files)):
            if copied[i]:
                continue
            if not exists(source_files[i]):
                sleep(1)
                break  # Copying caught up with collection.
            copy(source_files[i], destination_files[i])
            if exists(destination_files[i]):
                copied[i] = True
    # Make one last attempt after acquisition finished.
    for i in range(0, len(source_files)):
        if not copied[i]:
            copy(source_files[i], destination_files[i])
            if exists(destination_files[i]):
                copied[i] = True
    # Clean up.
    for i in range(0, len(source_files)):
        if copied[i]:
            remove(source_files[i])
    from os import rmdir
    rmdir(directory)


migrate_directory = ""


def shortened_repr(x, n_chars=80):
    """limit string length using ellipses (...)"""
    s = __builtins__.repr(x)
    if len(s) > n_chars:
        s = s[0:n_chars - 10 - 3] + "..." + s[-10:]
    return s


def copy(source, destination):
    """Create a copy of a file with the same timestamp"""
    if destination == source:
        return
    from os import remove
    from shutil import copy2
    from os.path import exists, dirname
    if not exists(source):
        error(f"{source!r}: file not found")
        return
    if exists(destination):
        remove(destination)
    directory = dirname(destination)
    if directory and not exists(directory):
        mkdir(directory)
    try:
        copy2(source, destination)
    except Exception as msg:
        error("Error copying %r to %r: %s" % (source, destination, msg))


def remove(pathname):
    """Delete a file."""
    from os.path import exists
    if not exists(pathname):
        return
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
        except Exception as msg:
            error("Cannot create %r: %s" % (directory, msg))


def version():
    return __version__


def Windows_pathname(pathname):
    """Translate between UNIX-style to Windows-style pathnames
    E.g. "//id14bxf/data" to "\\id14bxf\\data"""
    pathname = pathname.replace("/", "\\")
    return pathname


@cached_function()
def lecroy_scope(name):
    return Lecroy_Scope(name)


def start(name):
    lecroy_scope(name).IOC.running = True
    lecroy_scope(name).server.start()


def stop(name):
    lecroy_scope(name).IOC.running = False
    lecroy_scope(name).server.stop()


def run(name):
    lecroy_scope(name).IOC.running = True
    lecroy_scope(name).server.run()


run_server = run  # for backward compatibility

if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    name = "BioCARS.xray_scope"
    # name = "BioCARS.laser_scope"
    # name = "BioCARS.diagnostics_scope"
    # name = "LaserLab.laser_scope"

    self = lecroy_scope(name)

    print(f"self = {self!r}")
    # print(f"self.trig_count_reg = {self.trig_count_reg}")
    print(f"start({self.name!r})")
    # print("self.server.start()")

    # print("lecroy_scope("BioCARS.xray_scope").server.start()")
    print("self.monitoring_timing_system_acquisition = True")
