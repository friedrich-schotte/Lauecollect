"""
Data base to save and recall motor positions
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2019-05-26
"""
__version__ = "1.0.1" # values, show_in_list

from logging import debug,info,warn,error

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
            casput(PV_name,getattr(configuration,prop))
            casmonitor(PV_name,callback=self.monitor)
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                PV_name = (self.prefix+"."+conf.name+"."+prop).upper()
                casput(PV_name,getattr(conf,prop))
                casmonitor(PV_name,callback=self.monitor)
                
            for motor_num in range(0,conf.n_motors):
                for prop in self.motor_properties:
                    PV_name = (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper()
                    casput(PV_name,getattr(conf,prop)[motor_num])
                    casmonitor(PV_name,callback=self.monitor)

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from configuration_driver import configuration
        from CAServer import casput
        for conf in configuration.configurations:
            for prop in self.configuration_properties:
                if PV_name == (self.prefix+"."+conf.name+"."+prop).upper():
                    setattr(conf,prop,value)
                    casput(PV_name,getattr(conf,prop))
            for motor_num in range(0,conf.n_motors):
                for prop in self.motor_properties:
                    if PV_name == (self.prefix+"."+conf.name+".MOTOR"+str(motor_num+1)+"."+prop).upper():
                        getattr(conf,prop)[motor_num] = value
                        casput(PV_name,getattr(conf,prop)[motor_num])
        

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
