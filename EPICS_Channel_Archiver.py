#!/bin/env python
"""EPICS Channel Archiver
Process variable history

Test:
curl "Content-Type: text/xml" -X POST -d @request.data http://everest.cars.aps.anl.gov/archive/cgi/ArchiveDataServer.cgi

Source: 
https://github.com/EPICSTools/ChannelArchiver/tree/master/XMLRPCServer

Friedrich Schotte, Nov 23, 2015 - Nov 23, 2015
"""
__version__ = "1.0"

# based on file "XMLRPCServer/request.data"
request_template = """\
<?xml version="1.0"?>
<methodCall>
<methodName>archiver.values</methodName>
<params>
<!-- key -->
<param><value><i4>{0[key]:d}</i4></value></param>
<!-- channel name array -->
<param>
  <value>
    <array>
      <data>
        <value><string>{0[PV_name]}</string></value>
      </data>
    </array>
  </value>
</param>
<!-- start time -->
<param><value><i4>{0[start_time]:.0f}</i4></value></param>
<param><value><i4>0</i4></value></param>
<!-- start time -->
<param><value><i4>{0[end_time]:.0f}</i4></value></param>
<param><value><i4>0</i4></value></param>
<!-- count -->
<param><value><i4>{0[count]:d}</i4></value></param>
<!-- how -->
<param><value><i4>{0[how]:d}</i4></value></param>
</params>
</methodCall>\
"""

URL = "http://everest.cars.aps.anl.gov/archive/cgi/ArchiveDataServer.cgi"

def PV_history(PV_name,start_time=0,end_time=None,count=1000000,key=2,how=3,
    URL=URL):
    """Process variable history
    start_time: number of seconds since Jan 1, 1970, 00:00:00 UST
    end_time: number of seconds since Jan 1, 1970, 00:00:00 UST
    count: maximum number of values to return
    key: which archive? 1 = full archive, 2 = current archive
    URL: e.g. "http://everest.cars.aps.anl.gov/archive/cgi/ArchiveDataServer.cgi"
    Return value: list of timettamps, list of floating point values
    """
    from time import time
    if end_time is None: end_time = time()+3600
    # Negative time are interperted as relative to now.
    if start_time < 0: start_time += time()
    if end_time < 0: end_time += time()
    
    params = dict(PV_name=PV_name,start_time=start_time,end_time=end_time,
        count=count,key=key,how=how)
    request = request_template.format(params)

    from httplib import HTTPConnection
    from urlparse import urlparse
    u = urlparse(URL)
    headers = {"Content-type": "text/xml"}
    conn = HTTPConnection(u.netloc)
    conn.request("POST",u.path,request,headers)
    response = conn.getresponse()
    data = response.read()
    data = data.replace("\r\n","\n") # DOS to UNIX

    # Parse XML data, extract item "value"
    from xml.etree import ElementTree
    from StringIO import StringIO
    tree = ElementTree.parse(StringIO(data))
    values = []; timestamps = []
    name = ""; severity = "0"
    for node in tree.iter():
        if node.tag == "name": name = node.text
        if node.tag == "i4" and name == "sevr": severity = node.text
        if severity == "0":
            if node.tag == "i4" and name == "secs": timestamps += [node.text]
            if node.tag == "i4" and name == "nano":
                timestamps[-1] += "."+node.text
            if node.tag == "double" and name == "value": values += [node.text]
    values = [float(v) for v in values]
    timestamps = [float(t) for t in timestamps]
    return timestamps,values 
    
def date_time(seconds):
    """Current date and time as formatted ASCII text, precise to 1 ms
    seconds: time elapsed since 1 Jan 1970 00:00:00 UST"""
    from datetime import datetime
    timestamp = str(datetime.fromtimestamp(seconds))
    return timestamp


if __name__ == "__main__":
    from time import time
    day = 86400
    print('timestamps,values = PV_history("14IDA:DAC1_4.VAL",start_time=-7*day,key=2)')
    print('for t,v in zip(timestamps,values): print date_time(t),v')
