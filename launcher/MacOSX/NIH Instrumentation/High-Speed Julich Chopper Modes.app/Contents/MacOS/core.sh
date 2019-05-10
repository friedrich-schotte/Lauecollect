#!/bin/bash -l
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../../../../.."; pwd`
exec python "$dir/Julich_Chopper_Modes_Panel.py" >> ~/Library/Logs/Python.log 2>&1
