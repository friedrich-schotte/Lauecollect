"""
This is to communicate with a LeCroy Windows-based oscilloscope over Ethernet.
This module requires the program 'lecroy_scope_server.py' to run locally
on the oscilloscope. It uses a simple TCP/IP connection, port number 2000, to
communicate with the 'lecroy_scope_server.py' program, which in turn calls
the LeCroyXStreamDSO application running on the oscilloscope via DCOM remote
procedure calls.

The command set is documented in LeCroy's "WaveMaster, WavePro Series Automation
Manual", file "Automation Manual.pdf" in "femto.niddk.nih.gov/APS/Laser Hutch/
Laser Oscilloscope".
A command that modifies a setting of the oscilloscope is, for instance,
"LeCroy.XStreamDSO.Measure.P1.GateStart.Value = 0.95". This sets the low limit of the gate
of measurement P1 to 0.95 divisions. This command generates not reply.
A query that generates a reply would be "LeCroy.XStreamDSO.Measure.P1.GateStart.Value".
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
name, e.g. "LeCroy.XStreamDSO.ClearSweeps.ActNow()".
Properties listed as 'Method' are called by appending "()" with optional
arguments to their name, e.g. "Sleep(1000)".
Commands are not case-sensitive.

Author: Friedrich Schotte
Date created: 2008-04-16
Date last modified: 2022-05-09
Revision comment: Issue: reporting online = False if setup fails
"""
__version__ = "4.8.1"

from logging import debug, warning
from numpy import nan
from cached_function import cached_function


@cached_function()
def lecroy_scope(name):
    return Lecroy_Scope(name)


def value_property(query_string, default_value=nan):
    """A property object to be used inside a class"""

    def fget(self):
        # Performs a query and returns the result as a number
        value = self.query(query_string)
        dtype = type(default_value)
        if dtype != str:
            try:
                value = dtype(eval(value))
            except Exception:
                value = default_value
        return value

    def fset(self, value):
        self.send("%s = %r" % (query_string, value))

    return property(fget, fset)


def function(property_name, formula, reverse_formula):
    """A property object to be used inside a class
    formula: e.g. 'x*10'
    reverse_formula: e.g. 'x/10.'
    """

    def fget(self):
        x = getattr(self, property_name)  # variable x needed for eval
        return eval(formula)

    def fset(self, x):  # variable x needed for eval
        setattr(self, property_name, eval(reverse_formula))

    return property(fget, fset)


def PV_object_property(name):
    @property
    def PV_object(self):
        from CA import PV
        return PV(self.prefix + name)

    return PV_object


