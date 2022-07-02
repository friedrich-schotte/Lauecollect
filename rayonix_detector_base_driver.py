"""
Remote control of the MAR CCD detector, using Michael Blum's sample remote
control server program "marccd_server_socket" with TCP port number 2222.

Usage example: det = rayonix_detector("marccd043.cars.aps.anl.gov:2222")

The server is started from the command line by the command "hsserver_legacy".

The server understand the following commands:
start - Puts the CCD to integration mode, no reply
readout,0,filename - Reads out the detector, corrects the image and saves it to a file
  no reply
readout,1 - reads a new background image, no reply
get_state - reply is integer number containing 6 4-bit fields
  bits 0-3: state: 0=idle,8=busy
  bits 4-7: acquire
  bits 8-11: read
  bits 12-15: correct
  bits 16-19: write 
  bits 20-23: dezinger 
  Each filed contains a 4-bit code, with the following meaning: 
  0=idle, 1=queued, 2=executing, 4=error 
  The exception is the 'state' field, which has only 0=idle and 8=busy.
writefile,<filename>,1 - Save the last read image, no reply
set_bin,8,8 - Use 512x512-pixel bin mode, no reply
set_bin,2,2 - Use full-resolution readout mode (2048x2048 pixels), no reply
  (The 1x1 bin mode with 4096x4096 pixels is not used, because the point-spread
  function of the fiber optic taper is large compared to the pixel size)
get_bin - reply is two integer numbers, e.g. "2,2"
get_size_bkg - reply is the number of pixels of current the background image, e.g. "2048,2048"

Reference: Rayonix HS detector manual 0.3e
Chapter 9: The Legacy Remote Mode for HS Detector Control

Author: Friedrich Schotte
Date created: 2013-09-20
Date last modified: 2022-06-21
Revision comment: Issue:
    polling_monitor.monitoring_setup: Starting polling of rayonix_detector_driver('BioCARS').ip_address_choices
"""
__version__ = "4.2.5"

from logging import info, error

from time import sleep, time

from monitored_value_property import monitored_value_property


def make_directory(filename):
    """Make sure that the directory of the given filename exists by create it,
    if necessary."""
    if filename is None or filename == "":
        return
    from os.path import dirname
    directory = dirname(filename)
    if directory == "":
        return
    makedirs(directory)


