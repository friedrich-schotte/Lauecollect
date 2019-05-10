#!/bin/bash -l
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../.."; pwd`
exec python "$dir/temperature_controller_server.py" run_IOC

