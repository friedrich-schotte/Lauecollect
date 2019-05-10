#!/usr/bin/env python
"""Find number of spots and decide if the sample is frozen.

Authors: Hyun Sun Cho, Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-10-31
Date last modified: 2018-10-29

1.4 - uses freeze_intervention from freeze_intervention module
    - changed function current_image_file() because i was always getting empty string
        as current temp filename
"""
__version__ = "1.4" # uses freeze_intervention from freeze_intervention module
from logging import debug,info,warn,error

class Sample_Frozen(object):
    name = "sample_frozen"
    from persistent_property import persistent_property
    deice_enabled = persistent_property("deice_enabled",False)
    threshold_N_spts = persistent_property("threshold_N_spts",10)
    running_timestamp = persistent_property("running_timestamp",0)
    ROIX = persistent_property("ROIX",1000) #900
    ROIY = persistent_property("ROIY",1000) #900
    WIDTH = persistent_property("WIDTH",150) #300 #400
    CAS_prefix = persistent_property("CAS_prefix",'NIH:SAMPLE_FROZEN_XRAY') #300 #400
    intervention_enabled = False
    retract_deicing_enabled = False
    retracted_time = 20.0

    def get_running(self):
        from time import time
        return time() - self.running_timestamp <= 3.0
    def set_running(self,value):
        from thread import start_new_thread
        from CAServer import casput
        if value and not self.running:
            casput(self.CAS_prefix+'.RUNNING', value)
            self.deice_enabled = True
            start_new_thread(self.run,())
        else: self.deice_enabled = False
    running = property(get_running,set_running)

    def get_is_intervention_enabled(self):
        from time import time
        return self.intervention_enabled
    def set_is_intervention_enabled(self,value):
        from CAServer import casput
        self.intervention_enabled = value
        casput(self.CAS_prefix+'.ENABLED', self.intervention_enabled)
    is_intervention_enabled = property(get_is_intervention_enabled,set_is_intervention_enabled)

    def run(self):
        from time import time,sleep
        from CAServer import casget,casput
        from SAXS_WAXS_control import SAXS_WAXS_control
        from temperature_controller import temperature_controller
        casput(self.CAS_prefix+'.ENABLED', self.intervention_enabled)
        casput(self.CAS_prefix+'.RUNNING', self.deice_enabled)
        try:
            print('current temperature %r' % temperature_controller.value)
            info('current temperature %r' % temperature_controller.value)
        except:
            warn('could not get temperature')
        last_image_file = ""
        while self.deice_enabled:
            try:
                self.intervention_enabled = casget(self.CAS_prefix+'.ENABLED')
            except:
                error('Failed to get CA %r' % (self.CAS_prefix+'.ENABLED'))
                self.intervention_enabled = False
            self.running_timestamp = time()
            if self.current_image_file != last_image_file:
                last_image_file = self.current_image_file
                if self.sample_frozen(self.current_image_file) and not self.aux_deicing and self.intervention_enabled and (temperature_controller.value < -5.0) :
                    self.aux_deicing = True
                elif self.sample_frozen(self.current_image_file) and SAXS_WAXS_control.inserted and self.retract_deicing and (temperature_controller.value < -5.0):
                    SAXS_WAXS_control.retracted = True
                    sleep(self.retracted_time)
                    SAXS_WAXS_control.inserted = True
                else:
                    pass
            else: sleep(0.25)

    @property
    def sample_currently_frozen(self):
        """Does te current image show ice diffraction peaks?"""
        return self.sample_frozen(self.current_image_file)

    @property
    def diffraction_spots(self):
        """Does te current image show ice diffraction peaks?"""
        return self.diffraction_spots_of_image(self.current_image_file)

    def get_deicing(self):
        """Is the motion controller program instructed to run in 'deice' mode?"""
        from freeze_intervention import freeze_intervention
        return freeze_intervention.active
    def set_deicing(self,value):
        from freeze_intervention import freeze_intervention
        freeze_intervention.active = value
        #from Ensemble_client import ensemble
        #ensemble.integer_registers[3] = 3 if value else 0
        #info("ensemble.integer_registers[3] = %r" % ensemble.integer_registers[3])
    aux_deicing = property(get_deicing,set_deicing)

    def get_retract(self):
        """Is the motion controller program instructed to run in 'deice' mode?"""
        from SAXS_WAXS_control import SAXS_WAXS_control
        return SAXS_WAXS_control.retracted
    def set_retract(self,value):
        from SAXS_WAXS_control import SAXS_WAXS_control
        SAXS_WAXS_control.retracted = value
    retract = property(get_retract,set_retract)

    def get_retract_deicing(self):
        from time import time
        return self.retract_deicing_enabled
    def set_retract_deicing(self,value):
        from CAServer import casput
        self.retract_deicing_enabled = value
        casput(self.CAS_prefix+'.RETRACT_ENABLED', self.retract_deicing_enabled)
    retract_deicing = property(get_retract_deicing,set_retract_deicing)

    def sample_frozen(self,image_file):
        from CAServer import casput
        total_spots = self.diffraction_spots_of_image(image_file)
        try:
            casput(self.CAS_prefix+'.SPOTS',total_spots)
        except:
            pass
        flag = total_spots >= self.threshold_N_spts
        
        return flag

    def diffraction_spots_of_image(self,image_file):  
        from peak_integration import spot_mask 
        from numimage import numimage
        from scipy.ndimage.measurements import label
        from os.path import basename

        I = numimage(image_file)
        ROIX,ROIY,WIDTH = self.ROIX,self.ROIY,self.WIDTH
        I = I[ROIX:ROIX+WIDTH,ROIY:ROIY+WIDTH]  # part of image
        mask = spot_mask(I+20)
        ##total_spots = mask.sum()
        labelled_mask,total_spots = label(mask)
        if total_spots > 0: debug("%s: %s spots" % (basename(image_file),total_spots))
        return total_spots

    @property
    def current_image_file(self):
        from rayonix_detector_continuous import rayonix_detector
        return rayonix_detector.current_temp_filename #<--this function always gives empty string Oct 29 2018
        #return rayonix_detector.current_image_filename