class Rayonix_Detector(object):
    """This is to remote control the MAR CCD detector
    Using remote protocol version 1"""
    from db_property import db_property

    db_name = "rayonix_detector"
    ip_address = db_property("ip_address", "mx340hs.cars.aps.anl.gov:2222", local=True)

    ip_address_choices = monitored_value_property([
        "mx340hs.cars.aps.anl.gov:2222",
        "pico5.cars.aps.anl.gov:2222",
        "pico1.niddk.nih.gov:2222",
        "pico5.niddk.nih.gov:2222",
        "pico7.niddk.nih.gov:2222",
        "pico8.niddk.nih.gov:2222",
        "localhost:2222",
    ])

    ignore_first_trigger = db_property("ignore_first_trigger", True)

    def __init__(self, name=None):
        """name: used for IP address, in case there is more than one detector"""
        if name is not None:
            self.name = name
        self.timeout = 1.0
        # This is to make the query method multi-thread safe.
        from threading import Lock
        self.lock = Lock()
        # If this flag is set 'start' automatically reads a background image
        # if there is no valid background image.
        self.auto_bkg = True
        # Whether to save corrected or raw images.
        self.save_raw = False
        # For triggered image acquisition
        # 0: the rising edge of the trigger initiates frame transfer/readout
        # 1: rising edge starts acquisition,
        #    falling edge initiates frame transfer/readout
        self.bulb_mode = 0
        # Keep track of when the detector was last read.
        self.last_read = 0.0
        # Verbose logging: record every command and reply in /tmp/rayonix_detector.log
        self.verbose_logging = True

    @property
    def connected(self):
        from tcp_client import connected
        return connected(self.ip_address)

    online = connected
    detector_online = connected

    def write(self, command):
        """Sends a command that does not generate a reply"""
        info("write %r" % command)
        from tcp_client import write
        write(self.ip_address, command)

    def query(self, command):
        """Send a command that generates a reply.
    Return the reply"""
        # debug("query %r" % command)
        from tcp_client import query
        reply = query(self.ip_address, command).decode("latin-1")
        return reply

    def state_code(self):
        """Status information as integer"""
        reply = self.query("get_state").strip("\n\0")
        if reply == "":
            return 0
        try:
            status = int(eval(reply))
        except Exception as message:
            error("command 'get_state' generated bad reply %r: %s" % (reply, message))
            return 0
        # bit 8 and 9 of the state code tell whether the task status of "read"
        # is either "queued" or "executing"
        if (status & 0x00000300) != 0:
            self.last_read = time()
        return status

    def is_idle(self):
        status = self.state_code()
        # bit mask 0x00444440 masks out error flags
        if (status & ~0x0444444F) == 0:
            return True
        else:
            return False

    def is_integrating(self):
        """tells whether the chip is integrating mode (not reading, not clearing)"""
        # "acquire" field is "executing"
        if not self.connected:
            return True
        return (self.state_code() & 0x00000020) != 0

    def is_reading(self):
        """tells whether the chip is currently being read out"""
        # bit 8 and 9 of the state code tell whether the task status of "read"
        # is either "queued" or "executing"
        return (self.state_code() & 0x00000300) != 0

    def is_correcting(self):
        """tells whether the chip is currently being read out"""
        # bit 8 and 9 of the state code tell whether the task status of "correct"
        # is either "queued" or "executing"
        return (self.state_code() & 0x00003000) != 0

    def state(self):
        """Status information as string: idle,integrating,reading,writing"""
        status = self.state_code()
        # bit mask 0x00444440 masks out error flags
        if (status & ~0x0444444F) == 0:
            return "idle"
        t = []
        if (status & 0x0000000F) == 6:
            t += ["unavailable"]
        if (status & 0x0000000F) == 7:
            t += ["error"]
        if (status & 0x0000000F) == 8:
            t += ["busy"]
        if (status & 0x00000010) != 0:
            t += ["integrate queued"]
        if (status & 0x00000020) != 0:
            t += ["integrating"]
        if (status & 0x00000040) != 0:
            t += ["integrate error"]
        if (status & 0x00000100) != 0:
            t += ["read queued"]
        if (status & 0x00000200) != 0:
            t += ["reading"]
        if (status & 0x00000400) != 0:
            t += ["read error"]
        if (status & 0x00001000) != 0:
            t += ["correct queued"]
        if (status & 0x00002000) != 0:
            t += ["correcting"]
        if (status & 0x00004000) != 0:
            t += ["correct error"]
        if (status & 0x00010000) != 0:
            t += ["write queued"]
        if (status & 0x00020000) != 0:
            t += ["writing"]
        if (status & 0x00040000) != 0:
            t += ["write error"]
        if (status & 0x00100000) != 0:
            t += ["dezinger queued"]
        if (status & 0x00200000) != 0:
            t += ["dezingering"]
        if (status & 0x00400000) != 0:
            t += ["dezinger error"]
        if (status & 0x01000000) != 0:
            t += ["series queued"]
        if (status & 0x02000000) != 0:
            t += ["acquiring series"]
        if (status & 0x04000000) != 0:
            t += ["series error"]
        state = ",".join(t)
        return state

    def start_integration(self, wait=True):
        """Puts the detector into integration mode by stopping the continuous
        clearing.
        In case the CCD readout is in progress, execution is delayed until the
        last readout is finished.
        This also acquires a background image, in case there is no valid background
        image (after startup or binning changed).
        wait: There is a 0.2 s delay until te detector enters "integrating" state,
        (maybe for the clearing to stop?)
        When wait=False, do not wait for this to happen.
        """
        # t0 = time()
        # Wait for the readout of the previous image to finish.
        while self.is_reading():
            sleep(0.05)
            # Work-around for a bug where the detector remains in "reading" state
            # forever. F. Schotte 27 Mar 2014
            # if time()-t0 > 2.0: self.abort()
        # Make sure there is a valid background image. Otherwise, the image
        # correction will fail.
        if self.auto_bkg:
            self.update_bkg()
        self.write("start")
        if not wait:
            return
        while not self.is_integrating() and self.connected:
            sleep(0.05)

    def abort(self):
        """Cancel series acquisition mode"""
        self.write("abort")

    def readout(self, filename=None):
        """Reads the detector.
        If a filename is given, the image is saved as a file.
        The image file is written in background as a pipelined operation.
        The function returns immediately.
        The pathname of the file is interpreted in file system of the server,
        not locally.
        If 'save_raw' is true (default: false), the image raw data is saved
        rather than the correct image.
        """
        if filename is not None:
            make_directory(filename)

        if not self.save_raw:
            if filename is not None:
                self.write("readout,0," + remote(filename))
            else:
                self.write("readout,0")
        else:
            if filename is not None:
                self.write("readout,3," + remote(filename))
            else:
                self.write("readout,3")
        # while not self.is_reading(): sleep(0.05)
        self.last_read = time()

    def readout_and_save_raw(self, filename):
        """Reads the detector and saves the uncorrected image as a file.
        The image file is written in background as a pipelined operation.
        The function returns immediately.
        The pathname of the file is interpreted in file system of the server,
        not locally.
        """
        make_directory(filename)
        self.write("readout,3," + remote(filename))
        self.last_read = time()

    def readout_raw(self):
        """Reads the detector out without correcting and displaying the image."""
        self.write("readout,3")
        self.last_read = time()

    def save_image(self, filename):
        """Saves the last read image to a file.
    The pathname of the file is interpreted in file system of the server,
    not locally.
    """
        make_directory(filename)
        self.write("writefile," + remote(filename) + ",1")

    def save_raw_image(self, filename):
        """Saves the last read image without spatial and uniformity correction
    to a file.
    The pathname of the file is interpreted in file system of the server,
    not locally.
    """
        make_directory(filename)
        self.write("writefile," + remote(filename) + ",0")

    def acquire_images_triggered(self, filenames):
        """Acquire a series of images timed by an external hardware
        trigger signal.
        filenames: list of absolute pathnames. Directory part must be
        valid pathname on file system of the Rayonix computer"""
        # The detector will ignore an "acquire_images_triggered" command if not
        # in "idle" state.
        if not self.state() == "idle":
            self.abort()
        while self.state() != "idle":
            sleep(0.05)

        # The "start_series_triggered" command does not allow a list of filenames
        # to be specified, but uses auto-generated filenames instead.
        # As a work-around generated a series of symbolic link complying to the
        # naming scheme imposed by the 'start_series_triggered' command that
        # point ot the real filenames. When the rayonix software tries to save
        # an image the symbolic link redirects is to create an image with
        # the specified name.
        from os.path import dirname, relpath, islink, exists
        from os import symlink, remove
        from shutil import rmtree
        directory = common_top_directory(filenames)
        tempdir = directory + "/.rayonix_temp"
        try:
            rmtree(tempdir)
        except OSError:
            pass
        makedirs(tempdir)
        for i in range(0, len(filenames)):
            link = tempdir + "/%06d.rx" % (i + 1)
            if islink(link) or exists(link):
                remove(link)
            try:
                pathname = relpath(filenames[i], tempdir)
            except Exception as msg:
                error("Relative path of %r with respect to %r: %s" %
                      (filenames[i], tempdir, msg))
                pathname = filenames[i]
            try:
                symlink(pathname, link)
            except Exception as msg:
                error("Cannot create of %r to %r: %s" % (pathname, link, msg))
            if not exists(dirname(filenames[i])):
                makedirs(dirname(filenames[i]))
        self.start_series_triggered(len(filenames), tempdir + "/", ".rx", 6)
        # Save location of image files for other applications
        from DB import dbput
        dbput("rayonix_detector_images.filenames", repr(filenames))

    def start_series_triggered(self, n_frames, filename_base,
                               filename_suffix=".rx", number_field_width=6):
        """Acquire a series of images timed by an external hardware
    trigger signal
    filename_base: Directory part must be valid pathname on file system of
    the Rayonix computer
    filename_suffix: including the dot (.)
    number_field_width: number of digits for the filename sequence number,
    e.g. 6 for 'test000001.rx'"""
        # Make sure the directory to write the image to exists.
        from os.path import dirname
        directory = dirname(filename_base)
        makedirs(directory)
        filename_base = remote(filename_base)
        # If already in sequence acquisition mode, cancel it.
        if not self.state() == "idle":
            self.abort()
        while self.state() != "idle":
            sleep(0.05)
        # Need a valid background image before starting acquisition.
        if self.auto_bkg:
            self.update_bkg()

        if self.bulb_mode == 0 and not self.ignore_first_trigger:
            # The detector software does not save to first image, which is a bad
            # image, when using triggered frame transfer mode. However, (as of
            # Jul 2014, version 0.3.10), the detector still requires 11 trigger pulses
            # to acquire 10 images.
            # Workaround: Software-trigger the detector once after starting a series.
            self.trigger_signal_type = "Software"
        # start_series,n_frames,first_frame_number=1,integration_time=0,
        # interval_time=0,frame_trigger_type,series_trigger_type=0,
        # filename_base,filename_suffix,number_field_width
        # 0 = not triggered, 1= triggered frame transfer, 2 = bulb mode, 3 = LCLS mode
        frame_trigger_type = 2 if self.bulb_mode else 1
        self.write("start_series,%d,1,0,0,%d,0,%s,%s,%d" %
                   (n_frames, frame_trigger_type, filename_base, filename_suffix, number_field_width))
        while self.state() != "acquiring series":
            sleep(0.05)
        if self.bulb_mode == 0 and not self.ignore_first_trigger:
            self.trigger()
            # Wait for the first (suppressed) image readout to complete.
            sleep(self.readout_time)
        self.trigger_signal_type = "Opto"

    def trigger(self):
        """Software-trigger the detector"""
        self.write("trigger,0.001")
        while "busy" in self.state():
            sleep(0.05)

    def get_trigger_signal_type(self):
        """'Opto','Opto Inverted','CMOS Pulldown','CMOS Pullup',
        'CMOS Pulldown Inverted','CMOS Pullup Inverted''Software'"""
        return self.query("get_trigger_signal_type")

    def set_trigger_signal_type(self, value):
        self.write("set_trigger_signal_type,%s" % value)
        while "busy" in self.state():
            sleep(0.05)

    trigger_signal_type = property(get_trigger_signal_type, set_trigger_signal_type)

    def get_bin_factor(self):
        try:
            return int(self.query("get_bin").split(",")[0])
        except ValueError:
            return

    def set_bin_factor(self, n):
        if self.bin_factor == n:
            return
        if not self.state() == "idle":
            self.abort()
        while self.state() != "idle":
            sleep(0.05)
        self.write("set_bin," + str(n) + "," + str(n))
        # After a bin factor change it takes about 2 s before the new
        # bin factor is read back.
        t = time()
        while self.get_bin_factor() != n and time() - t < 3:
            sleep(0.1)

    bin_factor = property(get_bin_factor, set_bin_factor,
                          doc="Readout X and Y bin factor")

    readout_modes = {
        0: "Normal",
        1: "High Gain",
        2: "Low Noise",
        3: "HDR",
        4: "Turbo",
    }

    @property
    def readout_mode_numbers(self):
        d = self.readout_modes
        return dict(zip(d.values(), d.keys()))

    @property
    def readout_mode(self):
        n = self.readout_mode_number
        if n in self.readout_modes:
            mode = self.readout_modes[n]
        else:
            mode = ""
        return mode

    @readout_mode.setter
    def readout_mode(self, mode):
        if mode in self.readout_mode_numbers:
            self.readout_mode_number = self.readout_mode_numbers[mode]

    @property
    def readout_mode_number(self):
        reply = self.query("get_readout_mode")
        try:
            n = int(reply)
        except ValueError as x:
            error(f"get_readout_mode: {reply!r}: {x}")
            n = 0
        return n

    @readout_mode_number.setter
    def readout_mode_number(self, n):
        if self.readout_mode_number == n:
            return
        if not self.state() == "idle":
            self.abort()
        while self.state() != "idle":
            sleep(0.05)
        self.write(f"set_readout_mode,{n}")

    def read_bkg(self):
        """Reads a fresh the background image, which is subtracted from every image after
    readout before the correction is applied.
    """
        if not self.is_idle():
            self.abort()
        while not self.is_idle():
            sleep(0.05)
        self.write("readout,1")  # read the CCD and stores the result as background
        while not self.is_idle():
            sleep(0.05)
        self.last_read = time()

    def image_size(self):
        """Width and height of the image in pixels at the current bin mode"""
        try:
            return int(self.query("get_size").split(",")[0])
        except ValueError:
            return 0

    @staticmethod
    def filesize(bin_factor):
        """Image file size in bytes including headers
        bin_factor: 2,4,8,16"""
        image_size = 7680 / bin_factor  # MS340HS
        header_size = 4096
        image_n_bytes = 2 * image_size ** 2
        filesize = header_size + image_n_bytes
        return filesize

    def bkg_image_size(self):  # does not work with protocol v1 (timeout)
        """Width and height of the current background image in pixels.
        This value is important to know if the bin factor is changed.
        If the background image does not have the same number of pixels
        as the last read image the correction as saving to file will fail.
        At startup, the background image is empty and this value is 0.
        """
        try:
            return int(self.query("get_size_bkg").split(",")[0])
        except ValueError:
            return 0

    def update_bkg(self):
        """Updates the background image if needed, for instance after the server has
        been restarted or after the bin factor has been changed.
        """
        if not self.bkg_valid():
            self.read_bkg()

    def bkg_valid(self):
        """Does detector software have a background image for the current
        bin mode, which is subtracted from every image after readout before
        the correction is applied."""
        return self.bkg_image_size() == self.image_size()

    # By default verbose logging is enabled. Change when problem solved.
    logging = False

    @property
    def readout_time(self):
        """Estimated readout time in seconds. Changes with 'bin_factor'."""
        safetyFactor = 1
        from numpy import nan
        # Readout rate in frames per second as function of bin factor:
        readout_rate = {1: 2, 2: 10, 3: 15, 4: 25, 5: 40, 6: 60, 8: 75, 10: 120}
        bin_factor = self.bin_factor
        if bin_factor in readout_rate:
            read_time = 1.0 / readout_rate[bin_factor]
        else:
            read_time = nan
        return read_time * safetyFactor

    def get_error_logfile(self):
        """File name error messages."""
        from tempfile import gettempdir
        return gettempdir() + "/rayonix_detector_error.log"

    error_logfile = property(get_error_logfile)

    def get_logfile(self):
        """File name for transcript if verbose logging is enabled."""
        from tempfile import gettempdir
        return gettempdir() + "/rayonix_detector.log"

    logfile = property(get_logfile)


