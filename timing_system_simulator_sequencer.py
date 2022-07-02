#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2020-05-20
Date last modified: 2022-05-24
Revision comment: Fixed: Issue: Reports send prematurely
    (by 2.2 s for example is packet length is 2.2 s)
"""
__version__ = "1.5.3"

import logging

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error


class Timing_System_Simulator_Sequencer:
    def __init__(self, timing_system):
        self.timing_system = timing_system
        self.__interrupt_handler_enabled__ = False
        self.sequencer_running = False

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.timing_system)

    version = __version__

    from cached import cached

    @cached
    @property
    def sysctl(self):
        from timing_system_simulator_sequencer_sysctl import Timing_System_Simulator_Sequencer_Sysctl
        return Timing_System_Simulator_Sequencer_Sysctl(self)

    @property
    def db_name(self):
        return self.timing_system.db_basename + "/sequencer"

    from db_property import db_property

    buffer_size = db_property("buffer_size", 8 * 1024)
    descriptor = db_property("descriptor", "")
    queue_name = db_property("queue_name", "")
    next_queue_name = db_property("next_queue_name", "")
    next_queue_sequence_count = db_property("next_queue_sequence_count", 0)
    next_queue_repeat_count = db_property("next_queue_repeat_count", 0)
    default_queue_name = db_property("default_queue_name", "")
    phase_matching_period = db_property("phase_matching_period", 12)

    def reset(self):
        self.buffer_size = 8 * 1024
        self.descriptor = ""
        self.queue_name = ""
        self.next_queue_name = ""
        self.default_queue_name = ""
        self.phase_matching_period = 12
        self.interrupt_handler_enabled = False

    from numpy import nan
    sequence_start_time = nan
    sequence_end_time = nan

    dt = db_property("dt", 0.0010182857142857144)

    from thread_property_2 import thread_property

    @thread_property
    def sequencer_running(self):
        from numpy import nan, isnan
        from time import time, sleep

        self.sequence_start_time = nan
        self.sequence_end_time = nan

        while not self.sequencer_running_cancelled:
            self.handle_single_sequence()

            wait_time = self.sequence_end_time - time()
            if isnan(wait_time):
                wait_time = 0.1
            # debug("sleep %r" % wait_time)
            if wait_time > 0:
                sleep(wait_time)

        self.sequence_start_time = nan
        self.sequence_end_time = nan

    sequencer_running_cancelled = False

    def get_interrupt_handler_enabled(self):
        return bool(self.__interrupt_handler_enabled__)

    def set_interrupt_handler_enabled(self, value):
        self.__interrupt_handler_enabled__ = bool(value)
        self.sequencer_running = value

    interrupt_handler_enabled = property(
        fget=get_interrupt_handler_enabled,
        fset=set_interrupt_handler_enabled,
    )

    def handle_single_sequence(self):
        from time import time
        from numpy import nan, isnan

        self.switch_sequence()
        data = self.current_sequence_data
        if data:
            if not isnan(self.sequence_end_time):
                self.sequence_start_time = self.sequence_end_time
            else:
                self.sequence_start_time = time()

            self.process_packet(data)
        else:
            if not isnan(self.sequence_end_time):
                self.report(self.sequence_start_time, "sequencer.current_sequence", "")
                self.report(self.sequence_start_time, "sequencer.current_sequence_length", 0)
            self.sequence_start_time = nan
            self.sequence_end_time = nan

    def process_packet(self, data):
        self.report(self.sequence_start_time, "sequencer.current_sequence",
                    self.current_sequence)
        self.report(self.sequence_start_time, "sequencer.current_sequence_length",
                    self.current_sequence_length)

        from struct import unpack
        from timing_system_sequencer import packet, type_names
        from sleep_until import sleep_until

        i = 0
        index_count = 0
        while i < len(data):
            timestamp = self.sequence_start_time + index_count * self.dt
            sleep_until(timestamp)

            packet_type, version, length = unpack(">BBH", data[i:i + 4])
            header_size = len(packet())
            payload = data[i + header_size:i + length]
            type_name = type_names.get(packet_type, "unknown")

            if type_name == "index count":
                count, = unpack(">I", payload)
                index_count = count
            elif type_name == "write":
                address, bitmask, bit_count = unpack(">III", payload)
                self.write_register(address, bitmask, bit_count)
            elif type_name == "increment":
                address, bitmask, bit_count = unpack(">III", payload)
                count = self.read_register(address, bitmask)
                count += bit_count
                self.write_register(address, bitmask, count)
            elif type_name == "report":
                address, bitmask = unpack(">II", payload[0:8])
                name = payload[8:].decode("utf-8")
                count = self.read_register(address, bitmask)
                self.report(timestamp, "registers." + name + ".count", str(count))
            elif type_name == "descriptor":
                descriptor = payload.decode("utf-8")
                if descriptor != self.descriptor:
                    self.descriptor = descriptor
                    self.report(self.sequence_start_time, "sequencer.descriptor", descriptor)
            elif type_name == "interrupt count":
                count, = unpack(">I", payload)
                self.sequence_end_time = self.sequence_start_time + count * self.dt
            i += length

    def read_register(self, address, bitmask):
        count = self.timing_system.registers.read(address, bitmask)
        return count

    def write_register(self, address, bitmask, count):
        self.timing_system.registers.write(address, bitmask, count)

    def report(self, timestamp, name, value):
        from numpy import isnan
        if isnan(timestamp):
            from time import time
            timestamp = time()
        report = "%.9f %s=%s" % (timestamp, name, value)
        if value != 0:
            debug("Report %.60s" % report)
        self.timing_system.handle_report(report)

    def switch_sequence(self):
        queue_sequence_count = self.queue_sequence_count
        queue_sequence_count += 1
        if queue_sequence_count >= len(self.queue):
            queue_sequence_count = 0
            self.queue_repeat_count += 1
        self.queue_sequence_count = queue_sequence_count
        self.switch_queue()

    def switch_queue(self):
        old_queue_name = self.queue_name
        old_next_queue_name = self.next_queue_name

        # Cleanup
        if self.next_queue_name and self.next_queue_name == self.queue_name:
            self.next_queue_name = ""

        if self.next_queue_name:
            switch_to_next_queue = False
            if self.next_queue_sequence_count < 0:
                info(
                    f"Switching queue from {self.queue_name!r} "
                    f"to {self.next_queue_name!r} immediately "
                    f"because it is the next queue and next queue sequence "
                    f"count is invalid ({self.next_queue_sequence_count})."
                )
                switch_to_next_queue = True
            if self.queue_repeat_count >= self.next_queue_repeat_count and \
                    self.queue_sequence_count == self.next_queue_sequence_count:
                info(
                    f"Switching queue from {self.queue_name!r} "
                    f"to {self.next_queue_name} "
                    f"because it is the next queue and "
                    f"queue repeat count {self.queue_repeat_count} >= next queue repeat count {self.next_queue_repeat_count} and "
                    f"queue sequence count {self.queue_sequence_count} == next queue sequence count {self.next_queue_sequence_count}"
                )
                switch_to_next_queue = True
            if switch_to_next_queue:
                info("Switching from %r to %r" % (self.queue_name, self.next_queue_name))
                self.queue_name = self.next_queue_name
                self.next_queue_name = ""

        if not self.get_file(self.queue_name) and self.get_file(self.default_queue_name):
            info(
                f"Switching queue from {self.queue_name!r} to {self.default_queue_name!r} "
                f"because file {self.queue_name!r} not found."
            )
            self.queue_name = self.default_queue_name

        if self.queue_name != self.default_queue_name:
            n = self.queue_repeat_count
            n_max = self.queue_max_repeat_count
            if n_max > 0:
                if n >= n_max:
                    info(
                        f"Switching from {self.queue_name} to {self.default_queue_name}"
                        f"queue_repeat_count {n} >= queue_max_repeat_count {n_max}"
                    )
                    self.queue_name = self.default_queue_name

        if self.queue_name != old_queue_name:
            self.report(self.sequence_end_time, "sequencer.queue_name",
                        self.queue_name)
        if self.next_queue_name != old_next_queue_name:
            self.report(self.sequence_end_time, "sequencer.next_queue_name",
                        self.next_queue_name)

    @property
    def current_sequence_data(self):
        return self.get_file(self.current_sequence_filename)

    @property
    def current_sequence_length(self):
        return self.file_size(self.current_sequence_filename)

    @property
    def current_sequence_filename(self):
        lineno = self.queue_sequence_count
        filename = self.queue[lineno] if 0 <= lineno < len(self.queue) else ""
        return filename

    current_sequence = current_sequence_filename

    def get_queue_sequence_count(self):
        return self.get_queue_intval("sequence_count")

    def set_queue_sequence_count(self, count):
        self.set_queue_intval("sequence_count", count)

    queue_sequence_count = property(get_queue_sequence_count, set_queue_sequence_count)

    def get_queue_repeat_count(self):
        return self.get_queue_intval("repeat_count")

    def set_queue_repeat_count(self, count):
        self.set_queue_intval("repeat_count", count)

    queue_repeat_count = property(get_queue_repeat_count, set_queue_repeat_count)

    def get_queue_max_repeat_count(self):
        return self.get_queue_intval("max_repeat_count")

    def set_queue_max_repeat_count(self, count):
        self.set_queue_intval("max_repeat_count", count)

    queue_max_repeat_count = property(get_queue_max_repeat_count, set_queue_max_repeat_count)

    def get_queue_intval(self, name):
        count = 0
        if self.queue_name:
            filename = self.queue_name + "_" + name
            count = self.get_file(filename)
            try:
                count = int(count)
            except ValueError:
                count = 0
        return count

    def set_queue_intval(self, name, count):
        if self.queue_name:
            filename = self.queue_name + "_" + name
            length = len(self.get_file(filename))
            data = "%d" % count
            data = data[0:length].ljust(length - 1, " ")
            if len(data) < length:
                data += "\n"
            self.put_file(filename, data.encode("utf-8"))
            self.report(self.sequence_end_time, "sequencer.fs." + filename,
                        data.replace("\n", " "))

    @property
    def queue(self):
        filename = self.queue_name
        queue = self.get_file(filename)
        queue = queue.decode("utf-8").splitlines()
        return queue

    def get_file(self, filename):
        if filename:
            content = self.timing_system.file_system.get_file(self.path(filename))
        else:
            content = b""
        return content

    def put_file(self, filename, data):
        # debug("%.80r,%.80r" % (filename,data))
        if filename:
            self.timing_system.file_system.put_file(self.path(filename), data)

    def file_size(self, filename):
        if filename:
            size = self.timing_system.file_system.file_size(self.path(filename))
        else:
            size = 0
        return size

    def path(self, filename):
        return self.sequencer_fs_path + "/" + filename

    sequencer_fs_path = "/tmp/sequencer_fs"


if __name__ == "__main__":
    # from pdb import pm
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level, format=msg_format)

    from timing_system_simulator import timing_system_simulator

    timing_system = timing_system_simulator("LaserLab")
    sequencer = Timing_System_Simulator_Sequencer(timing_system)

    self = sequencer

    # print("self.sequencer_running = True; from time import sleep; sleep(1); self.sequencer_running = False")
    # print('')
    print('self.read_register(0xF0FFB034,0x000FFFFF)')
    print('self.write_register(0xF0FFB034,0x000FFFFF,12000)')
