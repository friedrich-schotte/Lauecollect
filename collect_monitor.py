#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-02-02
Date last modified: 2019-02-03
"""
from redirect import redirect
redirect("collect_monitor")
from CA import camonitor
camonitor("NIH:TIMING.registers.ch7_state.count")
camonitor("NIH:TIMING.registers.image_number.count")
camonitor("NIH:TIMING.registers.xdet_count.count")
camonitor("NIH:TIMING.registers.xdet_trig_count.count")
camonitor("NIH:TIMING.registers.xdet_acq_count.count")
camonitor("NIH:TIMING.registers.acquiring.count")
from time import sleep
while True: sleep(0.1)
