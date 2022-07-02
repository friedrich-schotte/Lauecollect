"""
Author: Friedrich Schotte
Date created: 2022-05-12
Date last modified: 2022-05-12
Revision comment:
"""
__version__ = "1.0"

import logging


class field(property):
    def __init__(self, format_string, start, end):
        property.__init__(self, fget=self.get_property)
        self.format_string = format_string
        self.start = start
        self.end = end

    def get_property(self, instance):
        from struct import unpack
        return unpack(self.format_string, instance.wavedesc[self.start:self.end])[0]


class lecroy_scope_trace_file:
    filename = ""

    def __init__(self, filename=None):
        if filename is not None:
            self.filename = filename

    def __repr__(self):
        return f"{type(self).__name__}({self.filename!r})"

    @property
    def waveform(self):
        """tuple of two arrays, time, voltage"""
        from numpy import arange, array
        from numpy import frombuffer, int8, int16, float64, concatenate, zeros, nan

        # Check if format is indeed little-endian.
        assert(self.comm_order != 0)

        dtype = int8 if self.comm_type == 0 else int16
        data = frombuffer(self.content[self.data_offset:], dtype).astype(float)
        Nsamples = self.wave_array_count // self.subarray_count
        expected_size = self.subarray_count * Nsamples
        if len(data) < expected_size:
            logging.warning("%s: expecting %d*%d=%d samples, file truncated at %d samples." %
                            (filename, self.subarray_count, Nsamples, expected_size, len(data)))
            data = concatenate((data, nan * zeros(expected_size - len(data))))
        data = data.reshape((self.subarray_count, Nsamples))
        # Convert counts to voltage.
        U = data * self.vertical_gain - self.vertical_offset

        # Reconstruct time scales.
        trigger_time_array_offset = self.trigger_times_and_offsets_offset
        trigger_time_array = self.content[trigger_time_array_offset:trigger_time_array_offset + self.trig_time_array_size]

        data = frombuffer(trigger_time_array, float64)
        data = data.reshape((self.subarray_count, 2))
        relative_trigger_times, trigger_offsets = data.T

        t = array([arange(0, Nsamples) * self.horiz_interval + t0 for t0 in trigger_offsets])
        # t = array([arange(0,Nsamples)*horiz_interval for t0 in trigger_offsets])+trigger_offsets[0]

        return t, U

    @property
    def trigger_time(self):
        from struct import unpack
        from time import mktime
        from numpy import floor

        second, = unpack("<d", self.wavedesc[296 + 0:296 + 8])
        minute, = unpack("B", self.wavedesc[296 + 8:296 + 9])
        hour, = unpack("B", self.wavedesc[296 + 9:296 + 10])
        day, = unpack("B", self.wavedesc[296 + 10:296 + 11])
        month, = unpack("B", self.wavedesc[296 + 11:296 + 12])
        year, = unpack("H", self.wavedesc[296 + 12:296 + 14])
        trigger_time = mktime((year, month, day, hour, minute, int(floor(second)), -1, -1, -1)) \
            + (second - floor(second))
        return trigger_time

    @property
    def trigger_times(self):
        return self.trigger_time + self.relative_trigger_times

    @property
    def trigger_offsets(self):
        return self.trigger_times_and_offsets_array.T[1]

    @property
    def relative_trigger_times(self):
        return self.trigger_times_and_offsets_array.T[0]

    @property
    def trigger_times_and_offsets_array(self):
        from numpy import frombuffer, float64
        return frombuffer(self.trigger_times_and_offsets_data, float64).reshape((self.subarray_count, 2))

    @property
    def trigger_times_and_offsets_data(self):
        return self.content[self.trigger_times_and_offsets_offset:self.trigger_times_and_offsets_offset + self.trig_time_array_size]

    @property
    def trigger_times_and_offsets_offset(self):
        return self.wavedesc_offset + self.wave_descriptor_length + self.user_text_length

    @property
    def wavedesc(self):
        return self.content[self.wavedesc_offset:self.wavedesc_offset + 346]

    @property
    def wavedesc_offset(self):
        return self.content.find(b"WAVEDESC")

    @property
    def data_offset(self):
        return self.trigger_times_and_offsets_offset + \
               self.trig_time_array_size

    comm_type = field("<H", 32, 34)  # 0 = 8-bit, 1=16-bit
    comm_order = field("<H", 34, 36)  # 0=big endian, 1=little endian

    wave_descriptor_length = field("<i", 36, 40)
    user_text_length = field("<i", 40, 44)
    trig_time_array_size = field("<i", 48, 52)

    wave_array_1 = field("<i", 60, 64)
    wave_array_count = field("<i", 116, 120)
    subarray_count = field("<i", 144, 148)  # number of trigger events

    vertical_gain = field("<f", 156, 160)
    vertical_offset = field("<f", 160, 164)
    horiz_interval = field("<f", 176, 180)
    horiz_offset = field("<d", 180, 188)

    @property
    def content(self):
        if self.filename:
            from os.path import getsize
            length = getsize(self.filename)
            with open(self.filename, "rb+") as f:
                from mmap import mmap
                content = mmap(f.fileno(), length=length)
                f.close()
        else:
            content = bytearray()
        return content


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    filename = '//femto-data2/C/Data/2022.03/WAXS/GB3/GB3_PumpProbe_PC0-1/xray_traces/GB3_PumpProbe_PC0-1_6240_178ms_01_64.040C_07_01_C1.trc'
    self = lecroy_scope_trace_file(filename)

    print("from time_string import date_time; print(date_time(self.trigger_time))")