rayonix_detector = Rayonix_Detector()


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3]  # omit microseconds


def remote(pathname):
    """This converts the pathname of a file on a network file server from
    the local format to the format used on the MAR CCD computer.
    e.g. "//id14bxf/data" in Windows maps to "/net/id14bxf/data" on Unix"""
    from os.path import exists
    if not pathname:
        return pathname
    end = "/" if pathname.endswith("/") else ""
    # Try to expand a Windows drive letter to a UNC name.
    try:
        from win32wnet import WNetGetUniversalName, error
    except ImportError:
        def WNetGetUniversalName(x):
            return x

        error = RuntimeError
    # Convert "J:/anfinrud_0811/Data" to "J:\anfinrud_0811\Data".
    pathname = pathname.replace("/", "\\")
    # Convert "J:\anfinrud_0811\Data" to "\\mx340hs\data\anfinrud_0811\Data"
    try:
        pathname = WNetGetUniversalName(pathname)
    except error:
        pass
    # Convert "\\mx340hs\data\anfinrud_0811\Data" to "//mx340hs/data/anfinrud_0811/Data"
    pathname = pathname.replace("\\", "/")

    # Convert "//mx340hs/data/anfinrud_0811/Data" to "/net/mx340hs/data/anfinrud_0811/Data"
    if pathname.find("//") == 0:  # //server/share/directory/file
        parts = pathname.split("/")
        if len(parts) >= 4:
            server = parts[2]
            share = parts[3]
            path = "/".join(parts[4:])
            path = path.rstrip("/")
            if not exists("//" + server + "/" + share):
                for prefix in "/net", "/Mirror":
                    if exists(prefix + "/" + server + "/" + share):
                        pathname = prefix + "/" + server + "/" + share + "/" + path
                    if exists(prefix + "/" + server + "/home/" + share):
                        pathname = prefix + "/" + server + "/home/" + share + "/" + path

    if not pathname.endswith(end):
        pathname += end
    return pathname


