#!/bin/bash -l
# Determine the location of the Python module to load from the script pathname.
dir=`dirname "$0"`
path=`cd "$dir/../../../../../.." ; pwd`
exec python "$path/TimingPanel.py" >> ~/Library/Logs/Python.log 2>&1
