"""Instruct the ADXV image display application to display a live image during
data collection

Author: Friedrich Schotte
Date created: 2017-06-28
Date last modified: 2019-06-02
"""
__version__ = "1.0"

from logging import debug,info,warn,error

class ADXV_Live_Image(object):
    name = "ADXV_live_image"
    from persistent_property import persistent_property
    ip_address = persistent_property("ip_address","id14b4.cars.aps.anl.gov:8100")
    ip_address_choices = [
        "id14b4.cars.aps.anl.gov:8100",
        "pico5.cars.aps.anl.gov:8100",
    ]
    refresh_interval = persistent_property("refresh_interval",1.0)
    refresh_interval_choices = [0.25,0.5,1,2,5,10,30,60]
    last_refresh_time = 0.0

    from thread_property_2 import thread_property
    @thread_property
    def live_image(self):
        """Display a live image"""
        while not self.live_image_cancelled:
            self.update_live_image()
            self.live_image_wait_for_next_update()
        self.connected = False

    def live_image_wait_for_next_update(self):
        from time import sleep,time
        next_refresh_time = self.last_refresh_time + self.refresh_interval
        while time() < next_refresh_time and self.live_image:
            wait_time = min(max(next_refresh_time-time(),0),0.25)
            sleep(wait_time)
            next_refresh_time = self.last_refresh_time + self.refresh_interval

    live_image_filename = ""

    def update_live_image(self):
        """Display a live image"""
        filename = self.image_filename
        if filename and filename != self.live_image_filename:
            self.show_image(filename)

    def show_image(self,filename):
        """Tell ADSV to display an image"""
        if filename:
            from tcp_client import query,connected
            from time import time
            query(self.ip_address,"load_image %s" % filename,count=0)
            self.is_connected = connected(self.ip_address)
            if self.is_connected:
                self.live_image_filename = filename
                self.last_refresh_time = time()
        else:
            from tcp_client import disconnect
            disconnect(self.ip_address)
            self.is_connected = False
            self.live_image_filename = ""

    @property
    def image_filename(self):
        from instrumentation import rayonix_detector
        filename = rayonix_detector.current_temp_filename
        return filename

    is_connected = False

    def get_connected(self):
        return self.is_connected
    def set_connected(self,value):
        if bool(value) == False:
            from tcp_client import disconnect
            disconnect(self.ip_address)
            self.is_connected = False
        if bool(value) == True:
            from tcp_client import connect
            connect(self.ip_address)
            self.is_connected = True
    connected = property(get_connected,set_connected)

    online = connected

ADXV_live_image = ADXV_Live_Image()


def show_image(filename):
    from thread import start_new_thread
    start_new_thread(ADXV_live_image.show_image,(filename,))

if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    
    self = ADXV_live_image
    print('ADXV_live_image.ip_address = %r' % ADXV_live_image.ip_address)
    print('ADXV_live_image.refresh_interval = %r' % ADXV_live_image.refresh_interval)
    print('')
    print('ADXV_live_image.live_image = True')
    print('ADXV_live_image.update_live_image()')
    from instrumentation import rayonix_detector
    print('show_image(rayonix_detector.current_temp_filename)')
