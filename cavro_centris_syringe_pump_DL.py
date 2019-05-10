#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Authors: Valentyn Stadnytskyi, Philip Anfinrud, Brian Mahon, Friedrich Schotte
Date created: 12/8/2016 (original)
Date last modified: 05/25/2018


"""
__version__ = "1.3"

from time import sleep,time
from logging import debug,info,warn,error
import logging
from thread import start_new_thread

import traceback
import psutil, os
import platform #https://stackoverflow.com/questions/110362/how-can-i-find-the-current-os-in-python
p = psutil.Process(os.getpid()) #source: https://psutil.readthedocs.io/en/release-2.2.1/
# psutil.ABOVE_NORMAL_PRIORITY_CLASS
# psutil.BELOW_NORMAL_PRIORITY_CLASS
# psutil.HIGH_PRIORITY_CLASS
# psutil.IDLE_PRIORITY_CLASS
# psutil.NORMAL_PRIORITY_CLASS
# psutil.REALTIME_PRIORITYsindows':
if platform.system() == 'Windows':
    p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
elif platform.system() == 'Linux': #linux FIXIT
    p.nice(-10) # nice runs from -20 to +12, where -20 the most not nice code(highest priority)


from numpy import nan, mean, std, nanstd, asfarray, asarray, hstack, array, concatenate, delete, round, vstack, hstack, zeros, transpose, split, unique, nonzero, take, savetxt, min, max
from time import time, sleep, clock
import sys
import os.path
import struct
from pdb import pm
from time import gmtime, strftime, time
from logging import debug,info,warn,error

###These are Friedrich's libraries. 
###The number3 in the end shows that it is competable with the Python version 3. 
###However, some of them were never well tested.
if sys.version_info[0] ==3:
    from persistent_property3 import persistent_property
    from DB3 import dbput, dbget
    from module_dir3 import module_dir
    from normpath3 import normpath
else:
    from persistent_property import persistent_property
    from DB import dbput, dbget
    from module_dir import module_dir
    from normpath import normpath

from struct import pack, unpack
from timeit import Timer, timeit
import sys
###In Python 3 the thread library was renamed to _thread
if sys.version_info[0] ==3:
    from _thread import start_new_thread
else:
    from thread import start_new_thread
from datetime import datetime

from precision_sleep import precision_sleep #home-built module for accurate sleep

import msgpack
import msgpack_numpy as m
import socket

import platform
server_name = platform.node()

class server_LL(object):
    
    def __init__(self, name = ''):
        """
        to initialize an instance and create main variables
        """
        if len(name) == 0:
            self.name = 'test_communication_LL'
        else:
            self.name = name
        self.running = False
        self.network_speed = 12**6 # bytes per second
        self.client_lst = []
         
    def init_server(self):
        '''
        Proper sequence of socket server initialization
        '''
        self._set_commands()
        self.sock = self.init_socket()
        if self.sock is not None:
            self.running = True
        else:
            self.running = False

        self._start()

    def stop(self):
        self.running = False
        self.sock.close()

    def init_socket(self):
        '''
        initializes socket for listening, creates sock and bind to '' with a port somewhere between 2030 and 2050
        '''
        import socket
        ports = range(2030,2050)
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                self.port = port
                sock.listen(100)
                flag = True
            except:
                error(traceback.format_exc())
                flag = False
            if flag:
                break
            else:
                sock = None
        return sock
    
    def _set_commands(self):
        """
        Set type definition, the dictionary of command excepted by the server
        Standard supported commands:
        - "help"
        - "init"
        - "close"
        - "abort"
        - "snapshot"
        - "subscribe"
        - "task"
        """
        self.commands = {}
        self.commands['help'] = 'help'
        self.commands['init'] = 'init'
        self.commands['close'] = 'close'
        self.commands['abort'] = 'abort'
        self.commands['snapshot'] = 'snapshot'
        self.commands['subscribe'] = 'subscribe'
        self.commands['task'] = 'task'


    def _get_commands(self):
        """
        returns the dictionary with all supported commands
        """
        return self.commands
        
    def _start(self):
        '''
        creates a separete thread for server_thread function
        '''
        start_new_thread(self._run,())

    def _run(self):
        """
        runs the function _run_once in a while True loop
        """
        self.running = True
        while self.running:
            self._run_once()
        self.running = False

    def _run_once(self):
        """
        creates a listening socket.
        """
        client, addr = self.sock.accept()
        debug('Client has connected: %r,%r' %(client,addr))
        self._log_last_call(client, addr)                
        try:
            msg_in = self._receive(client)
        except:
            error(traceback.format_exc())
            msg_in = {b'command':b'unknown',b'message':b'unknown'}
        msg_out = self._receive_handler(msg_in,client)
        self._send(client,msg_out)

    def _transmit_handler(self,command = '', message = ''):
        from time import time
        res_dic  = {}
        res_dic[b'command'] = command
        res_dic[b'time'] = time()
        res_dic[b'message'] = message
        return res_dic
        
    def _receive_handler(self,msg_in,client):
        """
        the incoming msg_in has N mandatory fields:  command, message and time
        """
        from time import time
        res_dic = {}
        #the input msg has to be a dictionary. If not, ignore. FIXIT. I don't know how to do it in Python3
        debug('command received: %r' % msg_in)
        try:
            keys = msg_in.keys()
            command = msg_in[b'command']
            res_dic['command'] = command
            flag = True
            if command == b'help':
                res_dic['message'] = self.help()
            elif command == b'init':
                res_dic['message'] = self.dev_init()
            elif command == b'close':
                res_dic['message'] = self.dev_close()
            elif command == b'abort':
                res_dic['message'] = self.dev_abort()
            elif command == b'snapshot':
                res_dic['message'] = self.dev_snapshot()
            elif command == b'subscribe':
                try:
                    port = message['port']
                    err = ''
                except:
                    err = traceback.format_exc()
                if len(err) ==0:
                    res_dic['message'] = self.subscribe(client,port)
                else:
                    res_dic['message'] = 'server needs port number to subscribe'
            elif command == b'task':
                print(msg_in)
                if b'message' in msg_in.keys():
                    res_dic['message'] = self.task(msg_in[b'message'])
                else:
                    flag = False
                    err = 'task command does not have message key'
            else:
                flag = False
                err = 'the command %r is not supporte by the server' % command
            if not flag:
                debug('command is not recognized')
                res_dic['command'] = 'unknown'
                res_dic['message'] = 'The quote of the day: ... . I hope you enjoyed it.'
                res_dic['flag'] = flag
                res_dic['error'] = err
            else:
                res_dic['flag'] = flag
                res_dic['error'] = ''
        except:
            error(traceback.format_exc())
            res_dic['command'] = 'unknown'
            res_dic['message'] = 'The quote of the day: ... . I hope you enjoyed it.'
            res_dic['flag'] = True
            res_dic['error'] = ''
        res_dic[b'time'] = time()

        return res_dic

                
    def _receive(self,client):
        """
        descritpion:
        client sends 20 bytes with a number of expected package size. 
        20 bytes will encode a number up to 10**20 bytes. 
        This will be enough for any possible size of the transfer

        input: 
        client - socket client object

        output:
        unpacked data
        """
        import msgpack
        import msgpack_numpy as msg_m
        a = client.recv(20)
        length = int(a)
        debug('initial length: %r' % length)
        sleep(0.01)
        if length != 0:
            msg_in = ''.encode()
            while len(msg_in) < length:
                debug('length left (before): %r' % length)
                msg_in += client.recv(length - len(msg_in))
                debug('length left (after): %r' % length)
                sleep(0.01)
        else:
            msg_in = ''
        return msgpack.unpackb(msg_in, object_hook=msg_m.decode)
    
    def _send(self,client,msg_out):
        """
        descrition:
        uses msgpack to serialize data and sends it to the client
        """
        debug('command send %r' % msg_out)
        msg = msgpack.packb(msg_out, default=m.encode)
        length = str(len(msg))
        if len(length)!=20:
            length = '0'*(20-len(length)) + length
        try:
            client.sendall(length.encode())
            client.sendall(msg)
            flag = True
        except:
            error(traceback.format_exc())
            flag = False
        return flag

    def _connect(self,ip_address,port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.settimeout(10)
            server.connect((ip_address , port))
            server.settimeout(None)
            debug("Connection success!")
        except:
            error('%r' %(traceback.format_exc()))
            server = None
        return server

    def _transmit(self,command = '', message = '' ,ip_address = '127.0.0.1',port = 2031):
        msg_out = self._transmit_handler(command = command, message = message)
        server = self._connect(ip_address = ip_address,port = port)
        flag = self._send(server,msg_out)
        self.response_arg = self._receive(server)
        self._server_close(server)
        return self.response_arg

    def _server_close(self,server):
        server.close() 
        return server

    def _log_last_call(self,client,addr):
        self.last_call = [addr,client.getpeername()]

#***************************************************
#*** wrappers for basic response functions *********
#***************************************************
        
    def subscribe(self,port,client):
        self.subscribe_lst = [client.getpeername()[0],port]
        msg = 'subscribe command received' + str(self.subscribe_lst)
        debug(msg)
        return msg

    def help(self):
        debug('help command received')


#***************************************************
#*** wrappers for basic response functions *********
#***************************************************
    def help(self):
        msg = {}
        msg['server name']= self.name
        msg['commands'] = self.commands
        msg['dev_indicators'] = device.indicators.keys()
        msg['dev_controls'] = device.controls.keys()
        debug(msg)
        return msg
    
    def dev_init(self):
        msg = 'init command received'
        device.init()
        debug(msg)
        return msg
    
    def dev_close(self):
        msg = 'close command received'
        debug(msg)
        return msg

    def dev_abort(self):
        msg = 'abort command received'
        debug(msg)
        return msg

    def dev_snapshot(self):
        msg = 'snapshot command received'
        debug(msg)
        msg = device.snapshot()
        return msg


    
    def dev_task(self,msg):
        msg = 'task command received: %r' % msg
        debug(msg)
        return msg

    def dev_get_device_indicators(self, indicator = {}):
        response = {}
        if 'all' in indicator.keys():
            response = device.indicators
        else:
            for key in indicator.keys():
                if key in device.indicators.keys():
                    response[key] = device.indicators[key]
        return response

    def dev_set_device_indicators(self, control = {}):
        for key in controll.keys():
            if key in device.controlls.keys():
                device.controlls[key] = controll[key]

    def dev_get_device_controls(self, control = {}):
        response = {}
        if 'all' in control.keys():
            response = device.controls
        else:
            for key in controll.keys():
                if key in device.controls.keys():
                    response[key] = device.controls[key]
        return response

    def dev_set_device_controls(self, control = {}):
        for key in control.keys():
            if key in device.controls.keys():
                device.controls[key] = control[key]

class client_LL(object):
    
    def __init__(self, name = ''):
        """
        to initialize an instance and create main variables
        """
        if len(name) == 0:
            self.name = 'test_client_LL'
        else:
            self.name = name
        self.running = False
        self.network_speed = 12**6 # bytes per second
        self.client_lst = []
         
    def init_server(self):
        '''
        Proper sequence of socket server initialization
        '''
        self._set_commands()
        if self.sock is not None:
            self.running = True
        else:
            self.running = False

    def stop(self):
        self.running = False
        self.sock.close()
    
    def _set_commands(self):
        """
        Set type definition, the dictionary of command excepted by the server
        Standard supported commands:
        - "help"
        - "init"
        - "close"
        - "abort"
        - "snapshot"
        - "subscribe"
        - "task"
        """
        self.commands = {}
        self.commands['help'] = 'help'
        self.commands['init'] = 'init'
        self.commands['close'] = 'close'
        self.commands['abort'] = 'abort'
        self.commands['snapshot'] = 'snapshot'
        self.commands['subscribe'] = 'subscribe'
        self.commands['task'] = 'task'


    def _get_commands(self):
        """
        returns the dictionary with all supported commands
        """
        return self.commands

    def _transmit_handler(self,command = '', message = ''):
        from time import time
        res_dic  = {}
        res_dic[b'command'] = command
        res_dic[b'time'] = time()
        res_dic[b'message'] = message
        return res_dic
        
    

                
    def _receive(self,client):
        """
        descritpion:
        client sends 20 bytes with a number of expected package size. 
        20 bytes will encode a number up to 10**20 bytes. 
        This will be enough for any possible size of the transfer

        input: 
        client - socket client object

        output:
        unpacked data
        """
        import msgpack
        import msgpack_numpy as msg_m
        a = client.recv(20)
        length = int(a)
        sleep(0.01)
        if length != 0:
            msg_in = ''.encode()
            while len(msg_in) < length:
                msg_in += client.recv(length - len(msg_in))
                sleep(0.01)
        else:
            msg_in = ''
        return msgpack.unpackb(msg_in, object_hook=msg_m.decode)
    
    def _send(self,client,msg_out):
        """
        descrition:
        uses msgpack to serialize data and sends it to the client
        """
        debug('command send %r' % msg_out)
        msg = msgpack.packb(msg_out, default=m.encode)
        length = str(len(msg))
        if len(length)!=20:
            length = '0'*(20-len(length)) + length
        try:
            client.sendall(length.encode())
            client.sendall(msg)
            flag = True
        except:
            error(traceback.format_exc())
            flag = False
        return flag

    def _connect(self,ip_address,port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.settimeout(10)
            server.connect((ip_address , port))
            server.settimeout(None)
            debug("Connection success!")
        except:
            error('%r' %(traceback.format_exc()))
            server = None
        return server

    def _transmit(self,command = '', message = '' ,ip_address = '127.0.0.1',port = 2031):
        msg_out = self._transmit_handler(command = command, message = message)
        server = self._connect(ip_address = ip_address,port = port)
        flag = self._send(server,msg_out)
        self.response_arg = self._receive(server)
        self._server_close(server)
        return self.response_arg

    def _server_close(self,server):
        server.close() 
        return server

    def _log_last_call(self,client,addr):
        self.last_call = [addr,client.getpeername()]

#***************************************************
#*** wrappers for basic response functions *********
#***************************************************
        
    def subscribe(self,port,client):
        self.subscribe_lst = [client.getpeername()[0],port]
        msg = 'subscribe command received' + str(self.subscribe_lst)
        debug(msg)
        return msg


class syringe_pump_DL(object):
    
    def __init__(self):
        self.name = 'syringe_pump_DL'

    def init(self):
        from cavro_centris_syringe_pump_LL import driver
        driver.discover()

        self.indicators = {}
        self.controls = {}
        self.indicators['positions'] = {}
        self.indicators['valves'] = {}

    def help(self):
        debug('help command received')

    def snapshot(self):
        response = {}
        response['indicators'] = self.indicators
        response['controls'] = self.controls
        from numpy import random
        response['data'] = random.rand(2,100000)
        return response
        
    def update_indictors(self):
        from cavro_centris_syringe_pump_LL import driver
        self.indicators['positions'] = driver.positions(pids = [1,2,3,4])
        self.indicators['valves'] = driver.valve_get(pids = [1,2,3,4])


    def run_once(self):
        from time import sleep
        while True:
            self.update_indictors()
            sleep(1)

    def run(self):
        start_new_thread(self.run_once,())
        
        
server = server_LL(name = 'suringe_pump_server_DL')
client = client_LL(name = 'suringe_pump_client_DL')
from cavro_centris_syringe_pump_LL import driver
device = syringe_pump_DL()                       
server.init_server()
    
if __name__ == "__main__":
    from tempfile import gettempdir
    

    logging.basicConfig(#filename=gettempdir()+'/suringe_pump_DL.log',
                                        level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

    print('driver.discover()')
    print('driver.prime(1)')
    print('driver.prime(3)')
    
