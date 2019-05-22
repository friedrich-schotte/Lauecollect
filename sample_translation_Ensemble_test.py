"""

Friedrich Schotte, 18 Mar 2013 - 28 Mar 2013
"""
# Command: 'SETPARM 145,"Enable Trigger."\n'
# Reply:   '%\n'
# Command: 'GETPARM(145)\n'
# Reply:   '%OK: Trigger is enabled.\n'

__version__ = "0.5"

def query(command):
    """To send a command that generates a reply."""
    max_retries = 2
    from EPICS_comm import CommPort
    port = CommPort("14IDB:SAMPLECOM")
    port.timeout = 0.2
    # Transmit the command.
    # Parameter 145 = UserString0
    request = 'SETPARM 145,"%s"\n' % command
    reply = port.query(request)
    if not reply.startswith("%"):
        # Controller did not reply.
        if len(reply) == 0: log_error("Request %r: no reply" % request)
        else: log_error("Request %r: Reply %r: Expecting '%%'" % (request,reply))
        return ""
    # Get the reply.
    request = "GETPARM(145)\n"
    reply = port.query(request)
    attempt = 1
    if not reply.startswith("%"):
        # Controller did not reply.
        if len(reply) == 0: log_error("Request %r: no reply" % request)
        else: log_error("Request %r: Reply %r: Expecting '%%'" % (request,reply))
        return ""
    while reply == "%%%s\n" % command:
        # Command not yet processed. Give it more time.
        if attempt > max_retries: break
        log("Command %r: Attempt %d, Reply %r: Command not yet processed" %
            (command,attempt,reply))
        reply = port.query (request)
        attempt += 1
        if not reply.startswith("%"):
            # Controller did not reply.
            if len(reply) == 0: log_error("Request %r: no reply" % request)
            else: log_error("Request %r: Reply %r: Expecting '%%'" % (request,reply))
            return ""
    if not (reply.startswith("%OK: ") or reply.startswith("%?")):
        # Command not processed. (SampleTranslation program not running?)
        if reply == "%%%s\n" % command:
            log_error("Command %r: Attempt %d, reply %r: Command not processed" %
                (command,attempt,reply))
        else: log_error("Request %r: Reply %r: expecting '%%OK: ...' or '%%?'" % (request,reply))
        return ""
    if not reply.startswith("%OK: "):
        # Command processed, but not understood.
        if reply.startswith("%?"):
            log_error("Command %r: Reply %r: Command not understood" % (command,reply))
        else:
            log_error("Command %r: Reply %r: Expecting '%%OK: ...'" % (command,reply))
        return "" 
    reply = reply[5:] # remove "%OK: "
    reply = reply.strip("\n")
    log("Command %r: Reply %r" % (command,reply))
    return reply

def log(message):
    from sys import stderr
    stderr.write("Info: %s\n" % message)

def log_error(message):
    from sys import stderr
    stderr.write("Error: %s\n" % message)


if __name__ == "__main__": # for testing
    print 'query("Enable Trigger.")'
    print 'query("Disable Trigger.")'
