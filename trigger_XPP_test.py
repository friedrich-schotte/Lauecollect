from xppbeamline import xppevent

events = [
    {"code": 95,"comment":"DAQ evt"      , "t":range(0,12)},
    {"code": 98,"comment":"FPGA start"   , "t":[0]},
    {"code": 97,"comment":"Rayonix event", "t":[1]},
]

Nt = 12

def setSequence():
    i = 0
    for t in range(0,Nt):
        deltaBeam = 1
        for event in events:
            if t in event["t"]:
                xppevent.setstep(i,event["code"],deltaBeam,comment=event["comment"])
                deltaBeam = 0
                i += 1
    xppevent.setnsteps(i)
    while i<20:
        xppevent.setstep(i,0,0,comment=" ")
        i += 1
    xppevent.update()
    xppevent.start()                

def setSequenceLJ12(nPause=0):
    xppevent.setstep(0, 95, 1, comment='DAQ evt')
    xppevent.setstep(1, 98, 0, comment='FPGA start')
    for i in range(1,12+nPause):
      xppevent.setstep(i+1, 95, 1, comment='DAQ evt')
    xppevent.setstep(13+nPause, 97, 0, comment='Rayonix event')
    xppevent.setnsteps(14+nPause)

    xppevent.update()
    xppevent.start()

if __name__ == "__main__":
    print "setSequenceLJ12()"
    print "setSequence()"
