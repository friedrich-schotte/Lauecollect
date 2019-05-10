#!/bin/bash -l
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../../../../.."; pwd`
exec python "$dir/SAXS_WAXS_Methods_Panel.py" >> ~/Library/Logs/Python.log 2>&1
