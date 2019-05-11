from __future__ import with_statement

import socket

class TCP_Server(object):
  """This is to communicate with a server over Ethernet using TCP/IP."""

  def __init__(self,ip_address):
    """ip_address may be given as address:port. If :port is omitted, port
    number 2000 is assumed."""
    from thread import allocate_lock
    self.timeout = 1.0
    object.__init__(self)
    if ip_address.find(":") >= 0:
      self.ip_address = ip_address.split(":")[0]
      self.port = int(ip_address.split(":")[1])
    else: self.ip_address = ip_address; self.port = 2000
    self.connection = None # network connection
    # This is to make the query method multi-thread safe.
    self.lock = allocate_lock()

  def __repr__(self):
    return self.__class__.__name__+"('"+self.ip_address+":"+str(self.port)+"')"

  def write(self,command):
    """Send a command that does not generate a reply"""
    with self.lock: # Allow only one thread at a time inside this function.
      for retry in 1,2:
        self.connect()
        if not self.connected(): return
        try:
          self.connection.sendall(command+"\n")
        except socket.error: # in case of  "Connection reset by peer"...
          print "send: lost connection to '"+self.ip_address+"'"
          self.disconnect()
          continue
        # Make sure that the connection is still "alive".
        self.connection.settimeout(0.0001)
        try:
          t = self.connection.recv(1024)
          if len(t) == 0:
            print "send check: '"+self.ip_address+"' closed connection"
            self.disconnect()
            continue
          if len(t) > 0:
            print "write: command '%s' generated unexpected reply %r" % (command,t)
            self.disconnect()
            continue
        except socket.timeout: pass
        except socket.error: # in case of "Connection reset by peer"
          print "send check: lost connection to '"+self.ip_address+"'"
          self.diconnect()
          continue
        self.connection.settimeout(self.timeout)
        return

  def query(self,command):
    """Send a command that generates a reply, and return the reply."""
    with self.lock: # Allow only one thread at a time inside this function.
      for retries in 1,2:
        self.connect()
        if not self.connected(): return ""
        try: self.connection.sendall(command+"\n")
        except socket.error:  # in case of "Connection reset by peer"...
          print "send: lost connection to '"+self.ip_address
          self.disconnect()
          continue
        try:
          reply = self.connection.recv(4096)
          ##print "received "+str(len(reply))+" bytes"
          if len(reply) == 0:
            print "receive: '"+self.ip_address+"' closed connection."
            self.disconnect()
            continue
          while reply.find("\n") == -1:
            t = self.connection.recv(4096)
            ##print "received "+str(len(t))+" bytes"
            if len(t) == 0:
              print "receive: '"+self.ip_address+"' closed connection"
              self.disconnect()
              return reply
            reply += t          
          reply = reply.strip("\n")
          return reply
        except socket.timeout:
          print "receive: connection to '"+self.ip_address+"' timed out"
          self.disconnect()
          continue
        except socket.error:
          print "receive: lost connection to '"+self.ip_address+"'"
          self.disconnect()
          continue
      return ""

  def connect(self):
    "Establishes a TCP connection, if not already established"
    self.flush() # Make sure the receiving queue is empty.
    if not self.connected():
      self.connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      self.connection.settimeout(self.timeout)
      try: self.connection.connect((self.ip_address,self.port))
      except socket.error:
        self.connection = None
        print "Failed to connect to '"+self.ip_address+"', port",self.port
    if self.connection: self.connection.settimeout(self.timeout)

  def connected(self):
    "Return True if the connection is establisched, False otherwise"
    if self.connection == None: return False
    try: self.connection.getpeername()
    except socket.error: return False
    return True

  def flush(self):
    "Flush the receiving queue"
    if not self.connected(): return
    try:
      self.connection.settimeout(0.000001)
      t = self.connection.recv(1024)
      if len(t) == 0:
        print "flush: '"+self.ip_address+"' closed connection"
        self.disconnect()
        return
      while len(t) > 0:
        t = self.connection.recv(1024)
        if len(t) == 0:
          print "flush: '"+self.ip_address+"' closed connection"
          self.disconnect()
          return
    except socket.timeout: pass
    except socket.error: # in case of "Connection reset by peer"
      print "flush: lost connection to '"+self.ip_address+"'"
      self.disconnect()
      return
    self.connection.settimeout(self.timeout)

  def disconnect(self):
    "Shuts down the current TCP connection"
    if self.connection != None:
      self.connection.close()
      self.connection = None

  def reconnect(self):
    self.disconnect(); self.connect();

class subsystem:
    def __init__(self,server,name=""):
        self.__server__ = server
        self.__name__ = name
        
    def __getattr__(self,attr):
        ##print "subsystem.__getattr__(%r)" % attr
        if attr == "__members__": return self.__getmembers__()
        if self.__dict__.has_key(attr): return self.__dict__[attr]
        if attr.startswith("__") or attr.endswith("__"):
            raise AttributeError, "'subsystem' has no attribute '%s'" % attr
        if self.__name__: name = self.__name__+"."+attr
        else: name = attr
        return subsystem(self.__server__,name)

    def __setattr__(self,attr,val):
        ##print "subsystem.__setattr__(%r,%r)" % (attr,val)
        if attr.startswith("__") or attr.endswith("__"):
            self.__dict__[attr] = val
            return
        if not hasattr(self,"__server__"): return
        if not hasattr(self,"__name__"): return

        if self.__name__: name = self.__name__+"."+attr
        else: name = attr
        val = str(val)
        ##print "write","%s=%s" % (name,val)
        self.__server__.write("%s=%s" % (name,val))

    def __getmembers__(self):
        if not hasattr(self,"__server__"): return []
        if not hasattr(self,"__name__"): return []
        names = self.__server__.query(self.__name__).split("\n")
        while "" in names: names.remove("")
        return names

    def __getsubmembers__(self,name):
        if not hasattr(self,"__server__"): return []
        if not hasattr(self,"__name__"): return []
        if self.__name__: name = self.__name__+"."+name
        ##print "__getsubmembers__: query %r" % name
        names = self.__server__.query(name).split("\n")
        while "" in names: names.remove("")
        return names

    def __content__(self):
        members = self.__getmembers__()
        if len(members) > 1: return self
        if len(members) == 1:
            member = members[0]
            ##print "member %r" % member
            submembers = self.__getsubmembers__(member)
            ##print "submembers %r" % submembers
            if len(submembers) > 0: return self
        return self.__server__.query(self.__name__)

    def __repr__(self):
        ##print "subsystem.__repr__()"
        content = self.__content__()
        if type(content) == str: return repr(content)
        return "subsystem(%r,%r)" % (self.__server__,self.__name__)

    def __str__(self):
        content = self.__content__()
        if type(content) == str: return content
        return self.__server__.query(self.__name__)

    def __float__(self):
        from numpy import nan
        try: return float(str(self))
        except: return nan

    def __int__(self):
        try: return int(str(self))
        except: return 0

server = TCP_Server("id14timing.cars.aps.anl.gov:2000")        

timing_system = subsystem(server)
