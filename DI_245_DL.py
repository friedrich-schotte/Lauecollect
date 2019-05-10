#!/usr/bin/env python
"""
Four-channel USB Voltage and Thermocouple DAQ,
Resolution: 14-bit
Sampleling rate: 8000 Hz max
Range: +/- 50 V to +/- 10 mV, in 3 steps per decade (1,2.5,5)
build in cold junction compensation (CJC) for thermocouples

Reference:
DI-245 Communication Protocol
www.dataq.com/resources/pdfs/support_articles/DI-245-protocol.pdf

COM Port Communication Settings:
Baud rate: 115200, Data bits: 8, Stop bits: 1, Parity: none

Installing the DI-245 driver package and connecting DI-245 hardware to the
host computer’s USB port results in a COM port being hooked by the operating
system and assigned to the DI-245 device.

Multiple DI-245 devices may be connected to the same PC without additional
driver installations, which results in a unique COM port number assignment to
each by the operating system.

The DI-245 employs a simple ASCII character command set that allows complete
control of the instrument.

Long commands and arguments (longer than two characters) are separated by a
space character (0x20), and each long command string must be terminated with
a carriage return character (x0D). Long commands do not echo until the 0x0D
character is received.

Short commands (2 characters or less) are preceded with a null character
(0x00), which is not echoed, but each command character is echoed as it is
sent.

<0x00>command<(0x20)<argument1>(0x20)<agrument2>(0x0D)>

For example, the command "\0A1" generates the following response: "A12450"

Commands:
"\0A1"

      Returns device name: "2450"
"chn 0 5120\r" Enable analog channel 0 to measure an N type TC as the first scan list member
"chn 1 514\r"  Enable analog channel 2 to measure +/-100 mV as the second scan list member
"chn 2 3331\r" Enable analog channel 3 to measure +/-1 V as the third scan list member
"xrate 1871 10\r" Burst rate is 10 Hz,
               sampling frequency SF=79, averaging frequency AF=7
               SF+AF*256 = 79+7*256 = 1971, burst rate B = 8000/((SF+1)*(AF+3))
"\0S1"         Start the scanning processes, causes the DI-245 to respond with a continuous binary
               stream of one 16-bit signed integers per enabled measurement.
               The stream sequence repeats until data acquisition is halted by the stop
               command.
"\0S0"         Stop the scanning processes

Valentyn Stadnytskyi Nov 2017
"""

from numpy import concatenate,zeros,mean,std,uint16, nan
#from CAServer import casput
from serial import Serial
from time import time, sleep,gmtime, strftime
from sys import stdout
import os.path
from pdb import pm
from struct import unpack as struct_unpack
import logging
from logging import error,warn,info,debug
import circular_buffer_LL
from CAServer import casput,casget
from DI_245_driver import di245_driver
from persistent_property import persistent_property
from thread import start_new_thread


import msgpack
import msgpack_numpy as m

from socket import *

__version__ = '1.0.6' # Friedrich Schotte: logfile directory
__date__ = "04-30-18"

