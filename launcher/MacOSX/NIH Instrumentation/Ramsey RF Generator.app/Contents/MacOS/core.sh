#!/bin/bash -l
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../../../../.."; pwd`
exec python "$dir/Ramsey_RF_Generator_Panel.py" >> ~/Library/Logs/Python.log 2>&1
