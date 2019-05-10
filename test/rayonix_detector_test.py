if __name__ == "__main__": # for testing
  from instrumentation import *
  from numpy import *
  from ImageViewer import show_images
  from os.path import exists
  delays = ["100ps","316ps","1ns"]
  filenames = list(array([["/net/mx340hs/data/anfinrud_1403/Test/Sequence-Test/Test2/Test_%s_001.mccd" % d
        for d in ["off%d"%(1+i),delays[i]]] for i in range(0,len(delays))]).flatten())
  print 'ccd.acquire_images_triggered(filenames)'
  print 'ccd.acquire_images(filenames,integration_time=0.8,interval_time=1.0)'
  print 'xray_detector_trigger.trigger_once()'
  print 'xray_detector_trigger.generate_sequence(1,len(filenames))'
  print 'show_images(filenames)'
