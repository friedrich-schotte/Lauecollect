#!/bin/bash -l
# The -l (login) option makes sure that the environment is the same as for
# an interactive shell. 
localdir=`dirname "$0"`
dir=`cd "${localdir}/../../../../../.."; pwd`
exec python "$dir/EnsembleSAXS_PP_Panel.py" >> ~/Library/Logs/Python.log 2>&1
