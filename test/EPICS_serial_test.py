import CA ; CA.DEBUG = "silent"

from EPICS_serial_CA_test import Serial
port = Serial("14IDB:serial3") # loop back connector

fail_count = 0
for length in range(1,38):
    string = "x"*length+"\n"
    reply = port.query(string,terminator="\n")
    ##print "%r" % string
    ##print "%r" % reply
    if reply != string:
        print "Length %d: expected %d, got %d bytes" % \
            (length,len(string),len(reply))
        fail_count += 1
if fail_count > 0: print "%d failures" % fail_count
    
