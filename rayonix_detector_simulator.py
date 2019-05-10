#!/bin/env python
"""Friedrich Schotte, Jun 17, 2016 - Aug 14, 2017
"""
__version__ = "1.2.2" # Windows UNC pathnames, normpath

from logging import debug,info,warn,error
 
class Rayonix_Detector(object):
    from persistent_property import persistent_property
    bin_factor = persistent_property("bin_factor",2)
    npixels = 7680
    bkg_image_size = 0
    external_trigger = persistent_property("external_trigger",False)
    # Simulate trigger coming at this interval (in seconds).
    nominal_trigger_period = persistent_property("nominal_trigger_period",1.0)
    last_filename = ""
    # listen port number of this server script
    port = persistent_property("port",2222)
    trigger_times = []
    
    @property
    def state(self):
        if self.acquiring_series: return 0x02000000
        return 0
    
    @property
    def image_size(self):
        return self.npixels/self.bin_factor

    def handle_trigger(self):
        if self.acquiring_series:
            if not self.series_triggered:
                info("rayonix: Ignoring first trigger")
                self.series_triggered = True
            else: self.acquire_image()
        self.register_trigger_time()

    def register_trigger_time(self):
        from time import time
        self.trigger_times = self.trigger_times[-9:]+[time()]

    @property
    def measured_trigger_period(self):
        from numpy import nan
        from time import time
        self.monitoring_trigger = True
        t = self.trigger_times
        if len(t) >= 2 and time()-t[-1] <= t[-1]-t[-2]+5:
            T = t[-1]-t[-2]
        else: T = nan
        return T

    def get_trigger_period(self):
        if self.external_trigger: return self.measured_trigger_period
        else: return self.nominal_trigger_period
    def set_trigger_period(self,value):
        self.nominal_trigger_period = value
    trigger_period = property(get_trigger_period,set_trigger_period)       

    def acquire_image(self):
        from numimage import numimage
        from numpy import uint16
        from os.path import basename
        from thread import start_new_thread
        if self.acquiring_series:
            filename = "%s%0*d%s" % \
                (self.filename_base,self.number_field_width,
                 self.frame_number,self.filename_suffix)
            I = numimage((self.image_size,self.image_size),dtype=uint16,
                pixelsize=self.pixelsize)
            ##info("rayonix: Saving image %r %r" % (basename(filename),I.shape))
            start_new_thread(I.save,(filename,))
            self.last_filename = filename
            self.frame_number += 1
        if self.frame_number > self.last_frame_number:
            self.acquiring_series = False

    @property
    def pixelsize(self):
        pixelsize = 0.02*self.bin_factor
        return pixelsize

    def acquire_series(self):
        if self.external_trigger: self.acquire_series_on_trigger()
        self.acquire_series_on_timer()

    def acquire_series_on_trigger(self):
        from time import sleep
        self.monitoring_trigger = True
        while self.acquiring_series: sleep(0.05)

    __monitoring_trigger__ = False
    
    def get_monitoring_trigger(self):
        return self.__monitoring_trigger__
    def set_monitoring_trigger(self,value):
        from CA import camonitor,camonitor_clear
        if value: camonitor(self.trigger_PV,callback=self.trigger_callback)
        else: camonitor_clear(self.trigger_PV,callback=self.trigger_callback)
        self.__monitoring_trigger__ = value
    monitoring_trigger = property(get_monitoring_trigger,set_monitoring_trigger)

    __trigger_PV__ = persistent_property("trigger_PV","NIH:TIMING.registers.xdet_state")

    def get_trigger_PV(self): return self.__trigger_PV__
    def set_trigger_PV(self,value):
        if value != self.__trigger_PV__:
            from CA import camonitor,camonitor_clear
            camonitor_clear(self.__trigger_PV__,callback=self.trigger_callback)
            self.trigger_times = []
            self.__trigger_PV__ = value
            camonitor(self.__trigger_PV__,callback=self.trigger_callback)
    trigger_PV = property(get_trigger_PV,set_trigger_PV)

    @property
    def trigger_PV_OK(self):
        from CA import caget
        return caget(self.trigger_PV) is not None
    
    def trigger_callback(self,PV_name,value,formatted_value):
        ##info("rayonix: trigger_callback: %s=%s(%s)" % (PV_name,value,formatted_value))
        if value == 1: self.handle_trigger()

    def acquire_series_on_timer(self):
        from time import sleep
        sleep(self.trigger_period)
        while self.acquiring_series:
            self.handle_trigger()
            sleep(self.trigger_period)

    def process_command(self,query):
        """Process a command"""
        if query == "get_state": return str(self.state)
        elif query.startswith("start_series,"):
            start_series,n_frames,first_frame_number,integration_time,\
                interval_time,frame_trigger_type,series_trigger_type,\
                filename_base,filename_suffix,number_field_width \
                = query.split(",")
            self.start_series(int(n_frames),int(first_frame_number),
                float(integration_time),float(interval_time),
                int(frame_trigger_type),int(series_trigger_type),
                filename_base,filename_suffix,int(number_field_width))
        elif query == "get_bin":
            return str(self.bin_factor)+","+str(self.bin_factor)
        elif query.startswith("set_bin,"):
            set_bin,bin_factor,bin_factor = query.split(",")
            self.bin_factor = int(bin_factor)
        elif query == "get_size":
            return str(self.image_size)+","+str(self.image_size)
        elif query == "get_size_bkg":
            return str(self.bkg_image_size)+","+str(self.bkg_image_size)
        elif query.startswith("trigger,"): self.handle_trigger()
        elif query == "abort": self.abort()

    def start_series(self,n_frames=None,first_frame_number=None,
        integration_time=None,interval_time=None,frame_trigger_type=None,
        series_trigger_type=None,
        filename_base=None,filename_suffix=None,number_field_width=None):
        """Start acqisition of image series."""
        from normpath import normpath
        if n_frames is not None:
            self.n_frames = n_frames
        if first_frame_number is not None:
            self.first_frame_number = first_frame_number
        if filename_base is not None:
            self.filename_base = normpath(filename_base)
        if filename_suffix is not None:
            self.filename_suffix = filename_suffix
        if number_field_width is not None:
            self.number_field_width = number_field_width
        
        info("rayonix: Starting series of %d images..." % self.n_frames)
        self.frame_number = self.first_frame_number
        self.acquiring_series = True
        self.series_triggered = False # trigger pulse seen?
        from thread import start_new_thread
        start_new_thread(self.acquire_series,())

    n_frames = persistent_property("n_frames",10)
    first_frame_number = persistent_property("first_frame_number",0)
    filename_base = persistent_property("filename_base","/tmp/")
    filename_suffix = persistent_property("filename_suffix",".rx")
    number_field_width = persistent_property("number_field_width",6)
    
    frame_number = 0
    acquiring_series = False
    series_triggered = False

    @property
    def last_frame_number(self):
        return self.first_frame_number+self.n_frames-1

    def abort(self):
        """End acqisition of image series."""
        info("rayonix: Aborting acqisition.")
        self.acquiring_series = False

    def get_acquiring(self):
        """Is image series acqisition in progress?"""
        return self.acquiring_series
    def set_acquiring(self,value):
        if value: self.start_series()
        else: self.abort()
    acquiring = property(get_acquiring,set_acquiring)

    @property
    def readout_time(self):
        """Estimated readout time in seconds. Changes with 'bin_factor'."""
        return self.readout_time_of_bin_factor(self.bin_factor)

    def readout_time_of_bin_factor(self,bin_factor):
        """Estimated readout time in seconds as function of bin factor."""
        safetyFactor = 1
        from numpy import nan
        # Readout rate in frames per second as function of bin factor:
        readout_rate = {1: 2, 2: 10, 3: 15, 4: 25, 5: 40, 6: 60, 8: 75, 10: 120}
        if bin_factor in readout_rate: read_time = 1.0/readout_rate[bin_factor]
        else: read_time = nan
        return read_time*safetyFactor

    def get_server_running(self):
        return getattr(self.server,"active",False)
    def set_server_running(self,value):
        if self.server_running != value:
            if value: self.start_server()
            else: self.stop_server()
    server_running = property(get_server_running,set_server_running)
    
    server = None

    def start_server(self):
        # make a threaded server, listen/handle clients forever
        try:
            self.server = self.ThreadingTCPServer(("",self.port),self.ClientHandler)
            self.server.active = True
            info("rayonix: server version %s started, listening on port %d." % (__version__,self.port))
            from threading import Thread
            self.thread = Thread(target=self.run_server)
            self.thread.start() # Stop with: "self.server.shutdown()"
        except Exception,msg: error("rayonix: start_server: %r" % msg)

    def stop_server(self):
        if getattr(self.server,"active",False):
            self.server.server_close()
            self.server.active = False

    def run_server(self):
        try: self.server.serve_forever()
        except Exception,msg: info("rayonix: server: %s" % msg)
        info("rayonix: server shutting down")

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
             info("rayonix: accepted connection from "+self.client_address[0])
             import socket
             input_queue = ""
             while self.server.active:
                 # Commands from a client are not necessarily received as one packet
                 # but each command is terminated by a newline character.
                 # If 'recv' returns an empty string it means client closed the
                 # connection.
                 while input_queue.find("\n") == -1:
                     self.request.settimeout(1.0)
                     received = ""
                     while self.server.active:
                         try: received = self.request.recv(2*1024*1024)
                         except socket.timeout: continue
                         except Exception,x: error("rayonix: %r %r" % (x,str(x)))
                         if received == "": info("rayonix: client disconnected")
                         break
                     if received == "": break
                     input_queue += received
                 if input_queue == "": break
                 if input_queue.find("\n") != -1:
                     end = input_queue.index("\n")
                     query = input_queue[0:end]
                     input_queue = input_queue[end+1:]
                 else: query = input_queue; input_queue = ""
                 query = query.strip("\r ")
                 error("rayonix: evaluating query: '%s'" % query)
                 try: reply = det.process_command(query)
                 except Exception,x: error("rayonix: %r %r" % (x,str(x))); reply = ""
                 if reply:
                     reply = reply.replace("\n","") # "\n" = end of reply
                     reply += "\n"
                     info("rayonix: sending reply: "+repr(reply))
                     self.request.sendall(reply)
             info("rayonix: closing connection to "+self.client_address[0])
             self.request.close()
        
det = Rayonix_Detector()


def timestamp():
    """Current date and time as formatted ASCCI text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microseconds


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = det # for debugging
    from CA import camonitor,camonitor_clear,caget
    ##print('camonitor(self.trigger_PV,callback=self.trigger_callback)')
    ##print('camonitor_clear(self.trigger_PV,callback=self.trigger_callback)')
    ##print('self.acquiring = True')
    print('self.trigger_PV = %r' % self.trigger_PV)
    print('self.trigger_PV_OK')
    print('self.trigger_period')
    print('det.server_running = True')
