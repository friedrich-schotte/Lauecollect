"""Download a file via HTTP protocol or retreive the output of a CGI script.
Friedrich Schotte, Oct 23, 2015 - Oct 23, 2015
"""
__version__ = "1.0"

def wget(URL):
    """Upload a file across the network using HTTP protocol
    data: content of the file to upload.
    URL: e.g. "http://id14timing3.cars.aps.anl.gov/tmp/test.txt"
    """
    URL = URL.replace("http://","")
    ip_address = URL.split("/")[0]
    script = "/"+"/".join(URL.split("/")[1:])
    if not ip_address in connections:
        from httplib import HTTPConnection
        connection = HTTPConnection(ip_address)
        connections[ip_address] = connection
    connection = connections[ip_address]
    connection.request("GET",script)
    request = connection.getresponse()
    data = request.read()
    return data

connections = {}

if __name__ == "__main__": # for testing
    from time import time
    print('print(wget("http://pico23.niddk.nih.gov/test.cgi"))')
    print 't=time();x=wget("http://pico23.niddk.nih.gov/test.cgi");time()-t'
