#!/usr/bin/env python
"""
Prosilica GigE CCD cameras.
Author: Friedrich Schotte and Valentyn Stadnytskyi
Date created: 2017-04-13
Date last modified: 2018-10-16

based on original GigE_camera_server by Friedrich Schotte

0.0.1 - original GigE_camera_server by Friedrich Schotte

Configuration:
    from DB import dbset
    dbset("GigE_camera.WideFieldCamera.camera.IP_addr","pico3.niddk.nih.gov")
    dbset("GigE_camera.MicroscopeCamera.camera.IP_addr","pico14.niddk.nih.gov")
    dbset("GigE_camera.WideFieldCamera.ip_address","pico20.niddk.nih.gov:2001")
    dbset("GigE_camera.MicroscopeCamera.ip_address","pico20.niddk.nih.gov:2002")
"""
__version__ = "0.0.1"

from GigE_camera import GigE_camera

class Camera(GigE_camera):
    from persistent_property import persistent_property
    IP_addr = persistent_property("GigE_camera.{name}.camera.IP_addr",
        "pico3.niddk.nih.gov")
    use_multicast = persistent_property("GigE_camera.{name}.use_multicast",False)
    buffer_size = 10
    
    def __init__(self,name):
        GigE_camera.__init__(self)
        self.name = name
        self.frame_counts = []
        self.images = []
        self.monitoring = False
        self.last_frame_count = -1
        self.acquisition_requested = False
        self.start_monitoring()
        self.filenames = {}

    def get_acquiring(self):
        return self.acquisition_started
    def set_acquiring(self,value):
        self.acquisition_requested = value
    acquiring = property(get_acquiring,set_acquiring)
 
    def start_monitoring(self):
        self.monitoring = True
        from thread import start_new_thread
        start_new_thread(self.monitor,())

    def monitor(self):
        from time import sleep
        # This thread is the control thread.
        # The first threat to call "resume" becomes the control thread.
        # Any operation that change the state of the PvAPI library
        # coming from other threads are ignored.
        ##self.resume()
        
        while self.monitoring:
            if self.acquisition_requested:
                while not "started" in self.state:
                    self.start()
                    sleep(1)
                    info("%s: %s" % (self.IP_addr,self.state))
                while not self.has_image or self.timestamp == 0:
                    sleep(0.5)
                    info("%s" % self.state)
                while self.frame_count == self.last_frame_count:
                    if self.auto_resume: self.resume()
                    sleep(0.01)
                self.save_current_image()
                self.last_frame_count = self.frame_count
                self.images = self.images[-(self.buffer_size-1):]+[self.rgb_data]
                self.frame_counts = self.frame_counts[-(self.buffer_size-1):]+[self.frame_count]
            else: self.stop(); sleep(0.5)

    def acquire_sequence(self,framecounts,filenames):
        """Save a series of images"""
        for framecount,filename in zip(framecounts,filenames):
            if not framecount in self.filenames:
                self.filenames[framecount] = []
                if not filename in self.filenames[framecount]:
                    self.filenames[framecount] += [filename]

    def save_current_image(self):
        """Check whether the last acquired image needs to be saved
        and save it."""
        frame_count = self.frame_count
        if frame_count in self.filenames:
            for filename in self.filenames[frame_count]:
                self.save_image(self.rgb_data,filename)
            del self.filenames[frame_count]

    def save_image(self,rgb_data,filename):
        """Saves rgb_data in a file
        """
        from thread import start_new_thread
        from PIL import Image
        image = Image.new('RGB',(self.width,self.height))
        #image.fromstring(rgb_data)
        image.frombytes(rgb_data)
        image = self.rotated_image(image)
        from os import makedirs; from os.path import dirname,exists
        if not exists(dirname(filename)): makedirs(dirname(filename))
        info("Saving %r" % filename)
        start_new_thread(image.save,(filename,))

    # in degrees counter-clockwise
    orientation = persistent_property("{name}.Orientation",0)

    def rotated_image(self,image):
        """image: PIL image object"""
        return image.rotate(self.orientation)
        
camera = Camera("WideFieldCamera")


# server's listen port number
ip_address = "pico20.niddk.nih.gov:2000"