sample_frozen = Sample_Frozen()


image_file1 = "/net/mx340hs/data/anfinrud_1711/Data/WAXS/GA/GA-2/xray_images/GA-2_2_75.6C_3_562ns.mccd" # ice
image_file2 = "/net/mx340hs/data/anfinrud_1711/Data/WAXS/GA/GA-2/xray_images/GA-2_2_75.6C_3_-10us.mccd" # no ice
image_file3 = "/net/mx340hs/data/anfinrud_1711/Data/WAXS/GA/GA-2/xray_images/GA-2_2_75.6C_2_-10us.mccd" # no ice
image_file4 = "/net/mx340hs/data/anfinrud_1711/Data/WAXS/GA/GA-2/xray_images/GA-2_2_75.6C_3_-10us-2.mccd" # ice

def test():
    # Load a test image.
    from time import time
    
    t0 = time()
    is_sample_frozen1 = sample_frozen.sample_frozen(image_file1)
    t1 = time()
    print("time %.3f s" %(t1-t0))
    is_sample_frozen2 = sample_frozen.sample_frozen(image_file2)
    t2 = time()
    print("time %.3f s" %(t2-t1))
    is_sample_frozen3 = sample_frozen.sample_frozen(image_file3)
    t3 = time()
    print("time %.3f s" %(t3-t2))
    is_sample_frozen4 = sample_frozen.sample_frozen(image_file4)
    print("time %.3f s" %(time()-t3))
    
    print("sample frozen file1: %r" % is_sample_frozen1)
    print("sample frozen file2: %r" % is_sample_frozen2)
    print("sample frozen file3: %r" % is_sample_frozen3)
    print("sample frozen file4: %r" % is_sample_frozen4)

def show_current_image():
    from rayonix_detector_continuous import rayonix_detector
    image_file = rayonix_detector.current_temp_filename
    if image_file: show_image(image_file)

def show_image(image_file):
    from time import time
    from pylab import figure,imshow,title,show,cm
    from numimage import numimage
    from peak_integration import spot_mask,peak_integration_mask
    from numpy import minimum
    from scipy.ndimage.measurements import label

    I0 = numimage(image_file)
    ROIX,ROIY,WIDTH = sample_frozen.ROIX,sample_frozen.ROIY,sample_frozen.WIDTH
    I = I0[ROIX:ROIX+WIDTH,ROIY:ROIY+WIDTH]

    # Time the 'peak_integration_mask' function.
    t0 = time()
    mask = spot_mask(I+20)
    info('spot_mask = %.3f [s]' %(time()-t0))

    ##N_spots = mask.sum()
    labelled_mask,N_spots = label(mask)

    # Display the image.
    chart = figure(figsize=(8,8))
    title("%s: %d spots" % (image_file,N_spots))
    imshow(minimum(I,1000).T,cmap=cm.jet,origin='upper',interpolation='nearest')
 
    if N_spots != 0: 
        # Spot integration
        t0 = time()
        SB_mask = peak_integration_mask(I)    
        t1 = time()
        print "Time to find Spots and generate S_mask (s):",t1-t0

        # Perform the spot integration.
        print "Integrated intensity: ",sum(I*SB_mask)
        
        # Display 'mask'
        chart = figure(figsize=(8,8))
        title('SB_mask')
        imshow(SB_mask.T,cmap=cm.jet,origin='upper',interpolation='nearest')

    show()    
    
if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    self = sample_frozen # for debugging
    print('sample_frozen.threshold_N_spts = %r' % sample_frozen.threshold_N_spts)    
    print('test()')    
    print('show_current_image()')
    print('sample_frozen.diffraction_spots')
    print('sample_frozen.sample_currently_frozen')
    print('sample_frozen.deice_enabled = %r' % sample_frozen.deice_enabled)
    print('sample_frozen.running = True')
    print('sample_frozen.deicing')
