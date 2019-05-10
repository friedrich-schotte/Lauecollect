from instrumentation_id14 import ccd,pulses,waitt
from time import sleep,time

dir = "/data/pub/friedrich/test/test7"
Nrepeat = 10
Nalign = 200
Ndata = 30
timeout = 3.0

def test():
  for j in range(0,Nrepeat):
    # Alignnment scan
    print("%d Alignment" % (j+1))
    ccd.bin_factor = 8; waitt.value = 0.024
    filenames = [dir+"/alignment/test_%02d_%03d.mccd" % (j+1,i+1)
                 for i in range(0,Nalign)]
    ccd.acquire_images_triggered(filenames)
    pulses.value = Nalign
    while pulses.value > 0: sleep(0.05)
    sleep(waitt.value)
    t0 = time()
    while ccd.state() != "idle" and time()-t0 < timeout: sleep(0.05)
    if ccd.state() != "idle": print("CCD timeout: state %r" % (ccd.state()))
    # Data collection
    print("%d Data" % (j+1))
    ccd.bin_factor = 2; waitt.value = 0.110
    filenames = [dir+"/test_%02d_%03d.mccd" % (j+1,i+1)
                 for i in range(0,Ndata)]
    ccd.acquire_images_triggered(filenames)
    pulses.value = Ndata
    while pulses.value > 0: sleep(0.05)
    sleep(waitt.value)
    t0 = time()
    while ccd.state() != "idle" and time()-t0 < timeout: sleep(0.05)
    if ccd.state() != "idle": print("CCD timeout: state %r" % (ccd.state()))
    
if __name__ == "__main__": # for testing
  print('test()')
  
