#!/bin/bash -l
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../../../../.."; pwd`
exec python "$dir/Lightwave_Temperature_Controller_Panel.py" >> ~/Library/Logs/Python.log 2>&1
