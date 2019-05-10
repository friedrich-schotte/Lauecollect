"""
Remote control of LeCroy X-Stream series oscilloscopes using  Microsoft's
COM protocol (Common Object Model).

This script runs only on a Windows machine with LeCroy XStream Software
installed.

Example:
X.Measure.P1.GateStart = 0.95
sets the low limit of the gate of measurement P1 to 0.95 divisions.
print X.Measure.P1.last.Result.Value
reads the current value of measurement P1

Setup required:
On the oscilloscope PC, in the Windows Firewall, an exception must by defined
for Microsoft RPC, TCP port 135 and the Oscilloscope application
(C:/Program Files/lecroy/xstream/lecroyxstreamdso.exe).

python needs to run under the same user account on the local PC as the
oscilloscope application on the oscilloscope PC, e.g. 'Femtoland'.

Friedrich Schotte, NIH 28 Mar 2008
"""

import pythoncom,win32com.client #need to install pywin32
from time import time # for performance testing

# This works on oscilloscope PC itself.
X = win32com.client.Dispatch("LeCroy.XStreamDSO")

# Intended for remote control. XStream software needs to be installed
# on the local (client) machine, too. Otherwise it fails.
#X = win32com.client.DispatchEx("LeCroy.XStreamDSO",
#    machine="femto10") #,userName="Femtoland")

t = time()
num = X.Measure.P1.num.Result.Value
dt = time()-t
print "num(P1)=%g (time: %.3f s)" % (num,dt)
