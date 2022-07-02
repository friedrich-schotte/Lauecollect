"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-11
Revision comment:
"""
__version__ = "1.0"

from logging import debug, error


class Configuration(object):
    """Settings"""

    parameters = [
        "clk_src.count",  # Bunch clock source [0=RF IN,1=Ch1,...24=Ch24,25=RJ45:1,29=350MHz]
        "clock_period_external",
        "clock_period_internal",
        "clk_on.count",  # Clock manager [0=bypassed, 1=enabled]
        "clk_mul.count",  # Clock multiplier [0=N/A,1=2,2=3,...31=32]
        "clk_div.count",  # Clock divider [0=1,1=2,2=3,...7=8]
        "clk_dfs_mode.count",  # Clock DFS frequency mode [0=low freq,1=high freq]
        "clk_dll_mode.count",  # Clock DLL frequency mode [0=low freq,1=high freq]
        "sbclk_src.count",  # Single-bunch clock source [1=Ch1,...24=Ch24,27=RJ45:3]
        "clk_shift_stepsize",  # Clock shift step size
        "clk_88Hz_div_1kHz.count",  # 1-kHz clock divider of RF/4
        "p0_phase_1kHz.count",  # 1-kHz clock phased by SB clock?
        "p0_div_1kHz.count",  # 1-kHz clock divider of SB clock
        "hlc_src.count",  # Heatload chopper encoder in
        "hlc_div",
        "nsl_div",
        "p0fd2.count",
        "p0d2.count",
        "p0_shift.offset",
        "psod3.offset",
        "hlcnd.count",
        "hlcnd.offset",
        "hlcad.offset",
        "hlctd.offset",
    ]
    channel_parameters = [
        "PP_enabled",
        "input.count",
        "description",
        "mnemonic",
        "special",
        "specout.count",
        "offset_HW",
        "offset_sign",
        "pulse_length_HW",
        "offset_PP",
        "pulse_length_PP",
        "counter_enabled",
        "enable.count",
        "timed",
        "gated",
        "override.count",
        "state.count",
    ]

    def __init__(self, timing_system, name):
        """name: 'BioCARS', or 'LaserLab'"""
        self.timing_system = timing_system
        self.name = name

    def save(self):
        """Store current FPGA settings on local file system"""
        debug("Configuration %r saving..." % self.name)
        from DB import dbval, dbset

        for par in self.parameters:
            value = eval("self.timing_system." + par)
            db_name = "timing_system_configurations/%s.%s" % (self.name, par)
            if not equal(value, dbval(db_name)):
                debug("dbset(%r,%r)" % (db_name, value))
                dbset(db_name, value)
        for channel in self.timing_system.channels:
            for name in self.channel_parameters:
                value = eval("channel." + name)
                db_name = "timing_system_configurations/%s.%s.%s" % (
                    self.name,
                    channel.name,
                    name,
                )
                if not equal(value, dbval(db_name)):
                    debug("dbset(%r,%r)" % (db_name, value))
                    dbset(db_name, value)
        debug("Configuration %r saved." % self.name)

    def load(self):
        """Upload save settings to FPGA timing system"""
        debug("Configuration %r loading..." % self.name)
        from DB import db
        from numpy import nan, inf  # noqa - needed for eval

        for par in self.parameters:
            default_value = eval("self.timing_system.%s" % par)
            value = db(
                "timing_system_configurations/%s.%s" % (self.name, par), default_value
            )
            if not equal(value, default_value):
                execute(
                    "self.timing_system.%s = %r" % (par, value),
                    locals=locals(),
                    globals=globals(),
                )
        for channel_name in self.timing_system.channel_names:
            for name in self.channel_parameters:
                default_value = eval("self.timing_system.%s.%s" % (channel_name, name))
                db_name = "timing_system_configurations/%s.%s.%s" % (
                    self.name,
                    channel_name,
                    name,
                )
                value = db(db_name, default_value)
                if not equal(value, default_value):
                    execute(
                        "self.timing_system.%s.%s = %r" % (channel_name, name, value),
                        locals=locals(),
                        globals=globals(),
                    )
        debug("Configuration %r loaded." % self.name)

    def __repr__(self):
        return "%s(%r,%r)" % (type(self).__name__, self.timing_system, self.name)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


def execute(command, locals=None, globals=None):
    from numpy import nan, inf  # noqa - needed for exec

    debug("Executing %r" % command)
    try:
        exec(command, locals, globals)
    except Exception as msg:
        error("Executing %r failed: %s" % (command, msg))


def equal(a, b):
    """Do a and b have the same value?"""
    return repr(a) == repr(b)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
