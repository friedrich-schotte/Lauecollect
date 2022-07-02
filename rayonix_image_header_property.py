"""
Author: Friedrich Schotte
Date created: 2022-06-14
Date last modified: 2022-06-14
Revision comment:
"""
__version__ = "1.0"
 
import logging


class bytes_header_property(property):
    def __init__(self, start, end):
        """
        :param start: byte offset
        :param end: byte offset
        """
        self.start = start
        self.end = end
        super().__init__(fget=self.get_value, fset=self.set_value)

    def get_value(self, image):
        return image.header_[self.start:self.end]

    def set_value(self, image, value):
        image.header[self.start:self.end] = value


class packed_header_property(bytes_header_property):
    def __init__(self, start, end, format_string):
        super().__init__(start, end)
        self.format_string = format_string

    def get_value(self, image):
        from struct import unpack
        data_bytes = super().get_value(image)
        value = unpack(self.format_string, data_bytes)[0]
        return value

    def set_value(self, image, value):
        from struct import pack
        from numpy import rint
        data_bytes = pack(self.format_string, int(rint(value)))
        super().set_value(image, data_bytes)


class scaled_header_property(packed_header_property):
    def __init__(self, start, end, format_string, scale_factor):
        super().__init__(start, end, format_string)
        self.scale_factor = scale_factor

    def get_value(self, image):
        return super().get_value(image) / self.scale_factor

    def set_value(self, image, value):
        super().set_value(image, value * self.scale_factor)


class string_header_property(bytes_header_property):
    def __init__(self, start, end):
        super().__init__(start, end)

    def get_value(self, image):
        data_bytes = super().get_value(image)
        value = data_bytes.rstrip(b"\0").decode("utf-8")
        return value

    def set_value(self, image, value):
        length = len(super().get_value(image))
        data_bytes = value.encode("utf-8")
        data_bytes = data_bytes.ljust(length, b'\0')
        data_bytes = data_bytes[0:length]
        super().set_value(image, data_bytes)


class converted_header_property(bytes_header_property):
    def __init__(self, start, end, converter):
        super().__init__(start, end)
        self.converter = converter

    def get_value(self, image):
        data_bytes = super().get_value(image)
        return self.converter.from_bytes(data_bytes)

    def set_value(self, image, value):
        data_bytes = self.converter.to_bytes(value)
        super().set_value(image, data_bytes)


class timestamp_header_property(converted_header_property):
    def __init__(self, start, end):
        super().__init__(start, end, converter=timestamp_converter)


class optional_timestamp_header_property(converted_header_property):
    def __init__(self, start, end):
        super().__init__(start, end, converter=optional_timestamp_converter)


class timestamp_converter:
    @staticmethod
    def from_bytes(data_bytes):
        try:
            months = int(data_bytes[:2])
            days = int(data_bytes[2:4])
            hours = int(data_bytes[4:6])
            minutes = int(data_bytes[6:8])
            year = int(data_bytes[8:12])
            seconds = int(data_bytes[13:15])

            from datetime import datetime
            date_time = datetime(year, months, days, hours, minutes, seconds)
            from time import mktime
            timestamp = mktime(date_time.timetuple())
        except ValueError:
            from numpy import nan
            timestamp = nan
        # Old version rayonix mccd file on before Feb 6 2015 does not have microseconds
        try:
            microseconds = int(data_bytes[16:22])
        except ValueError:
            microseconds = 0
        timestamp += microseconds * 1e-6

        return timestamp

    @staticmethod
    def to_bytes(value):
        from datetime import datetime
        data_bytes = datetime.fromtimestamp(value).strftime("%m%d%H%M%Y.%S %f") \
            .encode("ASCII").replace(b" ", b"\0").ljust(32, b"\0")
        return data_bytes


class optional_timestamp_converter:
    @staticmethod
    def from_bytes(data_bytes):
        from numpy import nan
        data_bytes = data_bytes.strip(b"\0")
        try:
            value = float(data_bytes)
        except ValueError:
            value = nan
        return value

    @staticmethod
    def to_bytes(value):
        return (b"%.9f" % value).ljust(32, b"\0")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
