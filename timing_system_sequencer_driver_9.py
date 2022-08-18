"""
Executing hardware timed configuration changes on the FPGA timing system
in "Piano Player" mode.

Author: Friedrich Schotte
Date created: 2015-05-01
Date last modified: 2022-08-17
Revision comment: Omitting new line terminator for sequence counts
"""
__version__ = "9.2"
__generator_version__ = "8.7.1"

import logging
from traceback import format_exc

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property
from reference import reference
from monitored_value_property import monitored_value_property
from retry_setattr import retry_setattr
from thread_property_2 import thread_property
from db_property import db_property
from numpy import nan
from timing_system_sequencer_driver_property import timing_system_sequencer_driver_property as sequencer_property


class queue_file_content_property(monitored_property):
    def __init__(self, queue_property_name):
        """property_name: e.g. 'current_queue_repeat_count'"""
        self.queue_property_name = queue_property_name

        for queue_type in self.queue_types:
            if self.queue_property_name.startswith(queue_type):
                self.queue_type = queue_type
                self.suffix = self.queue_property_name[len(queue_type):]
                break
        else:
            logging.error(f"{self.queue_property_name!r} does not start with one of {self.queue_types}")
            self.queue_type = self.queue_property_name
            self.suffix = ""

        super().__init__(
            inputs=self.queue_property_inputs,
            calculate=self.queue_property_calculate,
            fset=self.queue_property_set,
        )

    queue_types = ["queue1", "queue2", "queue", "current_queue"]

    def __repr__(self):
        return f"{self.class_name}({self.queue_property_name!r})"

    def queue_property_inputs(self, instance):
        if self.queue_type == "current_queue":
            input_references = [reference(instance, "current_queue_name")]
            for queue_name in instance.queue_names:
                input_references.append(reference(instance.fs, f"{queue_name}{self.suffix}"))
        else:
            input_references = [reference(instance.fs, f"{self.queue_type}{self.suffix}")]
        return input_references

    def queue_property_calculate(self, instance, *args):
        if self.queue_type == "current_queue":
            current_queue_name = args[0]
            str_values = args[1:]
            if current_queue_name in instance.queue_names:
                index = instance.queue_names.index(current_queue_name)
                str_value = str_values[index]
            else:
                if current_queue_name:
                    logging.error(f"{current_queue_name!r} not in {instance.queue_names}")
                str_value = ""
        else:
            str_value = args[0]

        return self.value_from_str(str_value)

    def queue_property_set(self, instance, count):
        str_value = self.str_from_value(count)
        if self.queue_type == "current_queue":
            queue_name = instance.current_queue_name
        else:
            queue_name = self.queue_type
        name = f"{queue_name}{self.suffix}"
        # logging.debug(f"{instance}.fs.{name} = {str_value!r})")
        retry_setattr(instance.fs, name, str_value)

    def value_from_str(self, str_value):
        return str_value

    def str_from_value(self, value):
        return value


class queue_property(queue_file_content_property):
    def value_from_str(self, str_value):
        from numpy import nan
        if str_value:
            try:
                value = int(str_value)
            except (ValueError, TypeError):
                value = nan
        else:
            value = nan
        return value

    def str_from_value(self, value):
        from numpy import isnan, rint
        str_value = str(int(rint(value))) if not isnan(value) else ""
        str_value = str_value.ljust(20)  # leave room for growth
        return str_value


class queue_content_property(queue_file_content_property):
    def value_from_str(self, file_content):
        IDs = file_content.strip("\n").split("\n") if len(file_content) > 0 else []
        return IDs

    def str_from_value(self, IDs):
        file_content = "\n".join(IDs) + ("\n" if len(IDs) > 0 else "")
        return file_content


@cached_function()
def timing_system_sequencer_driver(timing_system):
    return Timing_System_Sequencer_Driver(timing_system)