class Server(object):
    @property
    def name(self): return camera.name

    from thread import allocate_lock
    lock = allocate_lock()
    
    from persistent_property import persistent_property
    ip_address = persistent_property("GigE_camera.{name}.ip_address","pico20.niddk.nih.gov:2000")

    def get_address(self):
        return self.ip_address.split(":")[0]
    def set_address(self,value):
        self.ip_address = value+":"+str(self.port)
    address = property(get_address,set_address)

    def get_port(self):
        if ":" in self.ip_address: port = self.ip_address.split(":")[-1]
        else: port = "2000"
        try: port = int(port)
        except: port = 2000
        return port
    def set_port(self,value):
        self.ip_address = self.address+":"+str(value)
    port = property(get_port,set_port)

    def get_running(self):
        return self.server is not None
    def set_running(self,value):
        if self.running != value:
            if value: self.start()
            else: self.stop()
    running = property(get_running,set_running)
    
    server = None

    def start(self):
        """make a threaded server, listen/handle clients forever"""
        import socket
        for self.port in range(self.port,self.port+10):
            try:
                self.server = self.ThreadingTCPServer(("",self.port),self.ClientHandler)
                break
            except socket.error,msg: warn("server port %s: %s" % (self.port,msg))

        self.address = local_ip_address()
        info("server version %s, listening on %s." % (__version__,self.ip_address))

        from threading import Thread
        self.thread = Thread(target=self.run)
        self.thread.start() # Stop with: "self.server.shutdown()"

    def run(self):
        try: self.server.serve_forever()
        except Exception,msg: info("server: %s" % msg)
        info("server shutting down")

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
            self.server = None

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
             info("accepted connection from "+self.client_address[0])
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
                     if received == "": info("client disconnected"); break
                     ##debug("received %8d+%8d = %8d bytes" % (len(input_queue),
                     ##   len(received),len(input_queue)+len(received)))
                     input_queue += received
                 if input_queue == "": break
                 if input_queue.find("\n") != -1:
                     end = input_queue.index("\n")
                     query = input_queue[0:end]
                     input_queue = input_queue[end+1:]
                 else: query = input_queue; input_queue = ""
                 query = query.strip("\r ")
                 from numpy import array,nan
                 if query.find("=") >= 0:
                     debug("executing command: '%s'" % query)
                     try:
                         with Server.lock: exec(query)
                     except Exception,x: error("%r %r" % (x,str(x)))
                 else:
                     debug("evaluating query: '%s'" % query)
                     try:
                         with Server.lock: reply = eval(query)
                     except Exception,x:
                         error("%r %r" % (x,str(x))); reply = str(x)
                     if reply is None: reply = ""
                     elif type(reply) == str and len(reply) > 1024:
                         pass # do not waste time reformatting a string
                     elif reply is not None:
                         try: reply = repr(reply)
                         except: reply = str(reply)
                         reply = reply.replace("\n","") # "\n" = end of reply
                         reply += "\n"
                         debug("sending reply: "+repr(reply))
                     self.request.sendall(reply)
             info("closing connection to "+self.client_address[0])
             self.request.close()

server = Server()

def local_ip_address():
    """IP address of the local network interface as string in dot notation"""
    # Unfortunately, Python has no platform-indepdent function to find
    # the IP address of the local machine.
    # As a work-around let us pretend we want to send a UDP datagram to a
    # non existing external IP address.
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("129.166.233.186",1024))
    except socket.error: return "127.0.0.1" # Network is unreachable
    # This code does not geneate any network traffic, because UDP is not
    # a connection-orientation protocol.
    # Now, Python can tell us what would be thet "source address" of the packets
    # if we would sent a packet (but we won't actally sent a packet).
    address,port = s.getsockname()
    return address

def start(name):
    camera.name = name
    ##camera.acquiring = True # needed
    server.running = True

def run(name):
    """Run as a stand-alone server program"""
    from time import sleep
    start(name)
    while True: sleep(1)

def set_defaults():
    from DB import dbset
    dbset("GigE_camera.WideFieldCamera.camera.IP_addr","pico3.niddk.nih.gov")
    dbset("GigE_camera.MicroscopeCamera.camera.IP_addr","pico14.niddk.nih.gov")
    dbset("GigE_camera.WideFieldCamera.ip_address","pico20.niddk.nih.gov:2001")
    dbset("GigE_camera.MicroscopeCamera.ip_address","pico20.niddk.nih.gov:2002")

def debug(message):
    """Generate message without duplicates"""
    from logging import debug
    if message != last_message["debug"]: debug(message)
    last_message["debug"] = message

def info(message):
    """Generate message without duplicates"""
    from logging import info
    if message != last_message["info"]: info(message)
    last_message["info"] = message

def warn(message):
    """Generate message without duplicates"""
    from logging import warn
    if message != last_message["warn"]: warn(message)
    last_message["warn"] = message

def error(message):
    """Generate message without duplicates"""
    from logging import error
    if message != last_message["error"]: error(message)
    last_message["error"] = message
    
last_message = {"debug":"","info":"","warn":"","error":""}

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,format="%(asctime)s: %(message)s")
    from sys import argv
    if len(argv) > 1: run(argv[1])
    self = camera # for debugging
    from tempfile import gettempdir
    dir = gettempdir()+"/test"
    frame_counts = range(0,20)
    filenames = [dir+"/%06d.tif" % i for i in frame_counts]
    print('camera.acquire_sequence(frame_counts,filenames)')
    print('camera.acquiring = True')
    print('start("WideFieldCamera")')