class DI245_DL(object):
    CA_prefix = persistent_property('CA_prefix', 'NIH:DI245.')
    scan_lst = persistent_property('scan_lst', [])
    phys_ch_lst = persistent_property('phys_ch_lst', [])
    gain_lst = persistent_property('gain_lst', [])
    RingBuffer_size = persistent_property('RingBuffer_size', 0)
    calib = persistent_property('calib', [])
    time_out = persistent_property('time_out', 0)
    cjc_value = persistent_property('cjc_value', '')
    SN = persistent_property('SN', '')
    socket = persistent_property('socket', ['',''])
    type_def = persistent_property('type_def', '')

    def __init__(self):
        self.name = 'DI245_syringe_tower'
        self.CA_update_t = 0.3
        

    def server_init(self):
        casput(self.CA_prefix+'SOCKET',['',''])
        self.socketserver_init()
        self.CAserver_init()

    def socketserver_init(self):
        socket_port_lst = range(2030,2050)
        i = 0
        flag = True
        while flag:
            try:
                port = socket_port_lst[i]
                self.sock = socket(AF_INET, SOCK_STREAM)
                self.sock.bind(('', port))
                self.sock.listen(5)

                info('Trial %r, Connection to 127.0.0.1:%r is successful' % (i,port))
                self.socket_port = port
                self.socket = [gethostbyname(gethostname()),self.socket_port]
                casput(self.CA_prefix+'SOCKET',self.socket)

                flag = False
                info('flag in socketserver_init = %r' %flag)
            except Exception as e:
                i+=1
                error(e)
        self.server_command_dict = {}
        self.server_command_dict[-2] = '-2:dev_info(in: None, out: dict)'
        self.server_command_dict[-1] = '-1:type_def(in:None, out: dict)'
        self.server_command_dict[0] = '0:init()'
        self.server_command_dict[1] = '1:close()'
        self.server_command_dict[2] = '2:broadcast fixed rate(in: float, out: None)'
        self.server_command_dict[3] = '3:request average of N (in:N, out:float)'
        self.server_command_dict[4] = '4:request buffer all(in: None, out: nparray)'
        self.server_command_dict[5] = '5:request buffer update(in:pointer, out:nparray)'
        self.server_command_dict[6] = '6:perform calibration(in: None, out: nparray)'
        self.server_command_dict[7] = '7:get calibration(in: None, out: nparray)' #stores 1 oldest calibration record.
        self.server_command_dict[8] = '8:save to a file(in: None, out: none)'
        self.type_def = msgpack.packb(self.server_command_dict, default=m.encode)
        msg_in = [-1,-1,-1,-1]

        self._run()

    def _run(self):
        start_new_thread(self._server_thread,())

    def _server_thread(self):
        """
        socket thread
        """
        self.socket_is_running = True
        while self.socket_is_running:
            self.client, self.addr = self.sock.accept()
            self._log_last_call()
            info( 'Client has connected: %r %r' % (self.client, self.addr ))
            try:
                pointer_temp = self.circular_buffer.pointer
            except:
                pointer_temp = nan
            try:
                msg_in = msgpack.unpackb(self.client.recv(64),object_hook=m.decode)
            except Exception as e:
                error(e)
                msg_in = [nan,nan,nan,nan]
            info('input from the client: %r' % msg_in)
            if msg_in[0] == -1:
                self._send([msg_in[0],time(),msgpack.packb(self.type_def, default=m.encode),-1])

            elif msg_in[0] == 0:
                debug('init command received')
                reply = self.init()
                if reply:
                    self._send([msg_in[0],time(),str(reply),-1])
                else:
                    self._send([msg_in[0],time(),str(reply),-1])
            elif msg_in[0] == 1:
                self._send([msg_in[0],time(),'Termination of the server initated',-1])
                self.full_stop()
                self.is_running = False
            elif msg_in[0] == 2:
                self._send([msg_in[0],time(),'broadcast on demand request executed',-1])
                self.broadcast(method = "on demand")
            elif msg_in[0] == 3:
                self._send([msg_in[0],time(),np.mean(self.circular_buffer.get_last_N(N = int(msg_in[1])),axis = 1),
                            np.std(self.circular_buffer.get_last_N(N = int(msg_in[1])), axis = 1)])
            elif msg_in[0] == 4:
                self._send([msg_in[0],time(),pointer_temp,self.circular_buffer.get_all()])
            elif msg_in[0] == 5 and msg_in[1] != '':
                if pointer_temp>msg_in[1]:
                    temp_n = pointer_temp-msg_in[1]
                else:
                    temp_n = self.circular_buffer.size[1]+pointer_temp-msg_in[1]
                self._send([msg_in[0],time(),pointer_temp,self.circular_buffer.get_last_N(N = temp_n)])
            elif msg_in[0] == 6:
                dev.set_calib()
                self._send([msg_in[0],time(),self.calib,-1])
            elif msg_in[0] == 7:
                self._send([msg_in[0],time(),self.calib,-1])
            elif msg_in[0] == 8:
                self._send([msg_in[0],time(),'command is not assigned yet: not decided yet ',-1])
            elif msg_in[0] == 9:
                self._send([msg_in[0],time(),'command is not assigned yet: not decided yet',-1])
            else:
                self._send([msg_in[0],time(),'do not know how to interpret msg_in[0] is not an integer',-1])


    def _receive(self):
        return self.client.recv(64)

    def _send(self,msg_out):
        """
        sends 2 transmissions:
        1) one is length of the expected number of bytes
        2) actual data
        """
        msg = msgpack.packb(msg_out, default=m.encode)
        sleep(0.025)
        length = str(len(msg))
        self.client.sendall(length)
        sleep(0.025)
        self.client.sendall(msg)

    def _log_last_call(self):
        self.log_last_client = self.client
        self.log_last_addr = self.addr


    def CAserver_init(self):
        from CAServer import casget, casput
        self.is_running = False
        self.CA_update_t = 0.3
        casput(self.CA_prefix+'LIVE',self.is_running)
        casput(self.CA_prefix+'UPDATE_T',self.CA_update_t)
        try:
            casput(self.CA_prefix+'SOCKET',self.socket)
        except:
            error(traceback.format_exc())

    def CAserver_update(self):
        from CAServer import casget, casput
        casput(self.CA_prefix+'LIVE',self.is_running)
        casput(self.CA_prefix+'UPDATE_T',self.CA_update_t)

    def CAserver_stop(self):
        from CAServer import casget, casput, casdel
        casdel(self.CA_prefix+'LIVE')
        casdel(self.CA_prefix+'UPDATE_T')
        casdel(self.CA_prefix+'SOCKET')

    def init(self,SN = 1):
        self.dev = di245_driver

        if self.find_device():
            self.connect_device(0)
            self.configure_device()
            info('DI245 is found: %r' % self.available_ports)
            self.info_dict = {}
            self.info_dict['scan_lst'] = self.scan_lst
            self.info_dict['phys_ch_lst'] = self.phys_ch_lst
            self.info_dict['gain_lst'] = self.gain_lst
            self.info_dict['RingBuffer_size'] = self.RingBuffer_size
            self.info_dict['calib'] = self.calib
            self.info_dict['time_out'] = self.time_out
            self.info_dict['cjc_value'] = self.cjc_value
            self.info_dict['SN'] = self.SN
            try:
                self.info_dict['socket'] = [gethostbyname(gethostname()),self.socket_port]
            except:
                self.info_dict['socket'] = ['','']

            self.run()
            reply = True
        else:
            reply = False
            error('DI-245 is not found')


        return reply

    def stop(self):
        self.full_stop()
        del self.dev

    def setup_first_time(self):
        #self.SN = '57D81C13'
        self.scan_lst = ['0','1','2','3']
        self.phys_ch_lst = ['0','1','2','3']
        self.gain_lst = ['5','5','5','T-thrmc']
        self.RingBuffer_size = 4320000
        self.time_out = 0.1
        self.cjc_value = -2.0 #this number needs to be tested with ice or another well calibrated thermocouple
        self.calib = [0.025,0,0.025,0,0] # [scale_up, offset_up, scale_down, offset_down, time] 50 mV per atm factory setting

    def find_device(self):
        self.available_ports = di245_driver.find_com_port()
        if len(self.available_ports) != 0:
            reply = True
        else:
            reply = False
        return reply

    def connect_device(self, N = 0):
        if len(self.available_ports) > 0:
            self.dev.initialize()
            res = True
        else:
            res = False
        return res


    def configure_device(self):
        self.circular_buffer = circular_buffer_LL.server(size = (len(self.scan_lst),self.RingBuffer_size), var_type = 'int16')#4320000
        print(self.scan_lst,self.phys_ch_lst,self.gain_lst)
        self.dev.config_channels(scan_lst=self.scan_lst,phys_ch_lst=self.phys_ch_lst,gain_lst = self.gain_lst)


    def read_number(self):
        value_array = self.dev.read_number(N_of_channels = len(self.scan_lst), N_of_points = 1)
        return value_array


    def stop_scan(self):
        self.dev.stop_scan()

    def full_stop(self):
        try:
            self.dev.full_stop()
            self.is_running = False
        except:
            warn('dev is not initialized')

    def set_calib(self):
        from time import time
        a = mean(((self.circular_buffer.get_last_N(N = 300)[0]-8192.)/8192.)*float(self.gain_lst[0]))
        b = mean(((self.circular_buffer.get_last_N(N = 300)[1]-8192.)/8192.)*float(self.gain_lst[1]))
        c = mean(((self.circular_buffer.get_last_N(N = 300)[2]-8192.)/8192.)*float(self.gain_lst[2]))
        d = -3.2 #-3.2 (-2.2 agains another tempmeter)
        self.calib = [a,b ,c ,d , time()]

    def save_to_a_file(self):
        debug('save to a file pressed %r' % time())
        pass

    def broadcast(self, method = "on demand"):

        if method == "on demand":
            #debug('Broadcasting on demand')
            ch1 = mean(((self.circular_buffer.get_last_N(N = 50)[0]-8192.)/8192.)*float(self.gain_lst[0]))/ self.calib[0]
            casput("NIH:pressure_upstream",ch1)
            ch2 = mean(((self.circular_buffer.get_last_N(N = 50)[1]-8192.)/8192.)*float(self.gain_lst[1]))/ self.calib[1]
            casput("NIH:pressure_downstream",ch2)
            ch3 =  mean(((108.364-88.0461)/2.0**13)*(self.circular_buffer.get_last_N(N = 50)[2]-2.0**13)+88.0461+0.2)
            casput("NIH:pressure_barometric",ch3)
            ch4 = mean(self.circular_buffer.get_last_N(N = 50)[3]-8192.)*0.036621+100. + self.calib[3]
            casput("NIH:temperature_hutch",ch4)

        else:
            debug("unknown method(%r) requested" % method)

    def run(self):
        from thread import start_new_thread
        print('start new thread in run')
        start_new_thread(self.measurements, ())


    def measurements(self):
        from time import time
        self.is_running = True
        dev.CAserver_update()
        self.dev.ser.flushInput()
        self.dev.ser.flushOutput()
        self.dev.start_scan()
        sleep(3)
        self.start_running = time()
        self.last_broadcast = time()
        self.broadcast_period = 10
        while self.is_running:
            t = time()
            if t-time() > self.CA_update_t: self.CAserver_update()
            if self.dev.ser.isOpen:
                while self.dev.waiting()[0]>3:
                    self.circular_buffer.append(
                        self.dev.read_number(N_of_channels = 4, N_of_points = 1))
                sleep(0.04)

            else:
                warn('measurements: break')
                self.is_running = False
                self.end_running = time()
                dev.CAserver_update()
            if time() - self.last_broadcast > self.broadcast_period:
                self.broadcast()
                self.last_broadcast = time()



if __name__ == "__main__":
    from tempfile import gettempdir
    logging.basicConfig(filename=gettempdir()+'/di_245_DL.log',
                        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    dev = DI245_DL()
    dev.init()
    dev.server_init()
    
