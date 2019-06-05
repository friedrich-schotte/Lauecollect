"""
Data base to save and recall motor positions
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2019-05-31
"""
__version__ = "1.0.5" # issue: __builtins__.getattr: 'dict' object has no attribute 'getattr'
# Solution: made setattr, getattr static methods

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
            value = self.getattr(configuration,prop,expand=True)
            if value is not None:
                casput(PV_name,value,update=False)
                casmonitor(PV_name,callback=self.monitor)
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                PV_name = (self.prefix+"."+conf.name+"."+prop).upper()
                value = self.getattr(conf,prop,expand=True)
                if value is not None:
                    casput(PV_name,value,update=False)
                    casmonitor(PV_name,callback=self.monitor)
            for prop in self.motor_properties:
                for motor_num in range(0,conf.n_motors):
                    PV_name = (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper()
                    value = self.getitem(self.getattr(conf,prop),motor_num)
                    if value is not None:
                        casput(PV_name,value,update=False)
                        casmonitor(PV_name,callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from configuration_driver import configuration
        from CAServer import casput
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                if PV_name == (self.prefix+"."+conf.name+"."+prop).upper():
                    self.setattr(conf,prop,value)
                    value = self.getattr(conf,prop,expand=True)
                    if value is not None: casput(PV_name,value,update=False)
            for motor_num in range(0,conf.n_motors):
                for prop in self.motor_properties:
                    if PV_name == (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper():
                        self.setitem(self.getattr(conf,prop),motor_num,value)
                        value = self.getitem(self.getattr(conf,prop),motor_num)
                        if value is not None: casput(PV_name,value,update=False)
        
    def global_PV_name(self,prop):
        return (self.prefix+"."+prop).upper()

    def configuration_PV_name(self,conf,prop):
        return (self.prefix+"."+conf.name+"."+prop).upper()

    def motor_PV_name(self,conf,prop,motor_num):
        return (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper()

    @staticmethod
    def getattr(obj,property_name,expand=False):
        try: value = getattr(obj,property_name)
        except Exception,msg:
            error("%s.%s: %s\n%s" % (obj,property_name,msg,format_exc()))
            value = None
        if expand:
            if hasattr(value,"__getitem__"):
                try: value = value[:]
                except: warn("%s.%s[:]: %s\n%s" % (obj,property_name,msg,format_exc()))
        return value

    @staticmethod
    def setattr(obj,property_name,value):
        debug("setattr(%r,%r,%r)" % (obj,property_name,value))
        try: setattr(obj,property_name,value)
        except Exception,msg:
            error("%s.%s = %r: %s\n%s" % (obj,property_name,value,msg,format_exc()))

    @staticmethod
    def getitem(obj,i):
        try: value = obj[i]
        except Exception,msg:
            error("%s[%r]: %s\n%s" % (obj,i,msg,format_exc()))
            value = None
        if hasattr(value,"__getitem__"):
            try: value = value[:]
            except: warn("%s.%s[:]: %s\n%s" % (obj,property_name,msg,format_exc()))
        return value

    @staticmethod
    def setitem(obj,i,value):
        debug("setitem(%r,%r,%r)" % (obj,i,value))
        try: obj[i] = value
        except Exception,msg:
            error("%s[%r] = %r: %s\n%s" % (obj,i,value,msg,format_exc()))

configuration_server = Configuration_Server()




if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    from time import time # for performance testing
    import logging
    for h in logging.root.handlers[:]: logging.root.removeHandler(h)
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    self = configuration_server
    print("from configuration_driver import configuration")
    print("conf = configuration.configurations[0]")
    print("self.getattr(conf,'descriptions')")
    print("value = self.getattr(conf,'descriptions')")
    print("self.setattr(conf,'descriptions',value)")
    print("self.getitem(self.getattr(conf,'current_positions'),0)")
    print("self.getitem(self.getattr(conf,'positions'),0)")
    print("")
    print("configuration_server.update()")
    print("t=time(); configuration_server.update(); time()-t")
    print("configuration_server.run()")
    ##print("")
    ##from CAServer import casget
    ##print("casget(configuration_server.configuration_PV_name(conf,'descriptions'))")