class Lecroy_Scope(object):
    """This is to communicate with a LeCroy Windows PC-based oscilloscope over
    Ethernet."""
    from numpy import nan
    from persistent_property import persistent_property

    def __init__(self, name=None):
        """name: "domain_name.basename" e.g. "BioCARS.xray_scope" """
        if name:
            self.name = name

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

    name = property(get_name, set_name)

    @property
    def prefix(self):
        prefix = "%s:%s." % (self.domain_name, self.base_name)
        prefix = prefix.upper()
        # prefix = prefix.replace("BIOCARS", "NIH")
        return prefix

    def get_ip_address(self):
        from CA import cainfo
        return cainfo(self.prefix + "ACQUIRING_WAVEFORMS", "hostname")

    def set_ip_address(self, value):
        pass

    ip_address = property(get_ip_address, set_ip_address)

    @property
    def _ip_address_and_port(self):
        return self.ip_address + ":" + self.port

    @_ip_address_and_port.setter
    def _ip_address_and_port(self, ip_address_and_port):
        self.port = ip_address_and_port.split(":")[-1]

    @property
    def ip_address_and_port(self):
        from url import url
        return url(self.config_ip_address_and_port, ip_address=self.ip_address)

    def get_port(self):
        from CA import caget
        port = caget(self.prefix + "SERVER_PORT")
        if port is None:
            port = 2000
        return port

    def set_port(self, value):
        pass

    port = property(get_port, set_port)

    config_ip_address_and_port = persistent_property("ip_address", "pico21.niddk.nih.gov:2000")

    @property
    def online(self):
        online = self.ip_address != ""
        return online

    def query(self, command):
        """To send a command that generates a reply, e.g. "InstrumentID.Value".
        Returns the reply"""
        from tcp_client import query
        reply = query(self.ip_address_and_port, command).strip(b"\n")
        debug("%s, reply %s" % (to_repr(command), to_repr(reply)))
        return reply

    def send(self, command):
        """Sends a command to the oscilloscope that does not generate a reply,
        e.g. "LeCroy.XStreamDSO.ClearSweeps.ActNow()" """
        debug("%s" % to_repr(command))
        from tcp_client import query
        reply = query(self.ip_address_and_port, command)
        if reply.strip(b"\n"):
            debug("Got reply %s" % to_repr(reply))

    class gate_object(object):
        """This is to dynamically adjust the "Gate", defining the time range for
        and automated measurement. E.g. when you want to measure the rising edge
        of a periodic waveform which shift with respect to the trigger."""

        def __init__(self, scope, n=1):
            """n=1,2...6 is the waveform parameter number.
            The parameter is defined from the "Measure" menu, e.g. P1:delay(C3)."""
            self.scope = scope
            self.n = n

        def __repr__(self):
            return repr(self.scope) + ".gate(" + str(self.n) + ")"

        class start_object(object):
            """Changes the start of the "Gate" for an automated measurement"""

            def __init__(self, gate):
                """n=1,2...6 is the waveform parameter number.
              The parameter is defined from the "Measure" menu, e.g. P1:delay(C3)."""
                self.scope = gate.scope
                self.n = gate.n
                self.last_t = None
                self.name = "P" + str(self.n) + ".start"
                self.unit = "s"

            def __repr__(self):
                return repr(self.scope) + ".gate(" + str(self.n) + ").start"

            def get_value(self):
                """returns the last set value"""
                if self.last_t is None:
                    return self.last_t  # speed up, use cached value
                div = self.val("LeCroy.XStreamDSO.Measure.P%s.GateStart.Value" % self.n)
                # get the time base in seconds per division
                t_div = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorScale.Value")
                t0 = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorOffset.Value")
                # convert from divisions (0-10, 5 = center) to time in s
                t = (div - 5) * t_div - t0
                self.last_t = t
                return t

            def set_value(self, t):
                # get the time base in seconds per division
                t_div = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorScale.Value")
                t0 = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorOffset.Value")
                # convert from time in seconds to divisions (0-10, 5 = center)
                div = (t + t0) / t_div + 5
                if div < 0:
                    div = 0
                if div > 10:
                    div = 10
                self.scope.write("LeCroy.XStreamDSO.Measure.P" + str(self.n) + ".GateStart.Value = " + str(div))
                # cache the last value
                self.last_t = (div - 5) * t_div - t0

            value = property(get_value, set_value, doc="low limit in s")

            def val(self, query):
                """Performs a query and returns the result as a number"""
                try:
                    return float(self.scope.query(query))
                except (ValueError, TypeError):
                    return nan

        def get_start(self, n=1):
            return self.gate_object.start_object(self)

        start = property(get_start, doc="low limit of measurement gate")

        class stop_object(object):
            """Changes the start of the "Gate" for an automated measurement"""

            def __init__(self, gate):
                """n=1,2...6 is the waveform parameter number.
              The parameter is defined from the "Measure" menu, e.g. P1:delay(C3)."""
                self.scope = gate.scope
                self.n = gate.n
                self.last_t = None
                self.name = "P" + str(self.n) + ".stop"
                self.unit = "s"

            def __repr__(self):
                return repr(self.scope) + ".gate(" + str(self.n) + ").start"

            def get_value(self):
                """Last set value"""
                if self.last_t is None:
                    return self.last_t  # speed up, use cached value
                div = self.val("LeCroy.XStreamDSO.Measure.P%s.GateStop.Value" % self.n)
                # get the time base in seconds per division
                t_div = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorScale.Value")
                t0 = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorOffset.Value")
                # convert from divisions (0-10, 5 = center) to time in s
                t = (div - 5) * t_div - t0
                self.last_t = t
                return t

            def set_value(self, t):
                # get the time base in seconds per division
                t_div = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorScale.Value")
                t0 = self.val("LeCroy.XStreamDSO.Acquisition.Horizontal.HorOffset.Value")
                # convert from time in seconds to divisions (0-10, 5 = center)
                div = (t + t0) / t_div + 5
                if div < 0:
                    div = 0
                if div > 10:
                    div = 10
                self.scope.write("LeCroy.XStreamDSO.Measure.P" + str(self.n) + ".GateStop.Value = " + str(div))
                # cache the last value
                self.last_t = (div - 5) * t_div - t0

            value = property(get_value, set_value, doc="low limit in s")

            def val(self, query):
                """Performs a query and returns the result as a number"""
                try:
                    return float(self.scope.query(query))
                except (ValueError, TypeError):
                    return nan

        def get_stop(self, n=1):
            return self.gate_object.stop_object(self)

        stop = property(get_stop, doc="low limit of measurement gate")

    def gate(self, n=1):
        return self.gate_object(self, n)

    class measurement_object(object):
        """For automated measurements, including averaging and statistics"""

        def __init__(self, scope, n=1, type="value"):
            """n=1,2...6 is the waveform parameter number.
            The parameter is defined from the "Measure" menu, e.g. P1:delay(C3).
            The optional 'type' can by "value","min","max","stdev",or "count".
            """
            self.scope = scope
            self.n = n
            self.type = type

        def __repr__(self):
            return repr(self.scope) + ".measurement(" + str(self.n) + ")." + self.type

        def get_value(self):
            n = self.n
            if self.type == "value":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.last.Result.Value" % n)
            if self.type == "average":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value" % n)
            if self.type == "max":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value" % n)
            if self.type == "stdev":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value" % n)
            return nan

        value = property(get_value, doc="last sample (without averaging)")

        def get_average(self):
            n = self.n
            if self.type == "value":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "average":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.mean.Result.Value" % n)
            if self.type == "min":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value" % n)
            if self.type == "max":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value" % n)
            if self.type == "stdev":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % n)
            if self.type == "count":
                return self.val("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value" % n)
            return nan

        average = property(get_average, doc="accumulated average")

        def get_max(self):
            return self.val("LeCroy.XStreamDSO.Measure.P%d.max.Result.Value" % self.n)

        max = property(get_max, doc="maximum value contributing to average")

        def get_min(self):
            return self.val("LeCroy.XStreamDSO.Measure.P%d.min.Result.Value" % self.n)

        min = property(get_min, doc="minimum value contributing to average")

        def get_stdev(self):
            return self.val("LeCroy.XStreamDSO.Measure.P%d.sdev.Result.Value" % self.n)

        stdev = property(get_stdev, doc="standard deviation of individuals sample")

        def get_count(self):
            return self.val("LeCroy.XStreamDSO.Measure.P%d.num.Result.Value" % self.n)

        count = property(get_count, doc="number of measurement averaged")

        def get_name(self):
            return self.scope.query("LeCroy.XStreamDSO.Measure.P%d.Equation.Value" % self.n) + "." + self.type

        name = property(get_name, doc="string representation of the measurement")

        def get_unit(self):
            return self.scope.query("LeCroy.XStreamDSO.Measure.P%d.num.Result.VerticalUnits.Value")

        unit = property(get_unit, doc="unit symbol of measurement (if available)")

        def val(self, query):
            """Performs a query and returns the result as a number"""
            try:
                return float(self.scope.query(query))
            except (ValueError, TypeError):
                return nan

        def start(self):
            self.scope.start()

        def stop(self):
            self.scope.stop()

        def clear_sweeps(self):
            self.scope.clear_sweeps()

        reset_average = clear_sweeps
        reset_statistics = clear_sweeps

        def get_gate(self):
            return self.scope.gate(self.n)

        gate = property(get_gate, doc="start of measurement gate")

        def get_enabled(self):
            return self.scope.measurement_enabled

        def set_enabled(self, value):
            self.scope.measurement_enabled = value

        enabled = property(get_enabled, set_enabled)

    def measurement(self, n=1, type="value"):
        return self.measurement_object(self, n, type)

    P1 = PV_object_property("P1")
    P2 = PV_object_property("P2")
    P3 = PV_object_property("P3")
    P4 = PV_object_property("P4")
    P5 = PV_object_property("P5")
    P6 = PV_object_property("P6")
    P7 = PV_object_property("P7")
    P8 = PV_object_property("P8")

    def get_measurement_enabled(self):
        """Is the measurement active and usable?"""
        try:
            return eval(self.query("LeCroy.XStreamDSO.Measure.ShowMeasure.Value"))
        except Exception:
            return False

    def set_measurement_enabled(self, value):
        self.send("LeCroy.XStreamDSO.Measure.ShowMeasure.Value = " + str(value))

    measurement_enabled = property(get_measurement_enabled, set_measurement_enabled)

    def waveform(self, channel):
        """Recorded voltage values in units of volts.
        Channel: 1,2,3, or 4
        Return value: tuple"""
        result = self.query("LeCroy.XStreamDSO.Acquisition.C%s.Out.Result.DataArray" % channel)
        if result == "":
            return ()
        return eval(result)

    def save_waveform(self, channel, filename):
        """Generate LeCroy binary waveform file.
        channel: 1,2,3, or 4
        filename: pathname e.g. '/net/id14bxf/data/anfinrud_1203/test.trc'
        Needs to accessible to the oscilloscope computer as
        '\\\\id14bxf\\data\\anfinrud_1203\\test.trc'"""
        if filename == "" or filename is None:
            return
        from os.path import exists, dirname
        from os import makedirs
        directory = dirname(filename)
        if directory and not exists(directory):
            makedirs(directory)
        filename = Windows_pathname(filename)
        directory = filename[0:filename.rfind("\\")]
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveTo.Value = 'File'")
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveSource.Value = 'C%s'" % channel)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.WaveFormat.Value = 'Binary'")
        # BinarySubFormat is not documented in the "Automation Manual"
        # (July 2003) and "Automation Command Reference Manual" Reference
        # (2010), but shown as option in the XStream Browser,
        # under "LeCroy.XStreamDSO.SaveRecall.Waveform". Choices are "Byte", "Word", or "Auto".
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.BinarySubFormat.Value = 'Byte'")
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.WaveformDir.Value = %r" % directory)
        # Needed to force update of sequence number?
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.TraceTitle.Value = '__'")
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.TraceTitle.Value = '_'")
        save_filename = directory + "\\C%s_00000.trc" % channel
        self.send("remove(%r)" % save_filename)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.DoSave.ActNow()")
        self.send("rename(%r,%r)" % (save_filename, filename))

    def acquire_waveforms_to_directory(self, channel, directory="D:\\Waveforms"):
        """automatically acquire a series of waveform files
        using auto-save mode
        channel: 1,2,3, or 4
        directory: Pathname on the oscilloscope computer (remote, Windows)
        The waveform filenames will be:
        C1Waveform00000.trc, C1Waveform00001.trc, ..."""
        if not self.exists(directory):
            self.mkdir(directory)
        if not self.exists(directory):
            warning("Failed to create %r" % directory)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveTo.Value = 'File'")
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveSource.Value = 'C%s'" % channel)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.WaveFormat.Value = 'Binary'")
        # BinarySubFormat is not documented in the "Automation Manual"
        # (July 2003) and "Automation Command Reference Manual" Reference
        # (2010), but shown as option in the XStream Browser,
        # under "LeCroy.XStreamDSO.SaveRecall.Waveform". Choices are "Byte", "Word", or "Auto".
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.BinarySubFormat.Value = 'Byte'")
        directory = Windows_pathname(directory)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.WaveformDir.Value = %r" % directory)
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.TraceTitle.Value = 'Waveform'")
        self.waveform_autosave = "Off"  # forces the sequence number to be reset
        self.waveform_autosave = "Wrap"

    Windows_filenames = []
    temp_filenames = []

    from PV_property import PV_property

    acquiring_waveforms = PV_property("acquiring_waveforms", 0)
    auto_acquire = PV_property("auto_acquire", nan)

    trigger_counts_history = value_property("scope.trigger_counts_history", [[], []])
    trace_counts_history = value_property("scope.trace_counts_history", [[], []])
    timing_differences = value_property("scope.timing_differences", [])

    timing_offset = PV_property("timing_offset", nan)
    timing_jitter = PV_property("timing_jitter", nan)
    timing_reset = PV_property("timing_reset", 0)

    def get_waveform_acquisition_channel(self):
        """Which channel to save? 1,2,3, or 4"""
        value = self.query("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveSource.Value")
        value = value.replace("C", "")
        try:
            value = int(value)
        except ValueError:
            value = nan
        return value

    def set_waveform_acquisition_channel(self, value):
        """Which channel to save? 1,2,3, or 4"""
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.SaveSource.Value = 'C%s'" % value)

    waveform_acquisition_channel = property(get_waveform_acquisition_channel,
                                            set_waveform_acquisition_channel)
    trace_acquisition_channel = waveform_acquisition_channel

    def get_waveform_autosave(self):
        """Save a waveform file at each trigger event?
        Return values: 'Off','Wrap','Fill'
        'Wrap': old files overwritten
        'Fill': no files overwritten"""
        value = self.query("LeCroy.XStreamDSO.SaveRecall.Waveform.AutoSave.Value")
        return value

    def set_waveform_autosave(self, value):
        if value:
            value = "Wrap"
        else:
            value = "Off"
        self.send("LeCroy.XStreamDSO.SaveRecall.Waveform.AutoSave.Value = %r" % value)

    waveform_autosave = property(get_waveform_autosave, set_waveform_autosave)

    def exists(self, pathname):
        """Does the file exist on the file system of the oscilloscope computer?"""
        reply = self.query("exists(%r)" % pathname)
        try:
            return eval(reply)
        except Exception:
            return False

    def remove(self, pathname):
        """Remove a file on the file system of the oscilloscope
        computer (remotely)."""
        self.send("remove(%r)" % pathname)

    def rename(self, old_pathname, new_pathname):
        """Rename a file on the file system of the oscilloscope
        computer (remotely)."""
        self.send("rename(%r,%r)" % (old_pathname, new_pathname))

    def migrate_files(self, source_filenames, destination_filenames):
        """Copy each file in the list 'source_files' to the corresponding file
        in 'destination_files', on the file system of the oscilloscope
        computer (remotely)."""
        self.send("migrate_files(%r,%r)" % (source_filenames, destination_filenames))

    @property
    def migration_in_progress(self):
        """Are there files remaining to be copied?"""
        reply = self.query("migration_in_progress")
        try:
            return eval(reply)
        except Exception:
            return False

    @property
    def copied(self):
        """Which files are already copied? List of booleans"""
        reply = self.query("copied")
        try:
            return eval(reply)
        except Exception:
            return []

    @property
    def n_copied(self):
        """How many files are remaining to be copied?"""
        reply = self.query("sum(copied)")
        try:
            return eval(reply)
        except Exception:
            return 0

    def mkdir(self, pathname):
        """Create a directory on the file system of the oscilloscope
        computer (remotely)."""
        self.send("mkdir(%r)" % pathname)

    def rmdir(self, pathname):
        """Remove a directory with all its contents
        on the file system of the oscilloscope computer (remotely)."""
        self.send("rmdir(%r)" % pathname)

    def math_waveform(self, channel):
        """Recorded voltage values in units of volts.
        Channel: 1,2,3, or 4
        Return value: tuple"""
        result = self.query("LeCroy.XStreamDSO.SaveRecall.F%s.Out.Result.DataArray" % channel)
        if result == "":
            return ()
        return eval(result)

    class channel_object(object):
        """For properties of a specific channel"""

        def __init__(self, scope, n):
            """n = 1,2,3, or 4 is the channel number."""
            self.__scope__ = scope
            self.__n__ = n

        def __repr__(self):
            return repr(self.__scope__) + ".channel(" + str(self.__n__) + ")"

        def get_vertical_scale(self):
            return float(self.__scope__.query("LeCroy.XStreamDSO.Acquisition.C%d.VerScale.Value" % self.__n__))

        def set_vertical_scale(self, value):
            self.__scope__.send("LeCroy.XStreamDSO.Acquisition.C%d.VerScale.Value = %s" % (self.__n__, value))

        vertical_scale = property(get_vertical_scale, set_vertical_scale,
                                  doc="Volts/div")

        def get_coupling(self):
            """'DC50','DC1M', 'AC1M' or 'Gnd'"""
            return self.__scope__.query("LeCroy.XStreamDSO.Acquisition.C%d.Coupling.Value" % self.__n__)

        def set_coupling(self, value):
            self.__scope__.send("LeCroy.XStreamDSO.Acquisition.C%d.Coupling.Value = %r" % (self.__n__, value))

        coupling = property(get_coupling, set_coupling)

        def get_waveform(self):
            """Recorded voltage values, as tuple"""
            result = self.__scope__.query("LeCroy.XStreamDSO.Acquisition.C%s.Out.Result.DataArray" % self.__n__)
            if result == "":
                return ()
            return eval(result)

        waveform = property(get_waveform)

        def save_waveform(self, filename):
            """Dump oscilloscope trace as LeCroy binary waveform file (
            recommended extension: .trc)"""
            self.__scope__.save_waveform(self.__n__, filename)

        def acquire_waveforms(self, filenames):
            """Automatically acquire a series of waveform files
            using auto-save mode.
            filenames: list of strings that are absolute pathnames
            e.g. '/net/id14bxf/data/anfinrud_1203/test.trc'"""
            self.__scope__.acquire_waveforms(self.__n__, filenames)

        def start_acquiring_waveforms(self):
            """Undo "acquire_waveforms" """
            self.__scope__.start_acquiring_waveforms(self.__n__)

        def stop_acquiring_waveforms(self):
            """Undo "acquire_waveforms" """
            self.__scope__.stop_acquiring_waveforms()

        def acquire_waveforms_to_directory(self, directory):
            """Automatically acquire a series of waveform files
            using auto-save mode.
            directory: absolute pathname
            e.g. '/net/id14bxf/data/anfinrud_1203/'"""
            self.__scope__.acquire_waveforms_to_directory(self.__n__, directory)

        def get_trigger_mode(self):
            return self.__scope__.trigger_mode

        def set_trigger_mode(self, value):
            self.__scope__.trigger_mode = value

        trigger_mode = property(get_trigger_mode, set_trigger_mode)

        def get_enhance_resolution(self):
            """Noise Filter: 'None','0.5bits','1bits',...,'3bits'"""
            return self.val("LeCroy.XStreamDSO.Acquisition.C%s.EnhanceResType.Value" % self.__n__, "")

        def set_enhance_resolution(self, value):
            self.set_val("LeCroy.XStreamDSO.Acquisition.C%s.EnhanceResType.Value" % self.__n__, value)

        enhance_resolution = property(get_enhance_resolution, set_enhance_resolution)
        noise_filter = enhance_resolution

        def __getattr__(self, name):
            if not (name.startswith("__") and name.endswith("__")):
                return getattr(self.__scope__, name)
            else:
                raise AttributeError("Channel has not attribute %r" % name)

        def __setattr__(self, name, value):
            if not (name.startswith("__") and name.endswith("__")):
                setattr(self.__scope__, name, value)
            else:
                object.__setattr__(self, name, value)

    def channel(self, n):
        return self.channel_object(self, n)

    @property
    def C1(self):
        return self.channel(1)

    @property
    def C2(self):
        return self.channel(2)

    @property
    def C3(self):
        return self.channel(3)

    @property
    def C4(self):
        return self.channel(4)

    ch1 = C1
    ch2 = C2
    ch3 = C3
    ch4 = C4

    def start(self):
        """Clear the accumulated average and restart averaging.
        Also re-enables the trigger in case the scope was stopped."""
        self.sampling_mode = "RealTime"
        self.trigger_mode = "Normal"
        self.clear_sweeps()

    def stop(self):
        """Freezes the averaging by disabling the trigger of the oscilloscope."""
        self.send("LeCroy.XStreamDSO.Acquisition.TriggerMode.Value = 'Stopped'")

    def acquire_sequence(self, n_trigger=1):
        """Record a waveform with a given number of trigger events, using
        "sequence" mode. Does not wait for the acquisition to finish.
        use 'is_acquiring' to check when the acquisition has finished."""
        if n_trigger > 1:
            self.sampling_mode = "Sequence"
            self.n_segments = n_trigger
        else:
            self.sampling_mode = "RealTime"
        self.trigger_mode = "Stop"  # Needed?
        self.clear_sweeps()
        self.trigger_mode = "Normal"  # Needed?

    def get_is_acquiring(self):
        """Has 'acquire_sequence' finished?"""
        return self.trigger_mode == "Single"

    is_acquiring = property(get_is_acquiring)

    def trigger_single(self):
        """Trigger the oscilloscope in single shot mode.
        Also re-enables the trigger in case the scope was stopped."""
        self.clear_sweeps()
        self.trigger_mode = "Single"

    def get_trigger_mode(self):
        """'Stopped','Auto','Normal', or 'Single'"""
        return self.query("LeCroy.XStreamDSO.Acquisition.TriggerMode.Value")

    def set_trigger_mode(self, mode):
        self.send("LeCroy.XStreamDSO.Acquisition.TriggerMode.Value = %r" % mode)

    trigger_mode = property(get_trigger_mode, set_trigger_mode)

    def clear_sweeps(self):
        """Reset average count"""
        self.query("LeCroy.XStreamDSO.ClearSweeps.ActNow()")

    reset_average = clear_sweeps
    reset_statistics = clear_sweeps

    def get_sampling_mode(self):
        """'WStream', 'RealTime' or 'Sequence'"""
        return self.query("LeCroy.XStreamDSO.Acquisition.Horizontal.SampleMode.Value")

    def set_sampling_mode(self, mode):
        self.send("LeCroy.XStreamDSO.Acquisition.Horizontal.SampleMode.Value = %r" % mode)

    sampling_mode = property(get_sampling_mode, set_sampling_mode)

    def get_number_of_segments(self):
        """Number of trigger events to capture. Only valid when using
        'Sequence' sampling mode. Minimum 2"""
        try:
            return int(self.query("LeCroy.XStreamDSO.Acquisition.Horizontal.NumSegments.Value"))
        except (ValueError, TypeError):
            return 0

    def set_number_of_segments(self, n_segments):
        self.send("LeCroy.XStreamDSO.Acquisition.Horizontal.NumSegments.Value = %d" % n_segments)

    number_of_segments = property(get_number_of_segments, set_number_of_segments)
    n_segments = number_of_segments

    sequence_timeout = value_property("LeCroy.XStreamDSO.Acquisition.Horizontal.SequenceTimeout.Value")
    sequence_timeout_enabled = value_property("LeCroy.XStreamDSO.Acquisition.Horizontal.SequenceTimeoutEnable.Value", False)

    sampling_rate = value_property("LeCroy.XStreamDSO.Acquisition.Horizontal.SampleRate.Value")
    time_scale = value_property("LeCroy.XStreamDSO.Acquisition.Horizontal.HorScale.Value")
    time_range = function("time_scale", "x*10", "x/10.")
    trigger_delay = value_property("LeCroy.XStreamDSO.Acquisition.Horizontal.HorOffset.Value")
    time_offset = trigger_delay  # alias

    def val(self, query_string, default_value=nan):
        """Performs a query and returns the result as a number"""
        value = self.query(query_string)
        dtype = type(default_value)
        if dtype != str:
            try:
                value = dtype(eval(value))
            except Exception:
                value = default_value
        return value

    def set_val(self, query_string, value):
        """Change a setting"""
        self.send("%s = %r" % (query_string, value))

    @property
    def software_version(self):
        return self.id.split(",")[-1]

    @property
    def id(self):
        return self.query("LeCroy.XStreamDSO.InstrumentID.Value")

    filenames = value_property("scope.filenames", [])
    times = value_property("scope.times", [])
    trace_filenames = value_property("scope.trace_filenames", {})

    def trace_filename(self, i):
        reply = self.query("scope.trace_filename(%r)" % i)
        return reply

    trace_acquisition_running = PV_property("trace_acquisition_running", nan)

    trace_count_synchronized = PV_property("trace_count_synchronized", nan)
    auto_synchronize = PV_property("auto_synchronize", nan)

    def trace_count_synchronize(self):
        self.send("scope.trace_count_synchronize()")

    trace_count = PV_property("trace_count", 0)
    timing_system_trigger_count = PV_property("timing_system_trigger_count", 0)
    trace_count_offset = PV_property("trace_count_offset", 0)

    emptying_trace_directory = PV_property("emptying_trace_directory", 0)
    trace_directory_size = PV_property("trace_directory_size", 0)

    timing_system_trigger_enabled = value_property("scope.timing_system_trigger_enabled", False)

    enabled_channels = value_property("scope.enabled_channels", [])
    trace_source = value_property("scope.trace_source", "")
    trace_sources = PV_property("trace_sources", [])

    server_version = value_property("version()", "")

    def save_setup(self, name):
        """Store setup to setup file in Lauecollect directory"""
        self.setup_name = name
        self.setup_save = True

    def recall_setup(self, name):
        """Load setup from setup file in Lauecollect directory"""
        self.setup_name = name
        self.setup_recall = True

    setup_dirname = value_property("LeCroy.XStreamDSO.SaveRecall.Setup.PanelDir.Value", "")
    setup_basename = value_property("LeCroy.XStreamDSO.SaveRecall.Setup.PanelFilename.Value", "")

    def get_setup_filename(self):
        filename = self.setup_dirname + "\\" + self.setup_basename
        from normpath import normpath
        filename = normpath(filename)
        return filename

    def set_setup_filename(self, filename):
        from os.path import dirname, basename
        directory, file = dirname(filename), basename(filename)
        directory = Windows_pathname(directory)
        self.setup_dirname = directory
        self.setup_basename = file

    setup_filename = property(get_setup_filename, set_setup_filename)

    @property
    def local_setup_dirname(self):
        from module_dir import module_dir
        return module_dir(self) + "/lecroy_scope/" + self.name

    def local_setup_filename(self, name):
        return self.local_setup_dirname + "/" + name + ".lss"

    setup = PV_property("SETUP", "")
    setups = PV_property("SETUPS", [])
    setup_choices = setups
    setup_name = PV_property("SETUP_NAME", "")
    setup_filename = PV_property("SETUP_FILENAME", "")

    setup_save = PV_property("SETUP_SAVE", 0)
    setup_recall = PV_property("SETUP_RECALL", 0)

    monitoring_trace_count = value_property("scope.monitoring_trace_count", False)
    monitoring_trace_count_allowed = value_property("scope.monitoring_trace_count_allowed", False)
    monitoring_trace_count_2 = value_property("scope.monitoring_trace_count_2", False)
    monitoring_trig_count = value_property("scope.monitoring_trig_count", False)
    monitoring_timing = value_property("scope.monitoring_timing", False)


