"""Executing hardware timed configuration changes on the FPGA timing system
in "Piano Player" mode.

Author: Friedrich Schotte
Date created: 2015-05-01
Date last modified: 2019-05-09
"""
__version__ = "6.6.1" # issue: queue_sequeces: dictionary size changed during iteration
from logging import error,info,warn,debug
from numpy import nan,isnan

class Sequence(object):
    parameters = {}
 
    def __init__(self,**kwargs):
        """Arguments: delay=100e-12,laser_on=1,..."""
        from collections import OrderedDict
        from numpy import nan
        keys = timing_sequencer.parameters
        self.parameters = OrderedDict(zip(keys,[nan]*len(keys)))
        for name in kwargs:
            alt_name = name.replace("_on",".on")
            if not (name in keys or alt_name in keys):
                warn("Sequence: unsupported parameter %r" % name)
        for key in kwargs: setattr(self,key,kwargs[key])
        self.set_defaults()

    def __getattr__(self,name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        alt_name = name.replace("_on",".on")
        if name in self.parameters: return self.parameters[name]
        elif alt_name in self.parameters: return self.parameters[alt_name]
        else: return object.__getattribute__(self,name)

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        alt_name = name.replace("_on",".on")
        if name.startswith("__"): object.__setattr__(self,name,value)
        elif name in self.parameters: self.parameters[name] = value
        elif alt_name in self.parameters: self.parameters[alt_name] = value
        else: object.__setattr__(self,name,value)

    def set_defaults(self):
        """Fill in unspecified parameters with default values."""
        from numpy import isnan
        from timing_system import timing_system
        for key in self.parameters:
            if key in ["pass_number","image_number"]: continue
            if isnan(self.parameters[key]):
                self.parameters[key] = timing_sequencer.get_default(key)

    @property
    def descriptor(self):
        """Text representation of the parameters for generating this
        sequence"""
        p = self.parameters
        description = ",".join(["%s=%g"%(k,v) for k,v in zip(p.keys(),p.values())])+","

        description += "generator=%r," % "timing_sequence"
        description += "generator_version=%r," % __version__

        return description
    
    @property
    def register_counts(self):
        """list of registers, list of arrays of values"""
        from timing_system import timing_system,round_next
        from numpy import isnan,where,arange,rint,floor,ceil,array,cumsum
        from numpy import zeros,maximum,clip,unique
        from sparse_array import sparse_array
        
        delay = self.delay
        Tbase = timing_system.hsct # Period of the 987-Hz clock
        waitt = round_next(self.waitt,timing_system.waitt.stepsize)
        burst_waitt = round_next(self.burst_waitt,timing_system.burst_waitt.stepsize)
        burst_delay = round_next(self.burst_delay,timing_system.burst_delay.stepsize)
        n = int(rint(waitt/Tbase)) # Sequence length period in 987-Hz cycles
        ndt = int(rint(burst_waitt/Tbase)) # X-ray repetition period, in 987-Hz cycles
        n_burst_delay = int(rint(burst_delay/Tbase)) # X-ray burst delay, in 987-Hz cycles
        n = max(n,ndt*int(self.npulses)) # Make sure the period is long enough for npulses
        delay_coarse = int(floor(delay/Tbase))
        delay_value = delay - delay_coarse*Tbase
        it0 = n_burst_delay + ndt - 2 # First X-ray pulse, in 987-Hz cycles

        # The high-speed chopper determines the X-ray pulse timing. 
        xd = -timing_system.hsc.delay.offset
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-unch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        if 100e-9 < abs(timing_system.hsc.delay.value) < 4e-6:
            xd += timing_system.hsc.delay.value

        it_laser = it0-delay_coarse + arange(0,int(self.npulses)*ndt,ndt)
        it_xray = it0 + arange(0,int(self.npulses)*ndt,ndt)
        t_xray = it_xray*Tbase+xd
        t_laser = t_xray - delay

        # Trigger X-ray millsecond shutter
        pulse_length = timing_system.ms.pulse_length
        if self.burst_waitt < 0.010:
            # Assume the X-ray is continuously firing at 120 Hz.
            t_ms_open  = min(t_xray) - timing_system.ms.offset
            t_ms_close = max(t_xray) - timing_system.ms.offset + pulse_length
            t_ms_open  = array([t_ms_open])
            t_ms_close = array([t_ms_close])
        else:
            t_ms_open  = t_xray - timing_system.ms.offset
            t_ms_close = t_xray - timing_system.ms.offset + pulse_length
        it_ms_open  = maximum(floor(t_ms_open /Tbase),0).astype(int)
        it_ms_close = maximum(ceil(t_ms_close/Tbase),0).astype(int)
        it_ms_open  = it_ms_open [it_ms_open<n]
        it_ms_close = it_ms_close[it_ms_close<n]
        ms_inc =  sparse_array(n)
        ms_inc[it_ms_open]  += 1
        ms_inc[it_ms_close] -= 1
        ms_state_counts = clip(cumsum(ms_inc),0,1)
        ms_state_counts = sparse_array(ms_state_counts)

        # Trigger X-ray attenuator
        pulse_length = timing_system.s3.pulse_length
        if self.burst_waitt < 0.010:
            # Assume the X-ray is continuously firing at 120 Hz.
            t_xatt_open  = min(t_xray) - timing_system.s3.offset
            t_xatt_close = max(t_xray) - timing_system.s3.offset + pulse_length
            t_xatt_open  = array([t_xatt_open])
            t_xatt_close = array([t_xatt_close])
        else:
            t_xatt_open  = t_xray - timing_system.s3.offset
            t_xatt_close = t_xray - timing_system.s3.offset + pulse_length
        it_xatt_open  = maximum(floor(t_xatt_open /Tbase),0).astype(int)
        it_xatt_close = maximum(ceil(t_xatt_close/Tbase),0).astype(int)
        it_xatt_open  = it_xatt_open [it_xatt_open<n]
        it_xatt_close = it_xatt_close[it_xatt_close<n]
        xatt_inc =  sparse_array(n)
        xatt_inc[it_xatt_open]  += 1
        xatt_inc[it_xatt_close] -= 1
        xatt_state_counts = clip(cumsum(xatt_inc),0,1)
        xatt_state_counts = sparse_array(xatt_state_counts)

        # Detector readout 
        # Delay: "xdet.offset" (e.g. -6 ms)
        # Pulse length "xdet.pulse_length" (e.g. 2 ms)
        # After the last X-ray pulse
        ##t_xdet_rise = max(t_xray) - timing_system.xdet.offset
        # At beginning
        t_xdet_rise = 0 - timing_system.xdet.offset
        t_xdet_fall = t_xdet_rise + timing_system.xdet.pulse_length
        t_xdet_rise = array([t_xdet_rise])
        t_xdet_fall = array([t_xdet_fall])
        it_xdet_rise  = maximum(rint(t_xdet_rise /Tbase),0).astype(int)
        it_xdet_fall = maximum(rint(t_xdet_fall/Tbase),0).astype(int)
        it_xdet_rise  = it_xdet_rise [it_xdet_rise<n]
        it_xdet_fall = it_xdet_fall[it_xdet_fall<n]
        xdet_inc =  sparse_array(n)
        xdet_inc[it_xdet_rise]  += 1
        xdet_inc[it_xdet_fall] -= 1
        xdet_state_counts = clip(cumsum(xdet_inc),0,1)
        xdet_state_counts = sparse_array(xdet_state_counts)
        xdet_count_inc =  sparse_array(n)
        xdet_count_inc[it_xdet_rise] = 1

        # Trigger the sample translation after the last X-ray pulse.
        t_trans_rise = max(t_xray) - timing_system.trans.offset
        t_trans_fall = t_trans_rise + timing_system.trans.pulse_length
        t_trans_rise  = array([t_trans_rise])
        t_trans_fall = array([t_trans_fall])
        it_trans_rise  = maximum(rint(t_trans_rise /Tbase),0).astype(int)
        it_trans_fall = maximum(rint(t_trans_fall/Tbase),0).astype(int)
        it_trans_rise  = it_trans_rise [it_trans_rise<n]
        it_trans_fall = it_trans_fall[it_trans_fall<n]
        trans_inc =  sparse_array(n)
        trans_inc[it_trans_rise]  += 1
        trans_inc[it_trans_fall] -= 1
        trans_state_counts = clip(cumsum(trans_inc),0,1)
        trans_state_counts = sparse_array(trans_state_counts)
        ##trans_state_counts *= int(self.trans_on)
        if not self.trans_on: trans_state_counts = sparse_array(n,0)

        delay_dial = timing_system.delay.dial_from_user(delay_value)
        # Decompose the delay value into an X-ray delay and a laser delay.
        ld = xd - delay_dial

        # Picosecond laser amplifier trigger.
        pst_dial = timing_system.pst.dial_from_user(ld)
        pst_count = timing_system.pst.count_from_dial(pst_dial)
        pst_delay_counts = sparse_array(n,pst_count)
        pst_enable_counts = sparse_array(n)
        pst_enable_counts[it_laser] = int(self.laser_on)
        
        # Picosecond oscillator reference clock (Gigabaudics, 10 ps resolution)
        psd1_period = 5*timing_system.bct
        psd1_dial = timing_system.psd1.dial_from_user(pst_dial) % psd1_period
        psd1_count = timing_system.psd1.count_from_dial(psd1_dial)
        psd1_counts = sparse_array(n,psd1_count)

        # Picosecond oscillator reference clock (course, 7.1 ns resolution)
        pso_period = 5*timing_system.bct
        pso_coarse_step = timing_system.psod3.stepsize
        pso_dial = timing_system.psod3.dial_from_user(pst_dial) % pso_period
        psod3_dial = floor(pso_dial/pso_coarse_step)*pso_coarse_step
        psod3_count = timing_system.psod3.count_from_dial(psod3_dial)
        psod3_counts = sparse_array(n,psod3_count)
        # Picosecond oscillator reference clock (fine, 9 ps resolution)
        psod2_dial = pso_dial % pso_coarse_step
        clk_shift_count = timing_system.psod2.count_from_dial(psod2_dial)
        psod2_counts = sparse_array(n,clk_shift_count)
        
        # Laser shutter for LCLS -> ps L gate output 
        pulse_length = timing_system.psg.pulse_length
        if self.burst_waitt < 0.010:
            # Assume the laser is continuously firing at 120 Hz.
            t_psg_open  = min(t_laser) - timing_system.psg.offset
            t_psg_close = max(t_laser) - timing_system.psg.offset + pulse_length
            t_psg_open  = array([t_psg_open])
            t_psg_close = array([t_psg_close])
        else:
            t_psg_open  = t_laser - timing_system.psg.offset
            t_psg_close = t_laser - timing_system.psg.offset + pulse_length
        it_psg_open  = maximum(floor(t_psg_open /Tbase),0).astype(int)
        it_psg_close = maximum(ceil(t_psg_close/Tbase),0).astype(int)
        it_psg_open  = it_psg_open [it_psg_open<n]
        it_psg_close = it_psg_close[it_psg_close<n]
        psg_inc =  sparse_array(n)
        psg_inc[it_psg_open]  += 1
        psg_inc[it_psg_close] -= 1
        psg_state_counts = clip(cumsum(psg_inc),0,1)
        psg_state_counts = sparse_array(psg_state_counts)
        ##psg_state_counts *= int(self.laser_on)
        if not self.laser_on: psg_state_counts = sparse_array(n,0)

        # Nanosecond laser Q-switch trigger.
        nsq_dial = timing_system.nsq.dial_from_user(ld)
        nsq_count = timing_system.nsq.count_from_dial(nsq_dial)
        nsq_delay_counts = sparse_array(n,nsq_count)
        nsq_enable_counts = sparse_array(n)
        nsq_enable_counts[it_laser] = int(self.laser_on)
        
        # Nanosecond laser flashlamp trigger.
        nsf_dial = timing_system.nsf.dial_from_user(ld)
        nsf_count = timing_system.nsf.count_from_dial(nsf_dial)
        nsf_delay_counts = sparse_array(n,nsf_count)
        
        nsf_period = 48 # 20 Hz operation, 10 Hz = 96 counts
        it0_nsf = it_laser[0] % nsf_period
        it_nsf = range(it0_nsf,n,nsf_period)
        nsf_enable_counts = sparse_array(n)
        nsf_enable_counts[it_nsf] = 1

        # X-ray diagnostics oscilloscope
        xosct_count = timing_system.xosct.count_from_value(xd)
        xosct_delay_counts = sparse_array(n,xosct_count)
        xosct_enable_counts = sparse_array(n)
        xosct_enable_counts[it_xray] = int(self.xosct_on)

        # Laser diagnostics oscilloscope
        losct_count = timing_system.losct.count_from_value(ld)
        losct_delay_counts = sparse_array(n,losct_count)
        losct_enable_counts = sparse_array(n)
        losct_enable_counts[it_laser] = 1

        # Laser camera trigger
        lcam_count = timing_system.lcam.count_from_value(ld)
        lcam_delay_counts = sparse_array(n,lcam_count)
        lcam_enable_counts = sparse_array(n)
        lcam_enable_counts[it_laser] = int(self.lcam_on)

        # Camera shutter to protect the camera from laser flashes.
        pulse_length = timing_system.s1.pulse_length
        if self.burst_waitt < 0.010:
            # Assume the laser is continuously firing at 120 Hz.
            t_camshut_open  = min(t_laser) - timing_system.s1.offset
            t_camshut_close = max(t_laser) - timing_system.s1.offset + pulse_length
            t_camshut_open  = array([t_camshut_open])
            t_camshut_close = array([t_camshut_close])
        else:
            t_camshut_open  = t_laser - timing_system.s1.offset
            t_camshut_close = t_laser - timing_system.s1.offset + pulse_length
        it_camshut_open  = maximum(floor(t_camshut_open /Tbase),0).astype(int)
        it_camshut_close = maximum(ceil(t_camshut_close/Tbase),0).astype(int)
        it_camshut_open  = it_camshut_open [it_camshut_open<n]
        it_camshut_close = it_camshut_close[it_camshut_close<n]
        camshut_inc =  sparse_array(n)
        camshut_inc[it_camshut_open]  += 1
        camshut_inc[it_camshut_close] -= 1
        camshut_state_counts = clip(cumsum(camshut_inc),0,1)
        # Only close the shutter when the laser is firing.
        camshut_state_counts = sparse_array(camshut_state_counts)
        ##camshut_state_counts *= int(self.laser_on)
        if not self.laser_on: camshut_state_counts = sparse_array(n,0)

        # Indicate whether data acquisition is running.
        acquiring_counts = sparse_array(n,self.acquiring)

        registers,counts=[],[]
        registers += [timing_system.pst.enable];   counts += [pst_enable_counts]
        registers += [timing_system.pst.delay];    counts += [pst_delay_counts]
        if self.psg_on: registers += [timing_system.psg.state]; counts += [psg_state_counts]
        if self.s1_on:  registers += [timing_system.s1.state];  counts += [camshut_state_counts]
        registers += [timing_system.nsq.enable];   counts += [nsq_enable_counts]
        registers += [timing_system.nsq.delay];    counts += [nsq_delay_counts]
        registers += [timing_system.nsf.enable];   counts += [nsf_enable_counts]
        registers += [timing_system.nsf.delay];    counts += [nsf_delay_counts]
        if self.xdet_on:
            registers += [timing_system.xdet.state];   counts += [xdet_state_counts]
            registers += [timing_system.xdet_count];   counts += [xdet_count_inc]
        registers += [timing_system.trans.state];  counts += [trans_state_counts]
        registers += [timing_system.xosct.enable]; counts += [xosct_enable_counts]
        registers += [timing_system.xosct.delay];  counts += [xosct_delay_counts]
        if self.losct_on: registers += [timing_system.losct.enable]; counts += [losct_enable_counts]
        if self.losct_on: registers += [timing_system.losct.delay];  counts += [losct_delay_counts]
        registers += [timing_system.lcam.enable];  counts += [lcam_enable_counts]
        registers += [timing_system.lcam.delay];   counts += [lcam_delay_counts]
        if self.ms_on: registers += [timing_system.ms.state]; counts += [ms_state_counts]
        if self.s3_on: registers += [timing_system.s3.state]; counts += [xatt_state_counts]
        registers += [timing_system.psod3];        counts += [psod3_counts]
        registers += [timing_system.psod2];        counts += [psod2_counts]
        registers += [timing_system.acquiring];    counts += [acquiring_counts]

        if not isnan(self.image_number):
            image_number_counts = sparse_array(n,self.image_number)
            registers += [timing_system.image_number]; counts += [image_number_counts]
        if not isnan(self.pass_number):
            pass_number_counts = sparse_array(n,self.pass_number)
            registers += [timing_system.pass_number];  counts += [pass_number_counts]
        image_number_inc_counts = sparse_array(n,0)
        image_number_inc_counts[0] = self.image_number_inc
        registers += [timing_system.image_number_inc]; counts += [image_number_inc_counts]
        pass_inc_counts = sparse_array(n,0)
        pass_inc_counts[0] = self.pass_number_inc
        registers += [timing_system.pass_number_inc];  counts += [pass_inc_counts]
        if self.ms_on:
            pulses_counts = sparse_array(n,0)
            pulses_inc_counts = sparse_array(n)
            pulses_inc_counts[it_xray] = 1
            registers += [timing_system.pulses_inc];   counts += [pulses_inc_counts]
            registers += [timing_system.pulses];       counts += [pulses_counts]

        # Channel configuration-based sequence generation
        for i in range(0,len(timing_system.channels)):
            if timing_system.channels[i].PP_enabled:
                r,c = self.channel_register_counts(i)
                registers += r; counts += c

        return registers,counts

    def channel_register_counts(self,i):
        """i: channel number (0-based)"""
        from sparse_array import sparse_array
        from numpy import rint,floor,array,clip,cumsum
        from timing_system import timing_system,round_next

        delay = self.delay
        Tbase = timing_system.hsct # Period of the 987-Hz clock
        waitt = round_next(self.waitt,timing_system.waitt.stepsize)
        burst_waitt = round_next(self.burst_waitt,timing_system.burst_waitt.stepsize)
        burst_delay = round_next(self.burst_delay,timing_system.burst_delay.stepsize)
        n = int(rint(waitt/Tbase)) # Sequence length period in 987-Hz cycles
        ndt = int(rint(burst_waitt/Tbase)) # X-ray repetition period, in 987-Hz cycles
        n_burst_delay = int(rint(burst_delay/Tbase)) # X-ray burst delay, in 987-Hz cycles
        n = max(n,ndt*int(self.npulses)) # Make sure the period is long enough for npulses
        delay_coarse = int(floor(delay/Tbase))
        delay_value = delay - delay_coarse*Tbase

        channel = timing_system.channels[i]

        if channel.special == "test":
            # Test pattern generator
            state_counts = array([1,0]*(n/2)+[0]*(n%2))
            state_counts = sparse_array(state_counts)
        else:
            t0 = channel.offset
            dt = channel.pulse_length
            repeat = channel.repeat_period # 'pulse','burst','image'
            if repeat == 'pulse':    T = timing_system.burst_waitt.value
            elif repeat == 'burst':  T = timing_system.waitt.value
            elif repeat == 'image':  T = timing_system.bursts_per_image*timing_system.waitt.value
            elif repeat == '1 ms':   T = Tbase
            elif repeat == '50 ms':  T = 50*Tbase
            elif repeat == '100 ms': T = 100*Tbase

            t = array([t0,t0+dt])
            it = clip(rint(t/Tbase),0,n-1).astype(int)
            it_on,it_off = it.reshape((-1,2)).T
            inc = sparse_array(n)
            inc[it_on]  += 1
            inc[it_off] -= 1
            state_counts = clip(cumsum(inc),0,1)
            state_counts = sparse_array(state_counts)
        
        counts = [state_counts]
        registers = [channel.state]
        ##registers += [channel.delay]

        return registers,counts
        
    @property
    def t_laser(self):
        """Pump (laser arrival) times in seconds"""
        from timing_system import timing_system,round_next
        from numpy import isnan,where,arange,rint,floor,ceil,array,cumsum
        from numpy import zeros,maximum,clip,unique
        from sparse_array import sparse_array
        
        delay = self.delay
        Tbase = timing_system.hsct # Period of the 987-Hz clock
        waitt = round_next(self.waitt,timing_system.waitt.stepsize)
        burst_waitt = round_next(self.burst_waitt,timing_system.burst_waitt.stepsize)
        burst_delay = round_next(self.burst_delay,timing_system.burst_delay.stepsize)
        n = int(rint(waitt/Tbase)) # Sequence length period in 987-Hz cycles
        ndt = int(rint(burst_waitt/Tbase)) # X-ray repetition period, in 987-Hz cycles
        n_burst_delay = int(rint(burst_delay/Tbase)) # X-ray burst delay, in 987-Hz cycles
        n = max(n,ndt*int(self.npulses)) # Make sure the period is long enough for npulses
        delay_coarse = int(floor(delay/Tbase))
        delay_value = delay - delay_coarse*Tbase
        it0 = n_burst_delay + ndt - 2 # First X-ray pulse, in 987-Hz cycles

        # The high-speed chopper determines the X-ray pulse timing. 
        xd = -timing_system.hsc.delay.offset
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-unch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        if 100e-9 < abs(timing_system.hsc.delay.value) < 4e-6:
            xd += timing_system.hsc.delay.value

        it_laser = it0-delay_coarse + arange(0,int(self.npulses)*ndt,ndt)
        it_xray = it0 + arange(0,int(self.npulses)*ndt,ndt)
        t_xray = it_xray*Tbase+xd
        t_laser = t_xray - delay
        return t_laser

    @property
    def t_xray(self):
        """Probe (X-ray arrival) times in seconds"""
        from timing_system import timing_system,round_next
        from numpy import isnan,where,arange,rint,floor,ceil,array,cumsum
        from numpy import zeros,maximum,clip,unique
        from sparse_array import sparse_array
        
        delay = self.delay
        Tbase = timing_system.hsct # Period of the 987-Hz clock
        waitt = round_next(self.waitt,timing_system.waitt.stepsize)
        burst_waitt = round_next(self.burst_waitt,timing_system.burst_waitt.stepsize)
        burst_delay = round_next(self.burst_delay,timing_system.burst_delay.stepsize)
        n = int(rint(waitt/Tbase)) # Sequence length period in 987-Hz cycles
        ndt = int(rint(burst_waitt/Tbase)) # X-ray repetition period, in 987-Hz cycles
        n_burst_delay = int(rint(burst_delay/Tbase)) # X-ray burst delay, in 987-Hz cycles
        n = max(n,ndt*int(self.npulses)) # Make sure the period is long enough for npulses
        delay_coarse = int(floor(delay/Tbase))
        delay_value = delay - delay_coarse*Tbase
        it0 = n_burst_delay + ndt - 2 # First X-ray pulse, in 987-Hz cycles

        # The high-speed chopper determines the X-ray pulse timing. 
        xd = -timing_system.hsc.delay.offset
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-unch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        if 100e-9 < abs(timing_system.hsc.delay.value) < 4e-6:
            xd += timing_system.hsc.delay.value

        it_laser = it0-delay_coarse + arange(0,int(self.npulses)*ndt,ndt)
        it_xray = it0 + arange(0,int(self.npulses)*ndt,ndt)
        t_xray = it_xray*Tbase+xd
        t_laser = t_xray - delay
        return t_xray

    @property
    def data(self):
        """Binary sequence data"""
        descriptor = self.descriptor
        if timing_sequencer.cache_enabled:
            packet = timing_sequencer.cache_get(descriptor)
        if not timing_sequencer.cache_enabled or len(packet) == 0:
            registers,counts = self.register_counts
            packet = sequencer_packet(registers,counts,descriptor)
        if timing_sequencer.cache_enabled:
            timing_sequencer.cache_set(descriptor,packet)
        return packet

    def __repr__(self):
        p = self.parameters
        return "Sequence("+",".join(["%s=%r" % (key,p[key]) for key in p])+")"
        
sequence = Sequence


class TimingSequencer(object):
    from persistent_property import persistent_property
    
    from cached_property import cached_property
    count = 0
    parameters = [
        "delay",
        "laser_on",
        "psg.on",
        "waitt",
        "npulses",
        "burst_waitt",
        "burst_delay",
        "xosct.on",
        "losct.on",
        "lcam.on",
        "s1.on",
        "ms.on",
        "xdet.on",
        "trans.on",
        "trans.bit_code",
        "s3.on",
        "image_number",
        "pass_number",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",
        # Calibration constants and parameters
        "hlc_div",
        "hsc.delay",
        "hsc.delay.offset",
        "ms.offset",
        "ms.pulse_length",
        "psg.offset",
        "nsf.offset",
        "nsq.offset",
        "xdet.offset",
        "trans.offset",
        "trans.pulse_length",
    ]

    def get_default(self,name):
        """Get default value for parameter
        name: 'delay','laser_on'... """
        from timing_system import timing_system
        from numpy import nan
        
        if name == "acquiring": value = False
        elif name == "image_number": value = nan
        else:
            alt_name = name.replace("_on",".on")
            if alt_name in self.parameters: name = alt_name
            try: value = eval("timing_system.%s_on" % name)
            except AttributeError:
                try: value = eval("timing_system.%s.value" % name)
                except AttributeError: value = eval("timing_system.%s" % name)
        return value
    def set_default(self,name,value,update=True):
        """Set default value  for parameter
        name: 'delay','laser_on'... """
        alt_name = name.replace("_on",".on")
        if alt_name in self.parameters: name = alt_name
        from timing_system import timing_system
        try:
            eval("timing_system.%s_on" % name)
            exec("timing_system.%s_on = %r" % (name,value))
        except AttributeError:
            try:
                eval("timing_system.%s.value" % name)
                exec("timing_system.%s.value = %r" % (name,value))
            except AttributeError:
                exec("timing_system.%s = %r" % (name,value))
        if update: self.set_default_sequences()
    
    def __getattr__(self,name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute was not found the usual ways.
        from timing_system import timing_system
        alt_name = name.replace("_",".",1) # xdet_trig_count -> xdet.trig_count
        if name in self.parameters: return self.current_value(name)
        elif alt_name in self.parameters: return self.current_value(alt_name)
        elif hasattr(timing_system,name):
            attr = getattr(timing_system,name)
            if hasattr(attr,"value"): attr = attr.value
            return attr
        elif self.hasattr(timing_system,alt_name):
            attr = eval("timing_system.%s" % alt_name)
            if hasattr(attr,"value"): attr = attr.value
            return attr
        else: return object.__getattribute__(self,name)

    @staticmethod
    def hasattr(object,name):
        """name: e.g. 'hsc.delay'"""
        try: eval("object.%s" % name); return True
        except AttributeError: return False

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        from timing_system import timing_system
        alt_name = name.replace("_",".") # hsc_delay > hsc.delay
        if name.startswith("__"): object.__setattr__(self,name,value)
        elif name in self.parameters: self.set_default(name,value)
        elif alt_name in self.parameters: self.set_default(alt_name,value)
        elif hasattr(timing_system,name):
            attr = getattr(timing_system,name)
            if hasattr(attr,"value"): attr.value = value
            else: setattr(timing_system,name,value) 
        elif self.hasattr(timing_system,alt_name):
            attr = eval("timing_system.%s" % alt_name)
            if hasattr(attr,"value"): attr.value = value
            else: exec("timing_system.%s = %r" % (alt_name,value)) 
        else: object.__setattr__(self,name,value)

    def get_ip_address(self):
        """Timing system's network address"""
        from timing_system import timing_system
        return timing_system.ip_address
    def set_ip_address(self,value): 
        from timing_system import timing_system
        timing_system.ip_address = value
    ip_address = property(get_ip_address,set_ip_address)

    sequence_dir = "/tmp/sequencer_fs"
    queue_name = "queue"
    queue_filename = sequence_dir+"/"+queue_name
    queue_names = "queue1","queue2","queue"

    def get_queue(self):
        """Acquisition queue's packet IDs as list of strings"""
        return self.queue_content(self.queue_name)
    def set_queue(self,IDs):
        self.set_queue_content(self.queue_name,IDs)
    queue = property(get_queue,set_queue)

    def get_current_queue(self):
        """Packet IDs as list of strings"""
        return self.queue_content(self.current_queue_name)
    def set_current_queue(self,IDs):
        self.set_queue_content(self.current_queue_name,IDs)
    current_queue = property(get_current_queue,set_current_queue)

    def queue_content(self,queue_name):
        """Packet IDs as list of strings
        queue_name: "queue" (default) for data acquistion;
          "queue1" or "queue2" for idle mode
        """
        queue_filename = self.sequence_dir+"/"+queue_name
        file_content = self.file(queue_filename)
        IDs = file_content.strip("\n").split("\n") if len(file_content) > 0 else []
        return IDs

    def set_queue_content(self,queue_name,IDs):
        """Packet IDs as list of strings
        queue_name: "queue" (default) for data acquistion;
          "queue1" or "queue2" for idle mode
        IDs: Packet IDs as list of strings
        """
        queue_filename = self.sequence_dir+"/"+queue_name
        file_content = "\n".join(IDs)+("\n" if len(IDs)>0 else "")
        self.put_file(queue_filename,file_content)

        # First-time initialization
        filenames,file_contents = [],[]
        uploaded_files = self.uploaded_files
        filename = queue_filename+"_sequence_count"
        file_content = "%-20d" % 0
        if not filename in uploaded_files: filenames += [filename]; file_contents += [file_content]
        filename = queue_filename+"_repeat_count"
        file_content = "%-20d" % 0
        if not filename in uploaded_files: filenames += [filename]; file_contents += [file_content]
        filename = queue_filename+"_max_repeat_count"
        file_content = "%-20d" % 1
        if file_content != self.file(filename): filenames += [filename]; file_contents += [file_content]
        self.put_files(filenames,file_contents)

    def get_idle(self):
        """Is the idle queue being executed?"""
        return self.current_queue_name != self.queue_name
    def set_idle(self,value):
        if value: self.next_queue_name = self.default_queue_name
        else: self.next_queue_name = self.queue_name
    idle = property(get_idle,set_idle)

    def get_queue_active(self):
        """Is the data acquistion queue actively beeing executed?"""
        return self.current_queue_name == self.queue_name
    def set_queue_active(self,value):
        if value: self.next_queue_name = self.queue_name
        else: self.next_queue_name = self.default_queue_name
    queue_active = property(get_queue_active,set_queue_active)

    def _get_queue_length(self):
        """How many sequences are left in the acquisition queue?"""
        return len(self.queue)
    def set_queue_length(self,value):
        if value == 0: self.queue = []
    queue_length = property(_get_queue_length,set_queue_length)

    def get_current_queue_length(self):
        """How many sequences are left in the idle or acquisition queue?"""
        return len(self.current_queue)
    def set_current_queue_length(self,value):
        if value == 0: self.current_queue = []
    current_queue_length = property(get_current_queue_length,
        set_current_queue_length)

    def get_queue_length(self,queue_name):
        """How many sequences are left in the  queue?"""
        return len(self.queue_content(queue_name))

    @property
    def generator(self):
        """Sequence generator Python module name"""
        return self.current_sequence_property("generator","")

    @property
    def generator_version(self):
        """Sequence generator Python module version number"""
        return self.current_sequence_property("generator_version","")

    def current_sequence_property(self,name,default_value=None,dtype=None):
        """
        name: e.g. 'mode','delay','laseron','count'
        dtype: data type
        """
        descriptor = self.descriptor
        return self.property_value(self.descriptor,name,default_value,dtype)

    def current_value(self,name):
        """Get the value of a parameter from the currently executing sequence
        name: e.g. 'mode','delay','laseron','count'
        dtype: data type
        """
        if name in ["pass_number","image_number"]:
            from timing_system import timing_system
            value = getattr(timing_system,name)
            if hasattr(value,"value"): value = value.value
        else: value = self.property_value(self.descriptor,name)
        return value

    def property_value(self,descriptor,name,default_value=None,dtype=None):
        """Extract a value from a sequence descriptor
        descriptor: comma separated list
        e.g. 'mode=Stepping-48,delay=0.0316,laseron=True,count=6'
        name: e.g. 'mode','delay','laseron','count'
        """
        if default_value is None and dtype is not None: default_value = dtype()

        def default():
            if default_value is None: return self.get_default(name)
            else: return default_value 
            
        value = None
        for record in descriptor.split(","):
            parts = record.split("=")
            key = parts[0]
            if key != name: continue
            if len(parts) < 2: value = default()
            else:
                value = parts[1]
                try:
                    value = eval(value)
                    if dtype is not None: value = dtype(value)
                except: value = default()
        if value is None: value = default()
        return value

    def get_running(self):
        """Is the command currently running?"""
        running = self.current_sequence_length > 0
        running = running and self.interrupt_enabled
        running = running and self.interrupt_handler_enabled
        return running
    def set_running(self,value,update=None):
        if bool(value) == True:
            if update is None: self.update()
            else: update()
            self.interrupt_handler_enabled = 1
        if bool(value) == False:
            self.default_queue_name = ""
            self.next_queue_name = ""
    running = property(get_running,set_running)

    def set_queue_sequences(self,
        sequences,
        queue_name=None,
        default_queue_name=None,
        next_queue_name=None,
        ):
        """Queue a timing sequence for execution.
        sequences: list of seqence objects
        queue_name: "queue" (default) for data acquistion;
          "queue1" or "queue2" for idle mode
        default_queue_name: make this queue the new default when ready
        next_queue_name: switch to this queue when ready
        """
        if queue_name is None: queue_name = self.queue_name
        self.queue_sequences[queue_name] = sequences
        if default_queue_name is not None:
            self.default_queue_name_requested = default_queue_name
        if next_queue_name is not None:
            self.next_queue_name_requested = next_queue_name
        self.updating_queues = True

    queue_sequences = {}
    default_queue_name_requested = None
    next_queue_name_requested = None

    def update_queues(self):
        queue_sequences = dict(self.queue_sequences)
        for queue_name in queue_sequences:
            if self.updating_queues_cancelled: break

            sequences = queue_sequences[queue_name]

            self.set_queue_content(queue_name,[seq.id for seq in sequences])

            filenames = []
            file_contents = []

            uploaded_files = self.uploaded_files

            for i,sequence in enumerate(sequences):
                if self.updating_queues_cancelled: break
                filename = self.sequence_dir+"/"+sequence.id
                if not filename in filenames:
                    if not filename in uploaded_files:
                        if sequence.is_cached:
                            filenames += [filename]
                            file_contents += [sequence.data]
            if self.updating_queues_cancelled: break
            
            self.put_files(filenames,file_contents)
            for filename in filenames:
                if filename not in uploaded_files: uploaded_files += [filename]

            for i,sequence in enumerate(sequences):
                if self.updating_queues_cancelled: break
                filename = self.sequence_dir+"/"+sequence.id
                if filename not in uploaded_files:
                    if not sequence.is_cached:
                        info("Generating packets: %d/%d" % (i+1,len(sequences)))
                    file_content = sequence.data
                    self.put_file(filename,file_content)
                    uploaded_files += [filename]

        # Switch queue when ready    
        if self.default_queue_name_requested is not None:
            self.default_queue_name = self.default_queue_name_requested
            self.default_queue_name_requested = None
        if self.next_queue_name_requested is not None:
            self.next_queue_name = self.next_queue_name_requested
            self.next_queue_name_requested = None

    from thread_property_2 import thread_property
    updating_queues = thread_property(update_queues)
    updating_queues_cancelled = False

    def wait_for_queue_ready(self,queue_name):
        from time import sleep
        if not self.get_queue_ready(queue_name):
            info("%r not ready" % queue_name)
            while not self.get_queue_ready(queue_name): sleep(0.5)
            info("%r ready" % queue_name)

    @property
    def queue_ready(self):
        return self.get_queue_ready(self.queue_name)

    @property
    def queue_files_uploaded(self):
        return self.get_queue_files_uploaded(self.queue_name)

    def get_queue_files_uploaded(self,queue_name):
        uploaded_count = self.get_queue_uploaded_file_count(queue_name)
        count = self.get_queue_file_count(queue_name)
        uploaded = uploaded_count >= count
        return uploaded

    def get_queue_ready(self,queue_name):
        """Are there a sufficient number of files uploaded to start executing
        this queue?"""
        uploaded_count = self.get_queue_uploaded_file_count(queue_name)
        count = self.get_queue_file_count(queue_name)
        ready = uploaded_count >= count or uploaded_count > 2
        return ready

    def get_queue_file_count(self,queue_name):
        IDs = list(set(self.queue_content(queue_name)))
        count = len(IDs)
        return count

    def get_queue_uploaded_file_count(self,queue_name):
        IDs = list(set(self.queue_content(queue_name)))
        filenames = [self.sequence_dir+"/"+ID for ID in IDs]
        uploaded_files = self.uploaded_files
        count = sum([filename in uploaded_files for filename in filenames])
        return count

    def get_queue_files_uploaded(self,queue_name):
        """Are there a sufficient number of files uploaded to start executing
        this queue?"""
        IDs = self.queue_content(queue_name)
        filenames = [self.sequence_dir+"/"+ID for ID in IDs]
        uploaded_files = self.uploaded_files
        uploaded = all([filename in uploaded_files for filename in filenames])
        return uploaded

    def set_default_sequences(self,sequences=None):
        """Define what is executed when the sequencer queue is empty
        sequence: sequence object
        """
        if sequences is None: sequences = [Sequence()]
        queue_name = "queue1" if self.current_queue_name != "queue1" else "queue2"
        self.set_queue_sequences(
            sequences,
            queue_name,
            default_queue_name=queue_name,
            next_queue_name=queue_name,
        )

    def clear_default_packet(self):
        """This makes sure not sequence is executing when the sequencer queue
        is empty."""
        self.default_sequence_active = 0

    def get_interrupt_enabled(self):
        """Is the interrupt generator enabled?"""
        from timing_system import timing_system
        return timing_system.inton_sync.count == 1
    def set_interrupt_enabled(self,value):
        from timing_system import timing_system
        if bool(value) == False:
            timing_system.inton_sync.count = 0 
            timing_system.inton.count = 0 
        else: timing_system.inton.count = 1
    interrupt_enabled = property(get_interrupt_enabled,set_interrupt_enabled)
    enabled = interrupt_enabled

    def get_trigger_armed(self):
        """Is the system waiting  for an external trigger?"""
        from timing_system import timing_system
        armed = timing_system.inton.count == 1 \
            and timing_system.inton_sync.count == 0
        return armed
    def set_trigger_armed(self,value):
        """Is the system waiting  for an extrnal trigger?"""
        from timing_system import timing_system
        if bool(value) == True:
            timing_system.inton_sync.count = 0
            timing_system.inton.count = 1
        if bool(value) == False:
            timing_system.inton.count = 0
    trigger_armed = property(get_trigger_armed,set_trigger_armed)

    def timing_system_property(name):
        """Count value of a timing system register"""
        def get(self):
            from timing_system import timing_system
            return getattr(timing_system,name).count
        def set(self,value):
            from timing_system import timing_system
            getattr(timing_system,name).count = value
        return property(get,set)

    # 1-kHz clock cycles since restart of timing_system
    trigger_count = tclk_count = timing_system_property("tclk_count")
    sequence_count = intcount = timing_system_property("intcount")

    def driver_property(name,type=None,default_value=None,
        terminator="\n"):
        """sysfs-style kernel variable of sequencer driver"""
        driver_dir = "/proc/sys/dev/sequencer"
        def get(self):
            value = self.file(driver_dir+"/"+name)
            if type == str:
                if terminator:
                    if value.endswith(terminator):
                        value = value[0:-len(terminator)]
            elif type:
                try: value = type(value)
                except: value = default_value if default_value else type()
            return value
        def set(self,value):
            if type == str:
                if terminator:
                    if not value.endswith(terminator): value += terminator                                                                 
            elif type == bool: value = repr(int(value))
            elif type: value = repr(value)
            self.put_file(driver_dir+"/"+name,value)
        return property(get,set)

    def file_property(name,type=None,default_value=None,directory="",
        terminator=None):
        """sysfs-style kernel variable of sequencer driver"""
        def get(self):
            value = self.file(directory+"/"+name)
            if type == str:
                if terminator:
                    if value.endswith(terminator):
                        value = value[0:-len(terminator)]
            elif type:
                try: value = type(value)
                except: value = default_value if default_value else type()
            return value
        def set(self,value):
            if type == str:
                if terminator:
                    if not value.endswith(terminator): value += terminator                                                                 
            elif type == bool: value = repr(int(value))
            elif type: value = repr(value)
            self.put_file(directory+"/"+name,value)
        return property(get,set)

    sequence_active = driver_property("sequence_active",int,nan)
    default_sequence_active = driver_property("default_sequence_active",int,nan)
    queue_sequence_count = driver_property("queue_sequence_count",int,nan)
    current_queue_name = driver_property("queue_name",str,"")
    next_queue_name = driver_property("next_queue_name",str,"")
    next_queue_sequence_count = driver_property("next_queue_sequence_count",int,nan)
    default_queue_name = driver_property("default_queue_name",str,"")
    current_sequence_length = driver_property("current_sequence_length",int,nan)
    
    sequence_queue_interrupt_count_max = \
        driver_property("sequence_queue_interrupt_count_max",int,nan)
    sequence_queue_interrupt_count = \
        driver_property("sequence_queue_interrupt_count",int,nan)
    sequence_queue_packets = driver_property("sequence_queue_packets",int,nan)
    sequence_queue_bytes = driver_property("sequence_queue_bytes",int,nan)

    buffer_size = driver_property("buffer_size",int,nan)
    buffer_length = driver_property("buffer_length",int,nan)

    interrupt_handler_enabled = driver_property("interrupt_handler_enabled",int,nan)
    reset = driver_property("reset",int,nan)

    version = driver_property("version",str)
    debug_level = driver_property("debug_level",int,nan)

    __descriptor__ = cached_property(driver_property("descriptor",str),0.9)

    @property
    def descriptor(self):
        """Parameters of currently playing sequence as string"""
        from timing_system import timing_system
        value = timing_system.get_property("sequencer.descriptor")
        return value

    def get_queue_sequence_count(self):
        return self.queue_property(self.queue_name,"sequence_count")
    def set_queue_sequence_count(self,value):
        self.set_queue_property(self.queue_name,"sequence_count",value)
    queue_sequence_count = property(get_queue_sequence_count,
        set_queue_sequence_count)

    def get_current_queue_sequence_count(self):
        return self.queue_property(self.current_queue_name,"sequence_count")
    def set_current_queue_sequence_count(self,value):
        self.set_queue_property(self.current_queue_name,"sequence_count",value)
    current_queue_sequence_count = property(get_current_queue_sequence_count,
        set_current_queue_sequence_count)

    def get_queue_repeat_count(self):
        return self.queue_property(self.queue_name,"repeat_count")
    def set_queue_repeat_count(self,value):
        self.set_queue_property(self.queue_name,"repeat_count",value)
    queue_repeat_count = property(get_queue_repeat_count,
        set_queue_repeat_count)

    def get_current_queue_repeat_count(self):
        return self.queue_property(self.current_queue_name,"repeat_count")
    def set_current_queue_repeat_count(self,value):
        self.set_queue_property(self.current_queue_name,"repeat_count",value)
    current_queue_repeat_count = property(get_current_queue_repeat_count,
        set_current_queue_repeat_count)

    def get_queue_max_repeat_count(self):
        return self.queue_property(self.queue_name,"max_repeat_count")
    def set_queue_max_repeat_count(self,value):
        self.set_queue_property(self.queue_name,"max_repeat_count",value)
    queue_max_repeat_count = property(get_queue_max_repeat_count,
        set_queue_max_repeat_count)

    def get_current_queue_max_repeat_count(self):
        return self.queue_property(self.current_queue_name,"max_repeat_count")
    def set_current_queue_max_repeat_count(self,value):
        self.set_queue_property(self.current_queue_name,"max_repeat_count",value)
    current_queue_max_repeat_count = property(
        get_current_queue_max_repeat_count,
        set_current_queue_max_repeat_count)

    def queue_property(self,queue_filename,name):
        """name: "repeat_count" or "max_repeat_count" """
        if not queue_filename.startswith("/"):
            queue_filename = self.sequence_dir+"/"+queue_filename
        count = self.file(queue_filename+"_"+name)
        try: count = int(count)
        except: count = nan
        return count
    
    def set_queue_property(self,queue_filename,name,value):
        """name: "repeat_count" or "max_repeat_count" """
        if not queue_filename.startswith("/"):
            queue_filename = self.sequence_dir+"/"+queue_filename
        string = "%r" % value if not isnan(value) else ""
        string = string.ljust(20) # leave room for growth
        if string != "": string += "\n"
        self.put_file(queue_filename+"_"+name,string)

    @property
    def uploaded_files(self):
        """Full pathnames of files on the timing system's file system"""
        return self.files(self.sequence_dir+"/*")

    def files(self,pattern):
        """List of filenames on the timing system's file system
        pattern: e.g. '/tmp/sequence-*.bin' """
        # Work-around for buffer overflow in wildcard expansion
        # on server side (if directory contains 5520 entries).
        if pattern.endswith("/*"):
            directory = pattern[:-2]
            from file_server import wget
            filelist = wget("//"+self.ip_address+directory)
            files = filelist.strip("\n").split("\n") if len(filelist)>0 else []
            files = [directory+"/"+f for f in files]
        else:
            from file_server import wdir
            filelist = wdir("//"+self.ip_address+pattern)
            files = filelist.strip("\n").split("\n") if len(filelist)>0 else []
        return files

    def file(self,filename):
        """The content of a file on the timing system's file system
        filename: e.g. '/proc/sys/dev/seqeuncer/interrupt_enabled' """
        from file_server import wget
        if filename:
            content = wget("//"+self.ip_address+filename)
            ##debug("timing_sequencer: %s: %.20r..." % (filename,content))
        else: content = ""
        return content

    def remove(self,filename):
        """Delete a file from the timing system's file system
        filename: e.g. '/tmp/sequence/cache' """
        from file_server import wdel
        wdel(self.ip_address+filename)

    def put_file(self,filename,content):
        """Put file to the file system if the timing system"""
        report_if_not_valid_pathname(filename)
        from file_server import wput,wdel
        if len(content) > 0: wput(content,self.ip_address+filename)
        else: wdel(self.ip_address+filename)

    def put_files(self,filenames,contents):
        """Group transfer of serveral files to the file system if the timing
        system"""
        if len(filenames) > 0:
            s = "Transferring %d files:\n" % len(filenames)
            for i in range(0,min(len(filenames),2)):
                s += " %s: %d bytes\n" % (filenames[i],len(contents[i]))
            ##debug(s)
            from time import time
            self.last_filenames = filenames
            n = sum([len(content) for content in contents])
            t0 = time()
            debug("Transferring %d bytes of data to timing system" % n)
            for (filename,content) in zip(filenames,contents):
                self.put_file(filename,content)
            dt = time()-t0
            debug("Transferred %d bytes in %.3f s (%.0f bytes/s)" % (n,dt,float(n)/dt))

    def telnet(self,command):
        """Execute a system command on the timing system's CPU and return
        the result"""
        from telnet import telnet
        return telnet(self.ip_address,command)

    cache_enabled = persistent_property("cache_data",True)

    def cache_set(self,key,data):
        """Temporarily store binary data for fast restreival
        key: string"""
        from os.path import exists,dirname;
        from os import makedirs
        for filename in self.cache_filenames(key):
            if not exists(dirname(filename)): makedirs(dirname(filename))
            try: file(filename,"wb").write(data); break
            except: pass

    def cache_get(self,key):
        """Retreive temporarily stored binary data
        key: string"""
        data = ""
        for filename in self.cache_filenames(key):
            try: data = file(filename,"rb").read(); break
            except: pass
        return data

    def cache_clear(self):
        """Erase temporarily stored binary data on the locate drive"""
        from shutil import rmtree
        try: rmtree(self.cache_dir)
        except: pass

    def get_cache_size(self):
        """How many cached data objects are there?"""
        from os import listdir
        try: return len(listdir(self.cache_dir))
        except: return 0
    def set_cache_size(self,value):
        if value == 0: self.cache_clear()
    cache_size = property(get_cache_size,set_cache_size)

    def cache_filenames(self,key):
        """Where to store the data associated with key"""
        # If the key exceeds 254 characters, it needs to be shortened
        # by hashing, otherwise the file system would not allow it
        # to be used as a filename.
        filenames = []
        filename = self.cache_dir+"/"+key
        if valid_pathname(filename): filenames += [filename]
        filenames += [self.cache_dir+"/"+hash(key)] 
        return filenames

    @property
    def cache_dir(self):
        """Where to store temparary files"""
        from tempfile import gettempdir
        basedir = gettempdir()
        dir = basedir+"/sequencer/cache"
        return dir

    def get_remote_cache_size(self):
        """How many sequences are stored in the memory of the FPGA timing
        system?"""
        return len(self.remote_sequence_files)
    def set_remote_cache_size(self,value):
        if value == 0:
            for file in self.remote_sequence_files: self.remove(file)
    remote_cache_size = property(get_remote_cache_size,set_remote_cache_size)

    @property
    def remote_sequence_files(self):
        """Which sequences are stored in the memory of the FPGA timing system?"""
        files = self.files(self.sequence_dir+"/*")
        ## /tmp/sequencer_fs/f0e55f6b071d6b1f0cc341b2cce2451e
        from re import match,compile
        pattern = compile("^"+self.sequence_dir+"/"+"[0-9a-f]{32}$")
        files = [file for file in files if match(pattern,file)]
        return files

    def update(self):
        """Execute sequence using the current default parameters"""
        self.set_default_sequences()
        self.interrupt_enabled = True

    def acquire(self,delays=None,laser_on=None,
        waitt=None,npulses=None,burst_waitt=None,burst_delay=None,
        ms_on=None,s3_on=None,
        xdet_on=None,xosct_on=None,losct_on=None,trans_on=None,lcam_on=None,
        image_numbers=None,
        xatt_on=None):
        """For data acquisition
        delays: list of laser pump to X-ray probe time in seconds
        laser_on: Trigger the ps laser? True or False
        nst_on: Trigger the ns laser? True or False
        image_numbers: series number
        ms_on: Open X-ray millisecond shutter? True or False
        xatt_on: Attenuate X-ray beam? True or False
        """
        debug("Timing Sequencer: Building sequence list...")
        from timing_system import timing_system
        timing_system.clear_cache(); timing_system.cache += 1
            
        var_lists = delays,laser_on,waitt,npulses,burst_waitt,burst_delay,\
            image_numbers,ms_on,xatt_on,s3_on,trans_on
        
        if to_tuple(var_lists) not in self.sequence_cache:
            from numpy import nan,isnan,where
            N = 0
            for var_list in var_lists:
                if var_list is not None: N = len(var_list)
            
            if xatt_on is not None: s3_on = xatt_on        
            
            if delays is None: delays = [nan]*N
            if laser_on is None: laser_on = [nan]*N
            if waitt is None: waitt = [nan]*N
            if npulses is None: npulses = [nan]*N
            if burst_waitt is None: burst_waitt = [nan]*N
            if burst_delay is None: burst_delay = [nan]*N
            if image_numbers is None: image_numbers = [nan]*N
            if ms_on is None: ms_on = [1]*N
            if s3_on is None: s3_on = [0]*N
            if xdet_on is None: xdet_on = [1]*N
            if xosct_on is None: xosct_on = [1]*N
            if losct_on is None: losct_on = [1]*N
            if trans_on is None: trans_on = [1]*N
            if lcam_on is None: lcam_on = laser_on

            # Optimize image numbering
            image_number_inc = [i==0 or image_numbers[i] == image_numbers[i-1]+1
                                for i in range(0,N)]
            image_numbers = where(image_number_inc,nan,image_numbers)

            sequences = []
            for i in range(0,N):
                sequences += [Sequence(
                    delay=delays[i],
                    laser_on=laser_on[i],
                    waitt=waitt[i],
                    npulses=npulses[i],
                    burst_waitt=burst_waitt[i],
                    burst_delay=burst_delay[i],
                    ms_on=ms_on[i],
                    s3_on=s3_on[i],
                    xdet_on=xdet_on[i],
                    xosct_on=xosct_on[i],
                    losct_on=losct_on[i],
                    lcam_on=lcam_on[i],
                    trans_on=trans_on[i],
                    pass_number=1,
                    image_number=image_numbers[i],
                    image_number_inc=image_number_inc[i],
                    acquiring=1,
                )]
            self.sequence_cache[to_tuple(var_lists)] = sequences
    
        sequences = self.sequence_cache[to_tuple(var_lists)]
        self.set_queue_sequences(sequences)

        timing_system.cache -= 1

    def acquisition_start(self):
        """To be called after 'acquire'"""
        self.queue_active = False
        self.wait_for_queue_ready()
        self.image_number = 0
        self.pass_number = 0
        self.pulses = 0
        self.queue_active = True

    def acquisition_cancel(self):
        """End current data collection"""
        self.acquiring = False

    sequence_cache = {}

    def __repr__(self): return "timing_sequencer"

timing_sequencer = TimingSequencer()

def to_tuple(X):
    return tuple([tuple(x) if x is not None else None for x in X])
    
def sequencer_packet(registers,counts,descriptor=None):
    """Binary data packet for the timing sequencer (for one image for example)
    registers: list of timing register objects
    counts: list of interger arrays, one array for each register
    """
    # Find the times when register counts change.
    N = max([len(c) for c in counts])

    from timing_system import timing_system
    period = timing_system.hlc_div # 247 Hz: 4, 82.3 Hz: 12

    packets = {}

    def append(packets,key,data):
        packets[key] = packets.get(key,"")+data

    from sparse_array import starts

    for ireg in range(0,len(registers)):
        register = registers[ireg]
        name = register.name

        # Change registers
        if not name.endswith("_count"): # ordinary register
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = write_packet(register,count)
                append(packets,(it,ireg),packet)
        if name.endswith("_count"): # count register
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = increment_packet(register,count)
                append(packets,(it,ireg),packet)

        # Generate reports
        if name == timing_system.xdet.state.name:
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = report_packet(register)
                append(packets,(it,ireg),packet)
        if name.endswith("_count"):
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                if count != 0:
                    packet = report_packet(register)
                    append(packets,(it,ireg),packet)
        if name.endswith("_acq"):
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = report_packet(register)
                append(packets,(it,ireg),packet)
        if name  == "image_number":                    
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = report_packet(register)
                append(packets,(it,ireg),packet)
        if name == "image_number_inc":
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                if count != 0:
                    packet = report_packet(timing_system.image_number)
                    append(packets,(it,ireg),packet)
        if name  == "pass_number":
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = report_packet(register)
                append(packets,(it,ireg),packet)
        if name == "pass_number_inc":
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                if count != 0:
                    packet = report_packet(timing_system.pass_number)
                    append(packets,(it,ireg),packet)
        if name  == "acquiring":
            for it in starts(counts[ireg]):
                count = counts[ireg][it]
                packet = report_packet(register)
                append(packets,(it,ireg),packet)

    # Assemble packets in correct sequence order
    interrupt_data = [""]*N
    if N>0:
        interrupt_data[0] += interrupt_count_packet(N)
        if descriptor: interrupt_data[0] += descriptor_packet(descriptor)
    for it in range(0,N):
        for ireg in range(0,len(registers)):
            if (it,ireg) in packets: interrupt_data[it] += packets[it,ireg]
        interrupt_count = (it+1) % period
        interrupt_data[it] += interrupt_packet(interrupt_count,period)

    data = ""
    data += index_packets(interrupt_data)
    for it in range(0,N): data += interrupt_data[it]

    return data

def packet(type=0,payload=""):
    """Timing sequencer instruction
    Return value: binary data
    """
    if isinstance(type,str): type = type_codes[type]
    from struct import pack
    fmt = ">BBH"
    version = 1
    header_size = len(pack(fmt,type,version,0))
    length = header_size+len(payload)
    data = pack(fmt,type,version,length)+payload
    return data

def interrupt_packet(interrupt_count,period):
    """Timing sequencer instruction to wait for an interrupt
    Format: type (8bits),version (8bits),length (16bits),
      interrupt count (8bits),period (8bits)
    Return value: binary data as string, length: 6 bytes
    """
    from struct import pack
    data = packet("interrupt",pack(">BB",interrupt_count,period))
    return data

def write_packet(register,count):
    """Timing sequencer instruction to write a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),value (32bits), total 16 bytes
    register: e.g. pson
    count: integer number
    Return value: binary data as string
    """
    from struct import pack
    count_bitmask = ((1 << register.bits) - 1)
    converted_count = toint(count) & count_bitmask
    if converted_count != count:
        warn("register %r, mask 0x%X: converting count %r to %r" %
            (register,count_bitmask,count,converted_count))
    count = converted_count
    bitmask = count_bitmask << register.bit_offset
    address = register.address
    bit_count = count << register.bit_offset
    data = packet("write",pack(">III",address,bitmask,bit_count))
    return data

def increment_packet(register,count):
    """Timing sequencer instruction to write a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),value (32bits), total 16 bytes
    register: e.g. pson
    count: integer number
    Return value: binary data as string
    """
    if count != 0:
        ##debug("timing_seqence: increment_packet(%r,%r)" % (register,count))
        from struct import pack
        count_bitmask = ((1 << register.bits) - 1)
        if count != toint(count) & count_bitmask:
            warn("write_packet(%r,%r): converting count to %r" %
                (register,count,toint(count) & count_bitmask))
        count = toint(count) & count_bitmask
        bitmask = count_bitmask << register.bit_offset
        address = register.address
        bit_count = count << register.bit_offset
        data = packet("increment",pack(">III",address,bitmask,bit_count))
    else: data = ""
    return data

def descriptor_packet(descriptor):
    """Timing sequencer instruction
    descriptor: Parameter list as string
    Format: type (8bits),version (8bits),length (16bits),
      string(variable length)
    Return value: binary data as string
    """
    data = packet("descriptor",descriptor)
    return data

def output_packet(message):
    """Timing sequencer instruction
    message: string
    Format: type (8bits),version (8bits),length (16bits),
      string(variable length)
    Return value: binary data as string
    """
    data = packet("output",message)
    return data

def sequence_length_packet(sequence_length):
    """How long is the sequence of instructions following in bytes?
    Timing sequencer instruction
    sequence_length: interger, number of bytes
    Format: type (8bits),version (8bits),length (16bits),
      packet_length(32 bits)
    Return value: binary data as string, length: 8 bytes
    """
    from struct import pack
    data = packet("sequence length",pack(">I",sequence_length))
    return data

def interrupt_count_packet(interrupt_count):
    """How long will the sequence of instructions following take to execute?
    Timing sequencer instruction
    packet_length: interger, number of bytes
    Format: type (8bits),version (8bits),length (16bits),
      packet_length(32 bits)
    Return value: binary data as string, length: 8 bytes
    """
    from struct import pack
    data = packet("interrupt count",pack(">I",interrupt_count))
    return data

def report_packet(register):
    """Timing sequencer instruction to report the value of a register
    Format: type (8bits),version (8bits),length (16bits),
      address (32bits),bitmask (32bits),string(variable length)
    register: object e.g. timing_system.image_number
    count: integer number
    Return value: binary data as string
    """
    from struct import pack
    count_bitmask = ((1 << register.bits) - 1)
    bitmask = count_bitmask << register.bit_offset
    address = register.address
    name = register.name
    data = packet("report",pack(">II",address,bitmask) + name)
    return data

def index_packets(interrupt_data):
    """Table of offsets encoded as binary data.
    May be multiple packets if maximum packet size is exceeded."""
    # How many offsets can be stored in an index packet?
    header_size = len(packet())
    from struct import pack
    offset_size = len(pack(">I",0))
    max_packet_size = 2**16-1
    max_payload_size = max_packet_size - header_size
    N_max = max_payload_size/offset_size

    N = len(interrupt_data)
    total_length = 0
    for it0 in range(0,N,N_max):
        n = min(N-it0,N_max)
        total_length += header_size + n*offset_size

    offset = total_length
    data = ""
    for it0 in range(0,N,N_max):
        index_data = ""
        n = min(N-it0,N_max)
        for it in range(it0,it0+n):
            index_data += pack(">I",offset)
            offset += len(interrupt_data[it])
        data += packet("index",index_data)

    assert len(data) == total_length

    return data

def descriptor(data):
    """Parameter list as string
    data: binary data a string"""
    from struct import unpack
    descriptor = ""
    i = 0
    while i < len(data):
        type,version,length = unpack(">BBH",data[i:i+4])
        if type == 3:
            payload = data[i+4:i+length]
            descriptor = payload
            break
        i += length
    return descriptor

def packet_representation(data):
    """String
    data: binary data a string"""
    from struct import unpack,pack
    text = ""
    i = 0
    interrupt_count = 0
    while i < len(data):
        type,version,length = unpack(">BBH",data[i:i+4])
        header_size = len(packet())
        payload = data[i+header_size:i+length]
        type_name = type_names.get(type,"unknown")
        payload_repr = ""
        if type_name == "interrupt":
            count,period = unpack(">BB",payload)
            payload_repr = "%r/%r" % (count,period)
            interrupt_count += 1
        if type_name == "write":
            address,bitmask,bit_count = unpack(">III",payload)
            payload_repr = "addr=0x%08X, mask=0x%08X, count=0x%08X" \
                % (address,bitmask,bit_count)
        if type_name == "increment":
            address,bitmask,bit_count = unpack(">III",payload)
            payload_repr = "addr=0x%08X, mask=0x%08X, count=0x%08X" \
                % (address,bitmask,bit_count)
        if type_name == "descriptor":
            descriptor = payload
            payload_repr = descriptor.replace(",",",\n").strip("\n")
        if type_name == "output":
            output = payload
            payload_repr = "%r" % output
        if type_name == "sequence length":
            sequence_length, = unpack(">I",payload)
            payload_repr = "%r bytes" % sequence_length
        if type_name == "interrupt count":
            count, = unpack(">I",payload)
            payload_repr = "%r total" % count
        if type_name == "report":
            address,bitmask = unpack(">II",payload[0:8])
            name = payload[8:]
            payload_repr = "addr=0x%08X, mask=0x%08X, name=%r" \
                % (address,bitmask,name)
        if type_name == "index":
            offset_size = len(pack(">I",0))
            N = len(payload)/offset_size
            addresses = []
            for j in range(0,N):
                 address = unpack(">I",payload[j*offset_size:(j+1)*offset_size])
                 addresses += ["%6d" % address]
            payload_repr = []
            for j in range(0,N,8):
                payload_repr += [",".join(addresses[j:j+8])]
            payload_repr = "\n".join(payload_repr)
        prefix = "%-5d: %-4d %-15s " % (i,interrupt_count,type_name)
        lines = payload_repr.split("\n")
        for line in lines[:1]: text += prefix + abbreviate(line) + "\n"
        for line in lines[1:]: text += " "*len(prefix) + abbreviate(line) + "\n"
        i += length
    return text

def abbreviate(text,max_length = 240):
    """Shorten a string indixcating omitted part using elipsis ('...')"""
    if len(text) > max_length:
        text = text[0:max_length-16-3]+"..."+text[-16:]
    return text
    

type_codes = {
    "interrupt": 0,
    "write": 1,
    "increment": 2,
    "descriptor": 3,
    "output": 4,
    "sequence length": 5,
    "interrupt count": 6,
    "report": 7,
    "index": 8,
}

type_names =  dict(zip(type_codes.values(),type_codes.keys()))

def toint(x):
    """Force conversion to integer"""
    try: return int(x)
    except: return 0

def hash(text):
    """Calcualte the hash of a string, using the MD5 (Message Digest version 5)
    alorithm.
    Return value: ACSCII encoded hexadecimal number of 32 digits"""
    import hashlib
    m = hashlib.md5()
    m.update(text)
    hash = m.hexdigest()
    return hash

def instantiate(x): return x()

@instantiate
class lxd(object):
    """Laser to X-ray time delay"""
    name = "lxd"
    timeout = 2.0
    from numpy import nan
    __new_value__ = nan
    __last_move__ = 0
    
    def get_value(self): return timing_sequencer.delay
    def set_value(self,value):
        from time import time
        timing_sequencer.delay = value
        self.__new_value__ = value
        self.__last_move__ = time()
    value = property(get_value,set_value)

    def get_moving(self):
        from time import time
        moving = timing_sequencer.delay != self.__new_value__ and \
            time() <= self.__last_move__ + self.timeout
        return moving
    def set_moving(self,value): pass
    moving = property(get_moving,set_moving)

def hexdump(data):
    """Print string as hexdecimal numbers
    data: string"""
    s = ""
    for x in data: s += "%02X " % ord(x)
    return s

def report_if_not_valid_pathname(filename):
    """Report if this filename is not usable on Embedded uClinux 2.2."""
    if not valid_pathname(filename):
        warn("%r contains part of %d characters, exceeding liit of 254." %
            (filename,longest_pathname_component(filename)))

def valid_pathname(filename):
    """Is this filename is not usable on Linux or MacOS?"""
    valid = (longest_pathname_component(filename) <= 254)
    return valid

def longest_pathname_component(filename):
    n = max([len(x) for x in filename.split("/")])
    return n


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s %(levelname)s: %(message)s")
    ##import timing_system as t; t.DEBUG = True
    from timing_system import timing_system
    from numpy import arange
    from time import time,sleep # for timing
    from Ensemble_SAXS_pp import Ensemble_SAXS
    from timing_system import timing_system

    ##sequence = Sequence()
    ##self = sequence # for debugging
    self = timing_sequencer # for debugging
    i = 23 # channel number
        
    print('timing_system.prefix = %r' % timing_system.prefix)
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('')
    ##print('registers,counts = Sequence().register_counts')
    ##print('')
    ##print('timing_sequencer.cache_size = 0')
    ##print('timing_sequencer.update()')
    ##print('timing_sequencer.running = False')
    ##print('timing_sequencer.running = True')
    print('print packet_representation(index_packets([""]*2))')
    print('print packet_representation(descriptor_packet("x=1,y=2"))')