class Timing_System_Sequencer_Driver(object):
    def __init__(self, timing_system):
        self.timing_system = timing_system

    timing_system = None

    def __repr__(self):
        return f"{self.timing_system!r}.sequencer"

    @property
    def name(self):
        return self.timing_system.domain_name

    @property
    def db_name(self):
        return self.timing_system.db_name

    count = 0
    parameters = [
        "delay",
        "laser_on",
        "waitt",
        "npulses",
        "burst_waitt",
        "burst_delay",
        "xosct.on",
        "losct.on",
        "lcam.on",
        "s1.on",
        "ms.on",
        "xdet.on",
        "trans.on",
        "trans.bit_code",
        "s3.on",
        "image_number",
        "pass_number",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",
        # Calibration constants and parameters
        "hlc_div",
        "hsc.delay",
        "hsc.delay.offset",
        "ms.offset",
        "ms.pulse_length",
        "nsf.offset",
        "nsq.offset",
        "xdet.offset",
        "trans.offset",
        "trans.pulse_length",
    ]

    def get_default(self, name):
        """Get default value for parameter
        name: 'delay','laser_on'... """
        from numpy import nan

        if name == "acquiring":
            value = False
        elif name == "image_number":
            value = nan
        elif name == "pass_number":
            value = 0.0  # for backward compatibility with version 1.0.5
        else:
            names = self.alt_names(name)
            for n in names:
                try:
                    value = eval(f"self.timing_system.{n}")
                except AttributeError:
                    continue
                if hasattr(value, "value"):
                    continue
                break
            else:
                alt_names = ",".join(repr(n) for n in names[1:])
                raise AttributeError(f"{self.timing_system} has no attribute {name!r} (nor {alt_names})")
        return value

    def set_default(self, name, value, update=True):
        """Set default value  for parameter
        name: 'delay','laser_on'... """
        names = self.alt_names(name)
        for n in names:
            try:
                eval(f"self.timing_system.{n}")
            except AttributeError:
                continue
            try:
                exec(f"self.timing_system.{n} = {value!r}")
            except AttributeError:
                continue
            break
        else:
            alt_names = ",".join(repr(n) for n in names[1:])
            raise AttributeError(f"self.timing_system has no attribute {name!r} (nor {alt_names})")

        if update:
            self.set_default_sequences()

    def alt_names(self, name):
        names = [name]
        alt_name = name.replace("_on", ".on")
        if alt_name in self.parameters:
            names.append(alt_name)
        if not name.endswith("on"):
            names.append(name + "_on")
        names += [n + ".value" for n in names]
        return names

    def __getattr__(self, name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute was not found the usual ways.
        alt_name = name.replace("_", ".", 1)  # ch1_trig_count -> ch1.trig_count
        if name in self.parameters:
            return self.current_value(name)
        elif alt_name in self.parameters:
            return self.current_value(alt_name)
        elif hasattr(self.timing_system, name):
            attr = getattr(self.timing_system, name)
            if hasattr(attr, "value"):
                attr = attr.value
            return attr
        elif self.hasattr(self.timing_system, alt_name):
            attr = eval(f"self.timing_system.{alt_name}")
            if hasattr(attr, "value"):
                attr = attr.value
            return attr
        else:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        alt_name = name.replace("_", ".")  # hsc_delay > hsc.delay
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        elif name in self.__class__.__dict__:
            object.__setattr__(self, name, value)
        elif name == "timing_system":
            object.__setattr__(self, name, value)
        elif name in self.parameters:
            self.set_default(name, value)
        elif alt_name in self.parameters:
            self.set_default(alt_name, value)
        elif hasattr(self.timing_system, name):
            attr = getattr(self.timing_system, name)
            if hasattr(attr, "value"):
                attr.value = value
            else:
                setattr(self.timing_system, name, value)
        elif self.hasattr(self.timing_system, alt_name):
            attr = eval(f"self.timing_system.{alt_name}")
            if hasattr(attr, "value"):
                attr.value = value
            else:
                exec(f"self.timing_system.{alt_name} = {value!r}")
        else:
            object.__setattr__(self, name, value)

    @staticmethod
    def hasattr(obj, name): # noqa
        """name: e.g. 'hsc.delay'"""
        try:
            eval(f"obj.{name}")
            return True
        except AttributeError:
            return False
        except SyntaxError:
            return False

    ip_address = alias_property("timing_system.ip_address")

    sequence_dir = "/tmp/sequencer_fs"
    queue_name = "queue"
    current_queue_names = ['queue1', 'queue2']
    queue_filename = sequence_dir + "/" + queue_name
    queue_names = "queue1", "queue2", "queue"

    def get_queue_content(self, queue_name):
        """Packet IDs as list of strings
        queue_name: "queue" for data acquisition; "queue1" or "queue2" for idle mode
        """
        file_content = getattr(self.fs, queue_name) if queue_name else ""
        IDs = file_content.strip("\n").split("\n") if len(file_content) > 0 else []
        return IDs

    def set_queue_content(self, queue_name, IDs):
        """Packet IDs as list of strings
        queue_name: "queue" (default) for data acquisition;
          "queue1" or "queue2" for idle mode
        IDs: Packet IDs as list of strings
        """
        if queue_name:
            file_content = "\n".join(IDs) + ("\n" if len(IDs) > 0 else "")
            setattr(self.fs, queue_name, file_content)

            # First-time initialization
            if len(getattr(self.fs, f"{queue_name}_sequence_count")) < 20:
                setattr(self.fs, f"{queue_name}_sequence_count", f"{0:<20d}")
            if len(getattr(self.fs, f"{queue_name}_repeat_count")) < 20:
                setattr(self.fs, f"{queue_name}_repeat_count", f"{0:<20d}")
            if len(getattr(self.fs, f"{queue_name}_max_repeat_count")) < 20:
                setattr(self.fs, f"{queue_name}_max_repeat_count", f"{1:<20d}")

    @monitored_property
    def queue_active(self, current_queue_name):
        """Is the data acquisition queue actively being executed?"""
        return current_queue_name == self.queue_name

    @queue_active.setter
    def queue_active(self, value):
        if bool(value) is True:
            self.next_queue_name = self.queue_name
        if bool(value) is False:
            # Leave acquisition mode at the next sequence_count (fast).
            self.next_queue_sequence_count = -1
            self.next_queue_name = self.default_queue_name

    @monitored_property
    def queue_length(self, queue):
        """How many sequences are left in the acquisition queue?"""
        return len(queue)

    @queue_length.setter
    def queue_length(self, value):
        if value == 0:
            self.queue = []

    @monitored_property
    def current_queue_length(self, current_queue):
        """How many sequences are left in the idle or acquisition queue?"""
        return len(current_queue)

    @current_queue_length.setter
    def current_queue_length(self, value):
        if value == 0:
            self.current_queue = []

    @property
    def generator(self):
        """Sequence generator Python module name"""
        return self.current_sequence_property("generator", "")

    @property
    def generator_version(self):
        """Sequence generator Python module version number"""
        return self.current_sequence_property("generator_version", "")

    def current_sequence_property(self, name, default_value=None, dtype=None):
        """
        name: e.g. 'mode','delay','laser_on','count'
        dtype: data type
        """
        return self.property_value(self.descriptor, name, default_value, dtype)

    def current_value(self, name):
        """Get the value of a parameter from the currently executing sequence
        name: e.g. 'mode','delay','laser_on','count'
        dtype: data type
        """
        if name in ["pass_number", "image_number"]:
            value = getattr(self.timing_system.registers, name)
            if hasattr(value, "value"):
                value = value.value
        else:
            value = self.property_value(self.descriptor, name)
        return value

    def property_value(self, descriptor, name, default_value=None, dtype=None):
        """Extract a value from a sequence descriptor
        descriptor: comma separated list
        e.g. 'mode=Stepping-48,delay=0.0316,laser_on=True,count=6'
        name: e.g. 'mode','delay','laser_on','count'
        """
        if default_value is None and dtype is not None:
            default_value = dtype()

        def default():
            if default_value is None:
                return self.get_default(name)
            else:
                return default_value

        value = None
        for record in descriptor.split(","):
            parts = record.split("=")
            key = parts[0]
            if key != name:
                continue
            if len(parts) < 2:
                value = default()
            else:
                value = parts[1]
                # noinspection PyBroadException
                try:
                    value = eval(value)
                    if dtype is not None:
                        value = dtype(value)
                except Exception:
                    value = default()
        if value is None:
            value = default()
        return value

    default_phase_matching_period = alias_property("timing_system.clock.phase_matching_period")

    @monitored_property
    def running(
            self,
            current_sequence_length,
            interrupt_enabled,
            interrupt_handler_enabled,
    ):
        if current_sequence_length is None:
            logging.warning(f"current_sequence_length={current_sequence_length}")
        if interrupt_enabled is None:
            logging.warning(f"interrupt_enabled={interrupt_enabled}")
        if interrupt_handler_enabled is None:
            logging.warning(f"interrupt_handler_enabled={interrupt_handler_enabled}")

        running = all([
            current_sequence_length > 0,
            interrupt_enabled == 1,
            interrupt_handler_enabled == 1,
        ])

        # if not running:
        #     logging.debug(f"current_sequence_length={current_sequence_length}")
        #     logging.debug(f"interrupt_enabled={interrupt_enabled}")
        #     logging.debug(f"interrupt_handler_enabled={interrupt_handler_enabled}")
        #     logging.debug(f"running={running}")

        return running

    @running.setter
    def running(self, value):
        if bool(value) is True:
            self.update()
            self.interrupt_handler_enabled = 1
        if bool(value) is False:
            self.default_queue_name = ""
            self.next_queue_name = ""

    timing_system_acquiring = alias_property("timing_system.registers.acquiring.count")

    @monitored_property
    def acquiring(self, timing_system_acquiring):
        return timing_system_acquiring != 0

    @acquiring.setter
    def acquiring(self, acquiring):
        if not acquiring:
            self.update()

    acquisition_start_time = monitored_value_property(nan)

    def acquisition_start_time_setup(self):
        reference(self, "next_queue_name").monitors.add(self.acquisition_start_time_handler)
        reference(self, "current_queue_name").monitors.add(self.acquisition_start_time_handler)
        reference(self, "current_queue_repeat_count").monitors.add(self.acquisition_start_time_handler)

    @property
    def acquisition_start_time_handler(self):
        from handler import handler
        return handler(self.handle_acquisition_start_time)

    def handle_acquisition_start_time(self, event):
        if event.reference.attribute_name == "next_queue_name":
            if event.value == self.queue_name:
                self.acquisition_start_time = \
                    self.current_queue_repeat_count_last_changed + self.current_queue_duration

        if event.reference.attribute_name == "current_queue_name":
            if event.value == self.queue_name:
                self.acquisition_start_time = event.time

        if event.reference.attribute_name == "current_queue_repeat_count":
            self.current_queue_repeat_count_last_changed = event.time

    @monitored_property
    def acquisition_end_time(self, acquisition_start_time, queue_duration):
        return acquisition_start_time + queue_duration

    current_queue_repeat_count_last_changed = monitored_value_property(nan)

    @monitored_property
    def current_queue_duration(self, current_queue_length, composer_period, T_base):
        T = current_queue_length * composer_period * T_base
        return T

    @monitored_property
    def queue_duration(self, queue_length, composer_period, T_base, queue_max_repeat_count):
        T = queue_length * composer_period * T_base * queue_max_repeat_count
        return T

    composer_period = alias_property("composer.period")

    T_base = alias_property("timing_system.clock.hsct")

    def set_queue_sequences(self,
                            sequences,
                            queue_name=None,
                            default_queue_name=None,
                            next_queue_name=None,
                            ):
        """Queue a timing sequence for execution.
        sequences: list of sequence objects
        queue_name: "queue" (default) for data acquisition;
          "queue1" or "queue2" for idle mode
        default_queue_name: make this queue the new default when ready
        next_queue_name: switch to this queue when ready
        """
        if queue_name is None:
            queue_name = self.queue_name
        self.queue_sequences[queue_name] = sequences
        if default_queue_name is not None:
            self.default_queue_name_requested = default_queue_name
        if next_queue_name is not None:
            self.next_queue_name_requested = next_queue_name
        self.update_queues = True # noqa

    queue_sequences = {}
    default_queue_name_requested = None
    next_queue_name_requested = None

    @thread_property
    def update_queues(self):
        logging.debug(f"queue_sequences {list(self.queue_sequences)!r:.200}")
        logging.debug(f"default_queue_name_requested = {self.default_queue_name_requested!r}")
        logging.debug(f"next_queue_name_requested = {self.next_queue_name_requested!r}")

        while len(self.queue_sequences) > 0:
            if self.update_queues_cancelled:
                break
            queue_name = next(iter(self.queue_sequences))
            sequences = self.queue_sequences.pop(queue_name)

            sequence_ids = [seq.id for seq in sequences]

            logging.debug(f"Updating {queue_name!r} to {sequence_ids!r:.200}")
            self.set_queue_content(queue_name, sequence_ids)

            filenames = []
            file_contents = []

            uploaded_files = self.uploaded_files

            for i, sequence in enumerate(sequences):
                if self.update_queues_cancelled:
                    break
                filename = self.sequence_dir + "/" + sequence.id
                if filename not in filenames:
                    if filename not in uploaded_files:
                        if sequence.is_cached:
                            filenames += [filename]
                            file_contents += [sequence.data]
            if self.update_queues_cancelled:
                break

            self.put_files(filenames, file_contents)
            for filename in filenames:
                if filename not in uploaded_files:
                    uploaded_files += [filename]

            for i, sequence in enumerate(sequences):
                if self.update_queues_cancelled:
                    break
                filename = self.sequence_dir + "/" + sequence.id
                if filename not in uploaded_files:
                    if not sequence.is_cached:
                        logging.info(f"Generating packets: {i+1}/{len(sequences)}")
                    file_content = sequence.data
                    logging.debug(f"Uploading {sequence.id!r}")
                    self.put_file(filename, file_content)
                    uploaded_files += [filename]

        # Switch queue when ready
        if self.default_queue_name_requested is not None:
            logging.debug(f"Setting default queue to {self.default_queue_name_requested!r}")
            self.default_queue_name = self.default_queue_name_requested
            self.default_queue_name_requested = None
        if self.next_queue_name_requested is not None:
            logging.debug(f"Requesting switch to {self.next_queue_name_requested!r}")
            self.next_queue_name = self.next_queue_name_requested
            self.next_queue_name_requested = None

        self.remove_unused_sequences()

    @staticmethod
    def unique_sequences(sequences):
        unique_sequences = []
        IDs = []
        for sequence in sequences:
            ID = sequence.id
            if ID not in IDs:
                unique_sequences.append(sequence)
                IDs.append(ID)
        return unique_sequences

    def wait_for_queue_ready(self, queue_name):
        from time import sleep
        if not self.get_queue_ready(queue_name):
            logging.info(f"{queue_name!r} not ready")
            while not self.get_queue_ready(queue_name):
                sleep(0.5)
            logging.info(f"{queue_name!r} ready")

    @property
    def queue_ready(self):
        return self.get_queue_ready(self.queue_name)

    @property
    def queue_files_uploaded(self):
        return self.get_queue_files_uploaded(self.queue_name)

    def get_queue_ready(self, queue_name):
        """Are there a sufficient number of files uploaded to start executing
        this queue?"""
        uploaded_count = self.get_queue_uploaded_file_count(queue_name)
        count = self.get_queue_file_count(queue_name)
        ready = uploaded_count >= count or uploaded_count > 2
        return ready

    def get_queue_file_count(self, queue_name):
        IDs = list(set(self.get_queue_content(queue_name)))
        count = len(IDs)
        return count

    def get_queue_uploaded_file_count(self, queue_name):
        IDs = list(set(self.get_queue_content(queue_name)))
        filenames = [self.sequence_dir + "/" + ID for ID in IDs]
        uploaded_files = self.uploaded_files
        count = sum([filename in uploaded_files for filename in filenames])
        return count

    def get_queue_files_uploaded(self, queue_name):
        """Are there a sufficient number of files uploaded to start executing
        this queue?"""
        IDs = self.get_queue_content(queue_name)
        filenames = [self.sequence_dir + "/" + ID for ID in IDs]
        uploaded_files = self.uploaded_files
        uploaded = all([filename in uploaded_files for filename in filenames])
        return uploaded

    def set_default_sequences(self):
        """Define what is executed when the sequencer queue is empty"""
        sequences = self.Sequences()[:]
        self.configured = True
        queue_name = "queue1" if self.current_queue_name != "queue1" else "queue2"
        self.set_queue_sequences(
            sequences,
            queue_name,
            default_queue_name=queue_name,
            next_queue_name=queue_name,
        )

    def Sequence(self, delay=None, **kwargs):
        return self.composer.Sequence(delay=delay, **kwargs)

    def Sequences(self, delay=None, sequences=None, **kwargs):
        return self.composer.Sequences(delay=delay, sequences=sequences, **kwargs)

    @property
    def fs(self):
        from timing_system_sequencer_fs_driver_2 import timing_system_sequencer_fs_driver
        return timing_system_sequencer_fs_driver(self.timing_system)

    @property
    def composer(self):
        return self.timing_system.composer

    @property
    def sequencer(self):
        return self

    nom_buffer_size = db_property("buffer_size", 256 * 1024)

    inton = alias_property("timing_system.registers.inton.count")
    inton_sync = alias_property("timing_system.registers.inton_sync.count")
    IPIRE = alias_property("timing_system.registers.IPIRE.count")
    DEVICE_GIE = alias_property("timing_system.registers.DEVICE_GIE.count")
    IPIER = alias_property("timing_system.registers.IPIER.count")

    @monitored_property
    def configured(
            self,
            inton,
            IPIRE,
            DEVICE_GIE,
            IPIER,
            buffer_size,
            nom_buffer_size,
            phase_matching_period,
            default_phase_matching_period,
    ):
        return all([
            inton == 1,
            IPIRE == 1,
            DEVICE_GIE == 1,
            IPIER == 1,
            buffer_size == nom_buffer_size,
            phase_matching_period == default_phase_matching_period,
        ])

    @configured.setter
    def configured(self, value):
        """Configure the FPGA for 'Player Piano' mode at 1 kHz."""
        if value:
            # self.inton = 1
            self.IPIRE = 1
            self.DEVICE_GIE = 1
            self.IPIER = 1
            self.buffer_size = self.nom_buffer_size

    @monitored_property
    def interrupt_enabled(self, inton_sync):
        """Is the interrupt generator enabled?"""
        return inton_sync == 1

    @interrupt_enabled.setter
    def interrupt_enabled(self, value):
        if bool(value) is True:
            self.inton = 1
        if bool(value) is False:
            self.inton_sync = 0
            self.inton = 0

    @property
    def prefix(self):
        return f"{self.timing_system.prefix.strip('.')}.sequencer"

    current_queue_name = sequencer_property(name="queue_name", dtype=str)
    next_queue_name = sequencer_property(dtype=str)
    next_queue_sequence_count = sequencer_property(dtype=int)
    default_queue_name = sequencer_property(dtype=str)
    current_sequence_length = sequencer_property(dtype=int)
    current_sequence = sequencer_property(dtype=str)

    sequence_interrupt_count = sequencer_property(dtype=int)

    buffer_size = sequencer_property(dtype=int)
    phase_matching_period = sequencer_property(dtype=int)

    interrupt_handler_enabled = sequencer_property(dtype=int)
    reset = sequencer_property(dtype=int)

    version = sequencer_property(dtype=str)
    debug_level = sequencer_property(dtype=int)

    descriptor = sequencer_property(dtype=str)

    queue1 = queue_content_property("queue1")
    queue1_sequence_count = queue_property("queue1_sequence_count")
    queue1_repeat_count = queue_property("queue1_repeat_count")
    queue1_max_repeat_count = queue_property("queue1_max_repeat_count")

    queue2 = queue_content_property("queue2")
    queue2_sequence_count = queue_property("queue2_sequence_count")
    queue2_repeat_count = queue_property("queue2_repeat_count")
    queue2_max_repeat_count = queue_property("queue2_max_repeat_count")

    current_queue = queue_content_property("current_queue")
    current_queue_sequence_count = queue_property("current_queue_sequence_count")
    current_queue_repeat_count = queue_property("current_queue_repeat_count")
    current_queue_max_repeat_count = queue_property("current_queue_max_repeat_count")

    queue = queue_content_property("queue")
    queue_sequence_count = queue_property("queue_sequence_count")
    queue_repeat_count = queue_property("queue_repeat_count")
    queue_max_repeat_count = queue_property("queue_max_repeat_count")

    @property
    def uploaded_files(self):
        """Full pathnames of files on the timing system's file system"""
        return self.files(self.sequence_dir + "/*")

    @property
    def sequencer_fs_files_old(self):
        """Full pathnames of files on the timing system's file system"""
        from timing_system_file_client import wget
        file_list = wget("//" + self.ip_address + self.sequence_dir).decode("utf-8")
        files = file_list.strip("\n").split("\n") if len(file_list) > 0 else []
        return files

    @sequencer_fs_files_old.setter
    def sequencer_fs_files_old(self, files_remaining):
        files = self.sequencer_fs_files_old
        files_to_remove = [f for f in files if f not in files_remaining]
        # logging.debug(f"files to remove: {files_to_remove}")
        for f in files_to_remove:
            self.remove(self.sequence_dir + "/" + f)

    @monitored_property
    def sequencer_fs_files(self, fs_file_list):
        """Full pathnames of files on the timing system's file system"""
        files = fs_file_list.strip("\n").split("\n") if len(fs_file_list) > 0 else []
        return files

    @sequencer_fs_files.setter
    def sequencer_fs_files(self, files_remaining):
        files = self.sequencer_fs_files
        files_to_remove = [f for f in files if f not in files_remaining]
        # logging.debug(f"files to remove: {files_to_remove}")
        for f in files_to_remove:
            self.remove(self.sequence_dir + "/" + f)

    fs_file_list = sequencer_property(name="fs.", dtype=str)

    def files(self, pattern):
        """List of filenames on the timing system's file system
        pattern: e.g. '/tmp/sequence-*.bin' """
        # Work-around for buffer overflow in wildcard expansion
        # on server side (if directory contains 5520 entries).
        if pattern.endswith("/*"):
            directory = pattern[:-2]
            from timing_system_file_client import wget
            file_list = wget("//" + self.ip_address + directory).decode("utf-8")
            files = file_list.strip("\n").split("\n") if len(file_list) > 0 else []
            files = [directory + "/" + f for f in files]
        else:
            from timing_system_file_client import wdir
            files = wdir("//" + self.ip_address + pattern)
        return files

    def file(self, filename):
        """The content of a file on the timing system's file system
        filename: e.g. '/proc/sys/dev/sequencer/interrupt_enabled' """
        from timing_system_file_client import wget
        if filename:
            content = wget("//" + self.ip_address + filename)
            # logging.debug(f"{filename}: {content!r:.20}...")
        else:
            content = ""
        return content

    def remove(self, filename):
        """Delete a file from the timing system's file system
        filename: e.g. '/tmp/sequence/cache' """
        logging.debug(f"Removing {filename!r}")
        from timing_system_file_client import wdel
        wdel(self.ip_address + filename)

    def put_file(self, filename, content):
        """Put file to the file system if the timing system"""
        from timing_system_file_client import wput, wdel
        if len(content) > 0:
            # logging.debug(f"Transferring {len(content)} bytes of data to timing system")
            wput(content, self.ip_address + filename)
        else:
            wdel(self.ip_address + filename)

    def put_files(self, filenames, contents):
        """Group transfer of several files to the file system if the timing
        system"""
        if len(filenames) > 0:
            s = f"Transferring {len(filenames)} files:\n"
            for i in range(0, min(len(filenames), 2)):
                s += f" {filenames[i]}: {len(contents[i])} bytes\n"
            from time import time
            n = sum([len(content) for content in contents])
            t0 = time()
            logging.debug(f"Transferring {n} bytes of data to timing system")
            for (filename, content) in zip(filenames, contents):
                self.put_file(filename, content)
            dt = time() - t0
            logging.debug(f"Transferred {n} bytes in {dt:.3f} s ({float(n) / dt:.0f} bytes/s)")

    def telnet(self, command):
        """Execute a system command on the timing system's CPU and return
        the result"""
        from telnet import telnet
        return telnet(self.ip_address, command)

    cache_enabled = db_property("cache_data", True)

    def cache_set(self, key, data):
        """Temporarily store binary data for fast retrieval
        key: string"""
        from os.path import exists, dirname
        from os import makedirs
        for filename in self.cache_filenames(key):
            if not exists(dirname(filename)):
                makedirs(dirname(filename))
            try:
                open(filename, "wb").write(data)
                break
            except OSError:
                pass

    def cache_get(self, key):
        """Retrieve temporarily stored binary data
        key: string"""
        data = ""
        for filename in self.cache_filenames(key):
            try:
                data = open(filename, "rb").read()
                break
            except OSError:
                pass
        return data

    def cache_clear(self):
        """Erase temporarily stored binary data on the local drive"""
        from shutil import rmtree
        try:
            rmtree(self.cache_directory_name)
        except OSError:
            pass

    @property
    def cache_directory(self):
        from directory import directory
        return directory(self.cache_directory_name)

    cache_files = alias_property("cache_directory.files")

    @monitored_property
    def cache_size(self, cache_files):
        """How many packets are cached on the local file system?"""
        return len(cache_files)

    @cache_size.setter
    def cache_size(self, size):
        self.cache_files = self.cache_files[0:size]

    def cache_filenames(self, key):
        """Where to store the data associated with key"""
        # If the key exceeds 254 characters, it needs to be shortened
        # by hashing, otherwise the file system would not allow it
        # to be used as a filename.
        filenames = []
        filename = self.cache_directory_name + "/" + key
        if valid_pathname(filename):
            filenames += [filename]
        filenames += [self.cache_directory_name + "/" + get_hash(key)]
        return filenames

    @property
    def cache_directory_name(self):
        """Where to store temporary files"""
        from tempfile import gettempdir
        basedir = gettempdir()
        directory = basedir + "/sequencer/cache"
        return directory

    @monitored_property
    def remote_cache_size(self, loaded_sequence_ids):
        """How many sequences are stored in the memory of the FPGA timing
        system?"""
        return len(loaded_sequence_ids)

    @remote_cache_size.setter
    def remote_cache_size(self, count):
        sequence_ids_to_keep = list(self.current_queue)
        for s in self.loaded_sequence_ids:
            if s not in sequence_ids_to_keep and len(sequence_ids_to_keep) < count:
                sequence_ids_to_keep.append(s)
        self.loaded_sequence_ids = sequence_ids_to_keep

    def remove_unused_sequences(self):
        self.loaded_sequence_ids = self.queued_sequence_ids

    # e.g. f0e55f6b071d6b1f0cc341b2cce2451e
    from re import compile
    sequence_id_pattern = compile("^[0-9a-f]{32}$")

    @monitored_property
    def loaded_sequence_ids(self, sequencer_fs_files):
        """ID strings of sequences currently stored in the memory of the
        FPGA timing system."""
        files = sequencer_fs_files
        from re import match
        sequence_ids = [f for f in files if match(self.sequence_id_pattern, f)]
        return sequence_ids

    @loaded_sequence_ids.setter
    def loaded_sequence_ids(self, sequence_ids):
        files = self.sequencer_fs_files
        from re import match
        other_files = [f for f in files if not match(self.sequence_id_pattern, f)]
        self.sequencer_fs_files = other_files + sequence_ids

    @property
    def queued_sequence_ids(self):
        """ID strings of sequences currently or potentially in use"""
        IDs = []
        for queue_name in self.queue_names:
            IDs += self.get_queue_content(queue_name)
        IDs = list(set(IDs))
        return IDs

    def update(self):
        """Execute sequence using the current default parameters"""
        self.set_default_sequences()
        self.interrupt_enabled = True

    sequence_cache = {}


def sequencer_packet(register_specs, descriptor=None):
    """Binary data packet for the timing sequencer (for one image for example)
    registers: list of timing register objects
    counts: list of integer arrays, one array for each register
    """
    registers = [spec.register for spec in register_specs]

    # Find the times when register counts change.
    N = max([len(spec.counts) for spec in register_specs])

    packets = {}

    def append(packets, key, data):
        packets[key] = packets.get(key, b"") + data

    from sparse_array import starts

    for i_reg, spec in enumerate(register_specs):
        for op in spec.op.split(","):
            if op == "set":
                for it in starts(spec.counts):
                    count = spec.counts[it]
                    packet = write_packet(spec.register, count)
                    append(packets, (it, i_reg), packet)
            elif op == "inc":
                for it in starts(spec.counts):
                    count = spec.counts[it]
                    if count != 0:
                        packet = increment_packet(spec.register, count)
                        append(packets, (it, i_reg), packet)
            elif op == "report":
                for it in starts(spec.counts):
                    count = spec.counts[it]
                    if not ("inc" in spec.op and count == 0):
                        packet = report_packet(spec.register)
                        append(packets, (it, i_reg), packet)
            else:
                logging.warning(f"{op!r}: Expecting 'set', 'inc', or 'report'")

    # Assemble packets in correct sequence order
    interrupt_data = [b""] * N
    if N > 0:
        interrupt_data[0] += interrupt_count_packet(N)
        if descriptor:
            interrupt_data[0] += descriptor_packet(descriptor)
    for it in range(0, N):
        for i_reg in range(0, len(registers)):
            if (it, i_reg) in packets:
                interrupt_data[it] += packets[it, i_reg]
        if len(interrupt_data[it]) > 0:
            interrupt_data[it] = index_count_packet(it) + interrupt_data[it]

    data = b""
    for it in range(0, N):
        data += interrupt_data[it]

    return data


def packet(packet_type=None, payload=b""):
    """Timing sequencer instruction
    Return value: binary data
    """
    if packet_type is None:
        packet_type = 0
    if isinstance(packet_type, str):
        packet_type = type_codes[packet_type]
    from struct import pack
    fmt = ">BBH"
    version = 1
    header_size = len(pack(fmt, packet_type, version, 0))
    length = header_size + len(payload)
    data = pack(fmt, packet_type, version, length) + payload
    return data


def write_packet(register, count):
    """Timing sequencer instruction to write a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),value (32bits), total 16 bytes
    register: e.g. pson
    count: integer number
    Return value: binary data as string
    """
    data = b''
    count_bitmask = ((1 << register.bits) - 1)
    converted_count = to_int(count) & count_bitmask
    if converted_count != count:
        logging.warning(f"register {register!r}, mask 0x{count_bitmask:X}: converting count {count} to {converted_count}")
    count = converted_count
    bitmask = count_bitmask << register.bit_offset
    address = register.address
    bit_count = count << register.bit_offset
    from struct import pack, error
    try:
        data = packet("write", pack(">III", address, bitmask, bit_count))
    except error:
        logging.warning(f"register {register!r}, count {count}: address {address}, bitmask {bitmask}, bit_count {bit_count}: {format_exc()}")
    return data


def increment_packet(register, count):
    """Timing sequencer instruction to write a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),value (32bits), total 16 bytes
    register: e.g. pson
    count: integer number
    Return value: binary data as string
    """
    if count != 0:
        # logging.debug(f"increment_packet({register!r}, {count})")
        from struct import pack
        count_bitmask = ((1 << register.bits) - 1)
        if count != to_int(count) & count_bitmask:
            logging.warning(f"write_packet({register!r}, {count}): converting count to {to_int(count) & count_bitmask}")
        count = to_int(count) & count_bitmask
        bitmask = count_bitmask << register.bit_offset
        address = register.address
        bit_count = count << register.bit_offset
        data = packet("increment", pack(">III", address, bitmask, bit_count))
    else:
        data = b""
    return data


def descriptor_packet(descriptor):
    """Timing sequencer instruction
    descriptor: Parameter list as string
    Format: type (8bits),version (8bits),length (16bits),
      string(variable length)
    Return value: binary data as string
    """
    data = packet("descriptor", descriptor.encode("utf-8"))
    return data


def output_packet(message):
    """Timing sequencer instruction
    message: string
    Format: type (8bits),version (8bits),length (16bits),
      string(variable length)
    Return value: binary data as string
    """
    data = packet("output", message.encode("utf-8"))
    return data


def sequence_length_packet(sequence_length):
    """How long is the sequence of instructions following in bytes?
    Timing sequencer instruction
    sequence_length: integer, number of bytes
    Format: type (8bits),version (8bits),length (16bits),
      packet_length(32 bits)
    Return value: binary data as string, length: 8 bytes
    """
    from struct import pack
    data = packet("sequence length", pack(">I", sequence_length))
    return data


def interrupt_count_packet(interrupt_count):
    """How long will the sequence of instructions following take to execute?
    Timing sequencer instruction
    packet_length: integer, number of bytes
    Format: type (8bits),version (8bits),length (16bits),
      interrupt_count(32 bits)
    Return value: binary data as string, length: 8 bytes
    """
    from struct import pack
    data = packet("interrupt count", pack(">I", interrupt_count))
    return data


def report_packet(register):
    """Timing sequencer instruction to report the value of a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),string(variable length)
    register: object e.g. self.timing_system.registers.image_number
    count: integer number
    Return value: binary data as string
    """
    count_bitmask = ((1 << register.bits) - 1)
    bitmask = count_bitmask << register.bit_offset
    address = register.address
    name = register.name
    from struct import pack
    data = packet("report", pack(">II", address, bitmask) + name.encode("utf-8"))
    return data


def index_count_packet(index_count):
    """How many interrupts after the beginning of the sequence will the following
    packets execute?
    Timing sequencer instruction
    packet_length: integer, number of bytes
    Format: type (8bits),version (8bits),length (16bits),
      index_count(32 bits)
    Return value: binary data as string, length: 8 bytes
    """
    from struct import pack
    data = packet("index count", pack(">I", index_count))
    return data


def descriptor(data):
    """Parameter list as string
    data: binary data a string"""
    from struct import unpack
    descriptor = ""
    i = 0
    while i < len(data):
        packet_type, version, length = unpack(">BBH", data[i:i + 4])
        if packet_type == 3:
            payload = data[i + 4:i + length]
            descriptor = payload.decode("utf-8")
            break
        i += length
    return descriptor


def interrupt_count(data):
    """How long does this packet take to execute in clock ticks?
    data: binary data a string"""
    from struct import unpack
    count = 0
    i = 0
    while i < len(data):
        packet_type, version, length = unpack(">BBH", data[i:i + 4])
        header_size = len(packet())
        payload = data[i + header_size:i + length]
        type_name = type_names.get(packet_type, "unknown")
        if type_name == "interrupt count":
            count, = unpack(">I", payload)
            break
        i += length
    return count


def packet_representation(data):
    """String
    data: binary data a string"""
    from struct import unpack, pack
    text = ""
    i = 0
    interrupt_count = 0
    while i < len(data):
        packet_type, version, length = unpack(">BBH", data[i:i + 4])
        header_size = len(packet())
        payload = data[i + header_size:i + length]
        type_name = type_names.get(packet_type, "unknown")
        payload_repr = ""
        if type_name == "interrupt":
            count, period = unpack(">BB", payload)
            payload_repr = f"{count}/{period}"
            interrupt_count += 1
        if type_name == "write":
            address, bitmask, bit_count = unpack(">III", payload)
            payload_repr = f"addr=0x{address:08X}, mask=0x{bitmask:08X}, count=0x{bit_count:08X}"
        if type_name == "increment":
            address, bitmask, bit_count = unpack(">III", payload)
            payload_repr = f"addr=0x{address:08X}, mask=0x{bitmask:08X}, count=0x{bit_count:08X}"
        if type_name == "descriptor":
            descriptor = payload.decode("utf-8")
            payload_repr = descriptor.replace(",", ",\n").strip("\n")
        if type_name == "output":
            output = payload.decode("utf-8")
            payload_repr = f"{output!r}"
        if type_name == "sequence length":
            sequence_length, = unpack(">I", payload)
            payload_repr = f"{sequence_length} bytes"
        if type_name == "interrupt count":
            count, = unpack(">I", payload)
            payload_repr = f"{count} total"
        if type_name == "report":
            address, bitmask = unpack(">II", payload[0:8])
            name = payload[8:].decode("utf-8")
            payload_repr = f"addr=0x{address:08X}, mask=0x{bitmask:08X}, name={name!r}"
        if type_name == "index count":
            count, = unpack(">I", payload)
            payload_repr = f"{count}"
        if type_name == "index":
            offset_size = len(pack(">I", 0))
            N = len(payload) // offset_size
            addresses = []
            for j in range(0, N):
                address = unpack(">I", payload[j * offset_size:(j + 1) * offset_size])
                addresses += [f"{address:6d}"]
            payload_repr = []
            for j in range(0, N, 8):
                payload_repr += [",".join(addresses[j:j + 8])]
            payload_repr = "\n".join(payload_repr)
        prefix = f"{i:<5d}: {interrupt_count:<4d} {type_name:<15} "
        lines = payload_repr.split("\n")
        for line in lines[:1]:
            text += prefix + abbreviate(line) + "\n"
        for line in lines[1:]:
            text += " " * len(prefix) + abbreviate(line) + "\n"
        i += length
    return text


def abbreviate(text, max_length=240):
    """Shorten a string indicating omitted part using ellipsis ('...')"""
    if len(text) > max_length:
        text = text[0:max_length - 16 - 3] + "..." + text[-16:]
    return text


type_codes = {
    "interrupt": 0,
    "write": 1,
    "increment": 2,
    "descriptor": 3,
    "output": 4,
    "sequence length": 5,
    "interrupt count": 6,
    "report": 7,
    "index": 8,
    "index count": 9,
}

type_names = {type_codes[key]: key for key in type_codes}


def to_int(x):
    """Force conversion to integer"""
    try:
        return int(x)
    except (ValueError, TypeError):
        return 0


def get_hash(text):
    """Calculate the hash of a string, using the MD5 (Message Digest version 5)
    algorithm.
    Return value: ASCII encoded hexadecimal number of 32 digits"""
    import hashlib
    m = hashlib.md5()
    m.update(text.encode("utf-8"))
    value = m.hexdigest()
    return value


def instantiate(x):
    return x()


def hexdump(data):
    """Print string as hexadecimal numbers
    data: string"""
    s = ""
    for x in data:
        s += f"{ord(x):02X} "
    return s


def valid_pathname(filename):
    """Is this filename is not usable on Linux or macOS?"""
    valid = (longest_pathname_component(filename) <= 254)
    return valid


def longest_pathname_component(filename):
    n = max([len(x) for x in filename.split("/")])
    return n


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = 'BioCARS'

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = timing_system_sequencer_driver(timing_system)

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        logging.info(f"{event.reference} = {event.value!r}")

    references = [
        # _reference(self.fs, "queue_sequence_count"),
        # _reference(self, "queue_sequence_count"),
    ]
    for ref in references:
        ref.monitors.add(report)
