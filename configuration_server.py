"""
Data base to save and recall motor positions
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2019-05-28
"""
__version__ = "1.0.2" # setattr: handle exception

from logging import debug,info,warn,error
from traceback import format_exc

class Configuration_Server(object):
    prefix = "NIH:CONF"

    global_properties = [
        "configuration_names",
    ]

    configuration_properties = [
        "value",
        "values",
        "command_value",
        "title",
        "description",
        "matching_description",
        "closest_descriptions",
        "command_description",
        "command_rows",
        "matching_rows",
        "closest_rows",
        "n_motors",
        "descriptions",
        "updated",
        "formats",
        "nrows",
        "name",
        "motor_names",
        "names",
        "motor_labels",
        "widths",
        "formats",
        "tolerance",
        "description_width",
        "row_height",
        "show_apply_buttons",
        "apply_button_label",
        "show_define_buttons",
        "define_button_label",
        "show_stop_button",
        "serial",
        "vertical",
        "multiple_selections",
        "are_configuration",
        "motor_configuration_names",
        "are_numeric",
        "current_timestamp",
        "applying",
        "show_in_list",
    ]
    motor_properties = [
        "current_position",
        "positions",
        "positions_match",
    ]

    def run(self):
        from time import sleep
        while True:
            self.update()
            sleep(0.02)

    def update(self):
        from CAServer import casput,casmonitor
        from configuration_driver import configuration
        for prop in self.global_properties:
            PV_name = (self.prefix+"."+prop).upper()
            try: value = getattr(configuration,prop)
            except Exception,msg:
                error("%s: %s\n%s" % (prop,msg,format_exc()))
                value = None
            if value is not None:
                casput(PV_name,value)
                casmonitor(PV_name,callback=self.monitor)
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                PV_name = (self.prefix+"."+conf.name+"."+prop).upper()
                try: value = getattr(conf,prop)
                except Exception,msg:
                    error("%s.%s: %s\n%s" % (conf,prop,msg,format_exc()))
                    value = None
                if value is not None:
                    casput(PV_name,value)
                    casmonitor(PV_name,callback=self.monitor)
            for prop in self.motor_properties:
                for motor_num in range(0,conf.n_motors):
                    PV_name = (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper()
                    try: value = getattr(conf,prop)[motor_num]
                    except Exception,msg:
                        error("%s.%s[%r]: %s\n%s" % (conf,prop,motor_num,msg,format_exc()))
                        value = None
                    if value is not None:
                        casput(PV_name,value)
                        casmonitor(PV_name,callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from configuration_driver import configuration
        from CAServer import casput
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                if PV_name == (self.prefix+"."+conf.name+"."+prop).upper():
                    try: setattr(conf,prop,value)
                    except Exception,msg:
                        error("%s.%s = %r: %s\n%s" % (conf,prop,value,msg,format_exc()))
                    try: value = getattr(conf,prop)
                    except Exception,msg:
                        error("%s.%s: %s\n%s" % (conf,prop,msg,format_exc()))
                        value = None
                    if value is not None: casput(PV_name,value)
            for motor_num in range(0,conf.n_motors):
                for prop in self.motor_properties:
                    if PV_name == (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper():
                        try: getattr(conf,prop)[motor_num] = value
                        except Exception,msg:
                            error("%s.%s[%r] = %r: %s\n%s" % (conf,prop,motor_num,value,msg,format_exc()))
                        try: value = getattr(conf,prop)[motor_num]
                        except Exception,msg:
                            error("%s.%s[%r]: %s\n%s" % (conf,prop,motor_num,msg,format_exc()))
                            value = None
                        if value is not None: casput(PV_name,value)
        

configuration_server = Configuration_Server()
    
if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    from time import time # for performance testing
    import logging
    for h in logging.root.handlers[:]: logging.root.removeHandler(h)
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    print("configuration_server.update()")
    print("t=time(); configuration_server.update(); time()-t")
    print("configuration_server.run()")
