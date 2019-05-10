"""Friedrich Schotte, May 1, 2015 - May 1, 2015"""
from ftplib import FTP
from io import BytesIO
from struct import pack

data = ""
data += pack(">bbHIII",0x03,0x000,0x0001,0xF0FFB044,0x00000001,0x00000000)
data += pack(">bbHIII",0x03,0x000,0x0001,0xF0FFB044,0x00000001,0x00000001)
##file("/tmp/sequence.bin","w").write(data) # for debugging

f = BytesIO()
f.write(data)
f.seek(0)

ftp = FTP("pico25.niddk.nih.gov","root","root")
##ftp.storbinary ("STOR /tmp/sequence.bin",f) # for debugging
ftp.storbinary ("STOR /dev/sequencer",f)
ftp.close()
