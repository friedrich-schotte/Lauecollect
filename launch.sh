#!/bin/bash
# version 1.1
# Determine the Python module to load from the script pathname.
dir=`dirname "$0"`
# Look at run-time argument to determine which Python script to run.
if [ "$1" == "" ] ; then echo "usage: `basename $0` script.py" 2>&1; exit; fi
prog="$1"
if [ -e "$dir/setup_env.sh" ] ; then source "$dir/setup_env.sh" ; fi
python "$dir/$prog"
