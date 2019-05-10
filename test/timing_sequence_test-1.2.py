"""Friedrich Schotte, May 1, 2015 - May 7, 2015"""
from ftplib import FTP
from telnetlib import Telnet
from io import BytesIO
from struct import pack

data = ""
for i in range(0,10*1000/2):
    data += pack(">bbHIII",0x03,0x000,0x0001,0xF0FFB044,0x00000001,0x00000000)
    data += pack(">bbHIII",0x03,0x000,0x0001,0xF0FFB044,0x00000001,0x00000001)

f = BytesIO()
f.write(data)
f.seek(0)

ftp = FTP("pico25.niddk.nih.gov","root","root")
ftp.storbinary ("STOR /tmp/sequence.bin",f) 
ftp.close()

telnet = Telnet("pico25.niddk.nih.gov")
telnet.read_until("login: ")
telnet.write("root\n")
telnet.read_until("Password: ")
telnet.write("root\n")
telnet.read_until("# ")
telnet.write("/bin/cat < /tmp/sequence.bin > /dev/sequencer &\n")
telnet.read_until("# ")
telnet.write("exit\n")
transcript = telnet.read_all()
telnet.close()

def abort():
    telnet = Telnet("pico25.niddk.nih.gov")
    telnet.read_until("login: ")
    telnet.write("root\n")
    telnet.read_until("Password: ")
    telnet.write("root\n")
    telnet.read_until("# ")
    telnet.write("killall cat\n")
    telnet.read_until("# ")
    telnet.close()
