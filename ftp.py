"""Transfer data across th enet work via FTP protocol.
Friedrich Schotte, May 1, 2015 - Jun 24, 2015
"""
__version__ = "1.0"
from logging import error,warn,debug

def ftp(data,destination):
    """Transfer data to a remote file system
    data: binary datqa as string
    destination: host+pathname,
    e.g. 'pico25.niddk.nih.gov/tmp/sequence.bin'"""
    # //id14b4/usr/local/xControl/cpl contains a module named "io" which
    # makes Python's build-in module "io" unusable.
    import sys
    if "/usr/local/xControl/cpl" in sys.path:
        sys.path.remove("/usr/local/xControl/cpl")

    from ftplib import FTP
    from io import BytesIO

    ip_address = destination.split("/")[0]
    directory = "/"+"/".join(destination.split("/")[1:-1])
    filename = destination.split("/")[-1]
    pathname = directory+"/"+filename
    buffer = BytesIO()
    buffer.write(data)
    buffer.seek(0)

    # For performance reasons, keep the connection open across repeated calls.
    # Also allow connections to multiple servers be open at the same time.
    if not ip_address in ftp_connections: ftp_connections[ip_address] = None
    connection = ftp_connections[ip_address]

    while True:
        if connection is None:
            try: connection = FTP(ip_address,"root","root")
            except Exception,msg:
                error("FTP %r: %s" % (ip_address,msg))
                connection = None
                break
        try:
           connection.storbinary ("STOR "+pathname,buffer)
           break
        except Exception,msg:
           warn("FTP %r,%r: %s" % (ip_address,pathname,msg))
           connection = None
           continue

    ftp_connections[ip_address] = connection

ftp_connections = {}

if __name__ == "__main__":
    data = "This is a test.\n"
    print 'ftp(data,"id14timing3.cars.aps.anl.gov/tmp/sequence-1.bin")'
