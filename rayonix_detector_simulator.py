#!/usr/bin/env python
"""Author: Friedrich Schotte
Date created: 2016-06-17
Last modified: 2022-06-14
Revision comment: Adjusted pixelsize
"""
__version__ = "1.9.3"

from logging import debug, info, error, exception

from handler_method import handler_method


class Rayonix_Detector_Simulator(object):
    from persistent_property import persistent_property

    name = "rayonix_detector_simulator"
    bin_factor = persistent_property("bin_factor", 2)
    readout_mode_number = persistent_property("readout_mode_number", 0)
    n_pixels = 7680
    bkg_image_size = 0
    external_trigger = persistent_property("external_trigger", False)
    # Simulate trigger coming at this interval (in seconds).
    nominal_trigger_period = persistent_property("nominal_trigger_period", 1.0)
    last_filename = ""
    # listen port number of this server
    port = persistent_property("port", 2222)
    acquire_timestamp_offset = persistent_property("acquire_timestamp_offset", 19.128)
    trigger_times = []

    @property
    def state(self):
        if self.acquiring_series:
            return 0x02000000
        return 0

    @property
    def image_size(self):
        from numpy import rint
        return int(rint(self.n_pixels / self.bin_factor))

    def handle_trigger(self, time=None):
        # debug("Trigger detected")
        if time is None:
            from time import time as now
            time = now()
        self.last_trigger_time = time
        if self.acquiring_series:
            if not self.series_triggered:
                info("Ignoring first trigger")
                self.series_triggered = True
            else:
                self.acquire_image(time)

    @property
    def measured_trigger_period(self):
        from numpy import nan
        from time import time
        self.handling_trigger = True
        t = self.trigger_times
        if len(t) >= 2 and time() - t[-1] <= t[-1] - t[-2] + 5:
            T = t[-1] - t[-2]
        else:
            T = nan
        return T

    def get_trigger_period(self):
        if self.external_trigger:
            return self.measured_trigger_period
        else:
            return self.nominal_trigger_period

    def set_trigger_period(self, value):
        self.nominal_trigger_period = value

    trigger_period = property(get_trigger_period, set_trigger_period)

    def acquire_image(self, time):
        from threading import Thread

        if self.acquiring_series:
            filename = "%s%0*d%s" % \
                       (self.filename_base, self.number_field_width,
                        self.frame_number, self.filename_suffix)
            image = self.simulated_image(time)
            info(f"Saving image {filename!r} {image.shape}")
            Thread(target=image.save, args=(filename,)).start()
            self.last_filename = filename
            self.frame_number += 1
        if self.frame_number > self.last_frame_number:
            self.acquiring_series = False

    def simulated_image(self, time):
        from rayonix_image import rayonix_image
        from time import time as now
        from numpy import uint16

        image = rayonix_image(shape=(self.image_size, self.image_size),
                              pixelsize=self.pixelsize)
        image.data[:] += 10 + noise(1, shape=(self.image_size, self.image_size), dtype=uint16)
        image.acquire_timestamp = time + self.acquire_timestamp_offset
        image.header_timestamp = now()
        image.image_timestamp = int(now())
        return image

    @property
    def last_trigger_time(self):
        from time import time
        try:
            t = self.trigger_times[-1]
        except IndexError:
            t = time()
        return t

    @last_trigger_time.setter
    def last_trigger_time(self, time):
        self.trigger_times = self.trigger_times[-9:] + [time]

    @property
    def pixelsize(self):
        pixelsize = 0.0443 * self.bin_factor
        return pixelsize

    def acquire_series(self):
        if self.external_trigger:
            self.acquire_series_on_trigger()
        self.acquire_series_on_timer()

    def acquire_series_on_trigger(self):
        from time import sleep
        self.handling_trigger = True
        while self.acquiring_series:
            sleep(0.05)

    @property
    def handling_trigger(self):
        return self.trigger_handler in self.trigger_handlers

    @handling_trigger.setter
    def handling_trigger(self, handling):
        if handling:
            self.trigger_handlers.add(self.trigger_handler)
        else:
            self.trigger_handlers.remove(self.trigger_handler)

    @handler_method
    def trigger_handler(self, event):
        debug(f"{event}")
        self.handle_trigger(event.time)

    @property
    def trigger_handlers(self):
        from reference import reference
        return reference(self.trigger_PV, "value").monitors

    @property
    def trigger_PV(self):
        from CA import PV
        return PV(self.trigger_PV_name)

    @property
    def trigger_PV_name(self):
        return self.__trigger_PV_name__

    @trigger_PV_name.setter
    def trigger_PV_name(self, value):
        if value != self.__trigger_PV_name__:
            handling_trigger = self.handling_trigger
            self.handling_trigger = False
            self.__trigger_PV_name__ = value
            self.trigger_times = []
            self.handling_trigger = handling_trigger

    __trigger_PV_name__ = persistent_property("trigger_PV_name", "NIH:TIMING.registers.ch7_trig_count.count")

    @property
    def trigger_PV_OK(self):
        from CA import caget
        return caget(self.trigger_PV_name) is not None

    def acquire_series_on_timer(self):
        from time import sleep
        sleep(self.trigger_period)
        while self.acquiring_series:
            self.handle_trigger()
            sleep(self.trigger_period)

    def process_command(self, query):
        """Process a command"""
        if query == "get_state":
            return str(self.state)
        elif query.startswith("start_series,"):
            (
                start_series,
                n_frames,
                first_frame_number,
                integration_time,
                interval_time,
                frame_trigger_type,
                series_trigger_type,
                filename_base,
                filename_suffix,
                number_field_width,
            ) = query.split(",")
            self.start_series(int(n_frames), int(first_frame_number),
                              float(integration_time), float(interval_time),
                              int(frame_trigger_type), int(series_trigger_type),
                              filename_base, filename_suffix, int(number_field_width))
        elif query == "get_bin":
            return str(self.bin_factor) + "," + str(self.bin_factor)
        elif query.startswith("set_bin,"):
            set_bin, bin_factor, bin_factor = query.split(",")
            self.bin_factor = int(bin_factor)
        elif query == "get_readout_mode":
            return f"{self.readout_mode_number}"
        elif query.startswith("set_readout_mode,"):
            value = query.replace("set_readout_mode,", "", 1)
            try:
                n = int(value)
            except ValueError as x:
                error(f"set_readout_mode: {value!r}: {x}")
            else:
                self.readout_mode_number = n
        elif query == "get_size":
            return str(self.image_size) + "," + str(self.image_size)
        elif query == "get_size_bkg":
            return str(self.bkg_image_size) + "," + str(self.bkg_image_size)
        elif query.startswith("trigger,"):
            self.handle_trigger()
        elif query == "abort":
            self.abort()

    def start_series(
            self,
            n_frames=None,
            first_frame_number=None,
            integration_time=None,
            interval_time=None,
            frame_trigger_type=None,
            series_trigger_type=None,
            filename_base=None,
            filename_suffix=None,
            number_field_width=None,
            ):
        """Start acquisition of image series."""
        from normpath import normpath
        if n_frames is not None:
            self.n_frames = n_frames
        if first_frame_number is not None:
            self.first_frame_number = first_frame_number
        if integration_time is not None:
            pass
        if interval_time is not None:
            pass
        if frame_trigger_type is not None:
            pass
        if series_trigger_type is not None:
            pass
        if filename_base is not None:
            self.filename_base = normpath(filename_base)
        if filename_suffix is not None:
            self.filename_suffix = filename_suffix
        if number_field_width is not None:
            self.number_field_width = number_field_width

        info("Starting series of %d images..." % self.n_frames)
        self.frame_number = self.first_frame_number
        self.acquiring_series = True
        self.series_triggered = False  # trigger pulse seen?
        from threading import Thread
        Thread(target=self.acquire_series).start()

    n_frames = persistent_property("n_frames", 10)
    first_frame_number = persistent_property("first_frame_number", 0)
    filename_base = persistent_property("filename_base", "/tmp/")
    filename_suffix = persistent_property("filename_suffix", ".rx")
    number_field_width = persistent_property("number_field_width", 6)

    frame_number = 0
    acquiring_series = False
    series_triggered = False

    @property
    def last_frame_number(self):
        return self.first_frame_number + self.n_frames - 1

    def abort(self):
        """End acquisition of image series."""
        info("Aborting acquisition.")
        self.acquiring_series = False

    def get_acquiring(self):
        """Is image series acquisition in progress?"""
        return self.acquiring_series

    def set_acquiring(self, value):
        if value:
            self.start_series()
        else:
            self.abort()

    acquiring = property(get_acquiring, set_acquiring)

    @property
    def readout_time(self):
        """Estimated readout time in seconds. Changes with 'bin_factor'."""
        return self.readout_time_of_bin_factor(self.bin_factor)

    def readout_time_of_bin_factor(self, bin_factor):
        """Estimated readout time in seconds as function of bin factor."""
        safetyFactor = 1
        from numpy import nan
        if bin_factor in self.readout_rate:
            read_time = 1.0 / self.readout_rate[bin_factor]
        else:
            read_time = nan
        return read_time * safetyFactor

    # Readout rate in frames per second as function of bin factor:
    readout_rate = {1: 2, 2: 10, 3: 15, 4: 25, 5: 40, 6: 60, 8: 75, 10: 120}

    def get_server_running(self):
        return getattr(self.server, "active", False)

    def set_server_running(self, value):
        if self.server_running != value:
            if value:
                self.start_server()
            else:
                self.stop_server()

    server_running = property(get_server_running, set_server_running)

    server = None

    def start_server(self):
        # Stop with: "self.server.shutdown()"
        from threading import Thread
        Thread(target=self.run_server, daemon=True).start()

    def stop_server(self):
        if getattr(self.server, "active", False):
            self.server.server_close()
            setattr(self.server, "active", False)

    def run_server(self):
        from CAServer import casput
        casput("NIH:RAYONIX_SIM.ONLINE", 1)
        try:
            # make a threaded server, listen/handle clients forever
            self.server = self.ThreadingTCPServer(("", self.port), self.ClientHandler)
            setattr(self.server, "active", True)
            info("server version %s started, listening on port %d." % (__version__, self.port))
            self.server.serve_forever()
        except Exception as msg:
            info("run_server: %s" % msg)
        info("server shutting down")
        from CAServer import casdel
        casdel("NIH:RAYONIX_SIM.ONLINE")

    # By default, the "ThreadingTCPServer" class binds to the sever port
    # without the option SO_REUSEADDR. The consequence of this is that
    # when the server terminates you have to let 60 seconds pass, for the
    # socket to leave to "CLOSED_WAIT" state before it can be restarted,
    # otherwise the next bind call would generate the error
    # 'Address already in use'.
    # Setting allow_reuse_address to True makes "ThreadingTCPServer" use to
    # SO_REUSEADDR option when calling "bind".
    import socketserver

    class ThreadingTCPServer(socketserver.ThreadingTCPServer):
        allow_reuse_address = True

    class ClientHandler(socketserver.BaseRequestHandler):
        def handle(self):
            """Called when a client connects. 'self.request' is the client socket"""
            info("accepted connection from " + self.client_address[0])
            import socket
            input_queue = b""
            while getattr(self.server, "active", False):
                # Commands from a client are not necessarily received as one packet
                # but each command is terminated by a newline character.
                # If 'recv' returns an empty string it means client closed the
                # connection.
                while input_queue.find(b"\n") == -1:
                    self.request.settimeout(1.0)
                    received = b""
                    while getattr(self.server, "active", False):
                        try:
                            received = self.request.recv(2 * 1024 * 1024)
                        except socket.timeout:
                            continue
                        except Exception as x:
                            error("%s" % x)
                        if received == b"":
                            info("client disconnected")
                        break
                    if received == b"":
                        break
                    input_queue += received
                if input_queue == b"":
                    break
                if input_queue.find(b"\n") != -1:
                    end = input_queue.index(b"\n")
                    query = input_queue[0:end]
                    input_queue = input_queue[end + 1:]
                else:
                    query = input_queue
                    input_queue = b""
                query = query.strip(b"\r ")
                query = query.decode("latin-1")
                if not query.startswith("get_"):
                    debug(f"Received command {query!r}")
                try:
                    reply = rayonix_detector_simulator.process_command(query)
                except Exception as x:
                    exception(f"{query}: {x}")
                    reply = ""
                if reply:
                    reply = reply.replace("\n", "")  # "\n" = end of reply
                    reply += "\n"
                    # debug("sending reply %r" % reply)
                    reply = reply.encode("utf-8")
                    self.request.sendall(reply)
            info("closing connection to " + self.client_address[0])
            self.request.close()


rayonix_detector_simulator = Rayonix_Detector_Simulator()


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3]  # omit microseconds


def noise(average, shape, dtype=int):
    """Simulated shot noise"""
    from numpy import product
    size = product(shape)
    from numpy.random import poisson
    from numpy import ceil, tile
    block_size = 40000
    block_count = int(ceil(float(size) / block_size))
    block = poisson(average, block_size).astype(dtype)
    noise = tile(block, block_count)[0:size]
    noise = noise.reshape(shape)
    return noise


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = rayonix_detector_simulator

    # print('self.acquiring = True')
    print('self.trigger_PV_name = %r' % self.trigger_PV_name)
    print('self.trigger_PV_OK')
    print('self.trigger_period')
    print('self.server_running = True')
    print('self.run_server()')