def Windows_pathname_(pathname):
    """Translate between UNIX-style to Windows-style pathnames, following
    Universal Naming Convention.
    E.g. "/net/id14bxf/data" to "\\\\id14bxf\\data"""
    from os.path import dirname, basename
    directory, file = dirname(pathname), basename(pathname)
    if directory not in Windows_pathname_cache:
        Windows_pathname_cache[directory] = Windows_pathname(directory)
    Windows_dir = Windows_pathname_cache[directory]
    Win_pathname = Windows_dir + "\\" + file
    return Win_pathname


Windows_pathname_cache = {}


def Windows_pathname(pathname):
    """Translate between UNIX-style to Windows-style pathnames, following
    Universal Naming Convention.
    E.g. "/net/id14bxf/data" to "\\\\id14bxf\\data"""
    if pathname == "":
        return pathname
    if not pathname[1:2] == ":":
        # Resolve symbolic links. E.g. "/data" to "/net/id14bxf/data"
        from os.path import realpath
        pathname = realpath(pathname)
    # Mac OS X: mount point "/Volumes/share" does not reveal server name. 
    if pathname.startswith("/Mirror/"):
        pathname = pathname.replace("/Mirror/", "//")
    if pathname.startswith("/Volumes/data"):
        pathname = pathname.replace("/Volumes/data", "/net/id14bxf/data")
    if pathname.startswith("/Volumes/C"):
        pathname = pathname.replace("/Volumes/C", "/net/femto/C")
    # Convert separators from UNIX style to Windows style.
    # E.g. "//id14bxf/data/anfinrud_1106" to "\\id14bxf\data\anfinrud_1106" 
    pathname = pathname.replace("/", "\\")
    # Try to expand a Windows drive letter to a UNC name.
    # E.g. "J:/anfinrud_1106" to "//id14bxf/data/anfinrud_1106"
    try:
        import win32wnet
        pathname = win32wnet.WNetGetUniversalName(pathname)
    except Exception:
        pass
    # Convert from UNIX to Windows style.
    # E.g. "/net/id14bxf/data/anfinrud_1106" to "//id14bxf/data/anfinrud_1106"
    if pathname.startswith("\\net\\"):
        parts = pathname.split("\\")
        if len(parts) >= 4:
            # server = parts[2]
            # share = parts[3]
            pathname = "\\\\" + pathname[5:]
    return pathname


def to_repr(x, n_chars=80):
    """limit string length using ellipses (...)"""
    s = repr(x)
    if len(s) > n_chars:
        s = s[0:n_chars - 10 - 3] + "..." + s[-10:]
    return s


if __name__ == "__main__":  # for testing
    import logging  # for debugging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # from time import time # for performance testing
    # import CA
    # from CA import caget,caput,camonitor,cainfo # for debugging

    name = "BioCARS.xray_scope"
    # name = "BioCARS.laser_scope"
    # name = "BioCARS.diag_scope"
    # name = "LaserLab.laser_scope"

    self = lecroy_scope(name)  # for debugging
    print("self.query(b'1+1')")
    print("self.query(b'scope')")