def makedirs(pathname):
    """Create a directory, or make sure that the directory is world-writable"""
    # This is a workaround for problem caused by the Rayonix software running
    # under a different user id on the Rayonix control computer, compared
    # to the beamline control computer, so directories created via NFS on the
    # control machine might not be writable on the Rayonix computer.
    # E.g. user id 10660(xppopr) on "xpp-daq", versus user id 500(hsuser)
    # on "con-ics-xpp-rayonix"
    from os import makedirs, umask, chmod
    from os.path import exists
    from sys import stderr
    if exists(pathname) and not is_writable(pathname):
        try:
            chmod(pathname, 0o777)
        except Exception as details:
            stderr.write("chmod: %r: %r" % (pathname, details))
    if not exists(pathname):
        umask(0000)
        try:
            makedirs(pathname)
        except Exception as details:
            stderr.write("makedirs: %r: %r" % (pathname, details))


def is_writable(pathname):
    """Is file or folder writable?"""
    from os import access, W_OK
    return access(pathname, W_OK)


def common_top_directory(filenames):
    """filenames: list of strings"""
    from os.path import dirname
    if len(filenames) == 0:
        return []
    if len(filenames) == 1:
        return dirname(filenames[0])
    level = 1
    while level < 4:
        directory_names = []
        for pathname in filenames:
            for i in range(0, level):
                pathname = dirname(pathname)
            directory_names += [pathname]
        if all([n == directory_names[0] for n in directory_names]):
            break
        level += 1
    pathname = filenames[0]
    for i in range(0, level):
        pathname = dirname(pathname)
    return pathname


if __name__ == "__main__":  # for testing
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")
    self = rayonix_detector  # for debugging

    filenames = ["/tmp/test_%03d.mccd" % (i + 1) for i in range(0, 10)]
    print('rayonix_detector.ip_address = %r' % rayonix_detector.ip_address)
    print('')
    print('rayonix_detector.acquire_images_triggered(filenames)')
    print('rayonix_detector.bin_factor')
    print('rayonix_detector.readout_mode_number')
