"""
Stanford Research Systems 4-channel Delay Generatator DG535

Setup:
MacBook Pro "NIH-Instrumentation" (Windows 7) -> USB 4-port hub, port 4
-> TAMS USB GPIB interface -> DG535

Configuration:
MacBook Pro "NIH-Instrumentation":
- Installed Agilent I/O Library Suite 16.3.17914 from agilent.com/find/iosuite
- Installed TAMS USB-GPIB driver 2.0 from tamsinc.com/hpib/support
- C:\Program Files\Agilent\IO Libraries Suite\bin\iocfg32.exe -
  Available Interface Types - GPIB *TAMS 63488 USB/GPIB
  Configured nterfaces - VISA name: GPIB0 SICL Name: gpib0 - Edit...
  Edit VISA Config... - Add device - GPIB0::1
DG535:
- GPIB - GPIB Address = 1

Friedrich Schotte 11 Aug 2014 - 12 Aug 2014
"""
__version__ = "1.0.2"

import visa

class GpibInstrument(visa.GpibInstrument):
    """GPIB instrument
    This class contains a waork-around for a bug in the VISA library."""
    def write(self,message):
        visa.GpibInstrument.write(self,self.pad_string(message))

    ##def ask(self,message):
    ##    return visa.GpibInstrument.ask(self,self.pad_string(message))

    @staticmethod
    def pad_string(s):
        """Work-aound for a bug in the VISA library which causes every
        odd character, except the last, to be lost when sending to a GPIB
        instrument:
        e.g. "012345678" -> "02468",  "0123456789" -> "024689" """
        return ".".join(s)

class DG535_Instrument(GpibInstrument):
    """Stanford Research Systems Delay Generatator"""
    def start_burst(self,npulses):
        """Generate a series of trigger pulses.
        npulses: number of trigger pulses per burst
        waitt: pulse spacing in seconds
        """
        from time import sleep
        period = 1/self.burst_frequency
        duration = (npulses-1)*period
        # Force the burst counter to reset to avoid the long delay at
        # the end of the burst.
        self.trigger_mode = "external"
        self.burst_period_count = npulses+1
        self.burst_count = npulses
        self.trigger_mode = "burst"
        # Add long delay at the end to make sure that no more than one burst is
        # generated.
        self.burst_period_count = 32000

    def start_burst(self,npulses):
        """Generate a series of trigger pulses.
        npulses: number of trigger pulses per burst
        waitt: pulse spacing in seconds
        """
        self.write("TM1;BP%d;BC%d;TM3;BP32000"% (npulses-3+1,npulses-3))

    def get_burst_frequency(self):
        """Trigger rate when using "burst" trigger mode, in Hz"""
        return tofloat(self.ask("TR 1"))
    def set_burst_frequency(self,value):
        self.write("TR 1,%g" % value)
    burst_frequency = property(get_burst_frequency,set_burst_frequency)

    def get_burst_count(self):
        """Number of trigger pulses generated per burst"""
        return toint(self.ask("BC"))
    def set_burst_count(self,value):
        self.write("BC %d" % value)
    burst_count = property(get_burst_count,set_burst_count)

    def get_burst_period_count(self):
        """Repetiton period in burst mode in number of burst periods
        Must be at least burst_count+1."""
        return toint(self.ask("BP"))
    def set_burst_period_count(self,value):
        self.write("BP %d" % value)
    burst_period_count = property(get_burst_period_count,set_burst_period_count)

    def get_trigger_frequency(self):
        """Trigger rate when using internal trigger, in Hz"""
        return tofloat(self.ask("TR 0"))
    def set_trigger_frequency(self,value):
        self.write("TR 0,%g" % value)
    trigger_frequency = property(get_trigger_frequency,set_trigger_frequency)

    trigger_modes = {
        0: "internal",
        1: "external",
        2: "single shot",
        3: "burst",
        4: "line",
    }
    def get_trigger_mode(self):
        """Trigger rate when using internal trigger, in Hz"""
        code = toint(self.ask("TM"))
        if code in self.trigger_modes: value = self.trigger_modes[code]
        else: value = "?"
        return value
    def set_trigger_mode(self,value):
        modes = dict(zip(self.trigger_modes.values(),self.trigger_modes.keys()))
        if value in modes:
            code = modes[value]
            self.write("TM %d" % code)
    trigger_mode = property(get_trigger_mode,set_trigger_mode)


def toint(x):
    """Convert x to a floating point number.
    If not convertible return zero"""
    try: return int(x)
    except: return 0

def tofloat(x):
    """Convert x to a floating point number.
    If not convertible return 'Not a Number'"""
    from numpy import nan
    try: return float(x)
    except: return nan


DG535 = DG535_Instrument("GPIB0::1::INSTR")

if __name__ == "__main__": # for testing
    self = DG535
    print('DG535.start_burst(41)')
    print('DG535.burst_frequency = 41')
