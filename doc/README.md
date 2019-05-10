"""
"""DI-245 DATAQ Instruments Voltage and Thermocouple DAQ"""

Author: 
Valentyn Stadnytskyi v.stadnytskyi@gmail.com 

Date of last update: 
Sept 29, 2017

Communication Paramters: 

Commands:

Performance and Comments:

Source:
"DI-245 Communication protocol"
https://www.dataq.com/resources/pdfs/support_articles/DI-245-protocol.pdf


Setup:
Install pyserial module: pip install pyserial

USB-serial interface:

Windows driver details:
https://www.dataq.com/support/downloads/DATAQ%20Instruments%20Drivers%20Setup.exe

Description of files in the folder(project):
###DI-245-SERVER###
The DI-245-server.py consist of two threads: 
i) Thread_server takes care of communication
ii) Thread_measurements takes care of data acquisition from the DI-245 unit.

To start the server you need to pass 5 variable:
i) Port
ii) scan list: order in which you aquire data
iii) physical channels list
iv) the list of gains(see what gains are avaiable in the gain dictionary)
v) the length of the Ring Buffer in points. 1 point = 20 ms.
Example: run DI-245-server.py COM3 "0 1 2 3" "0 1 2 3" "T-thrmc 2.5 2.5 2.5" "1000000"

###DI245-CLASS###
full library of communication protocols.
Comments: for longer commands make sure to terminate them with the "carriage return" symbol.

###DI245-INTERFACE###
A simple interface that allows one time acquisition or debugging of some part of the code.

###DI-245-CLIENT###
this is a client that can send request to "Server", get response and process it. This is run on a different machine or different kernel of python. 

