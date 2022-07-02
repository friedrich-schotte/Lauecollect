"""Instruct the ADXV image display application to display a live image during
data collection

Author: Friedrich Schotte
Date created: 2017-06-28
Date last modified: 2022-06-22
Revision comment: Added: show_data_collection_image
"""
__version__ = "1.2"

from cached_function import cached_function


@cached_function()
def ADXV_live_image(domain_name): return ADXV_Live_Image(domain_name)


class ADXV_Live_Image(object):
    from db_property import db_property
    from thread_property_2 import thread_property
    from alias_property import alias_property

    def __init__(self, domain_name="BioCARS"):
        self.domain_name = domain_name

    @property
    def db_name(self):
        return f"{self.domain_name}/ADXV_live_image"

    name = "ADXV_live_image"

    ip_address = db_property("ip_address", "localhost:8100")

    ip_address_choices = [
        "localhost:8100",
        "127.0.0.1:8100",
        "id14b4.cars.aps.anl.gov:8100",
        "pico5.cars.aps.anl.gov:8100",
    ]

    show_data_collection_image = db_property("show_data_collection_image", False, local=True)

    refresh_interval = db_property("refresh_interval", 1.0, local=True)

    refresh_interval_choices = [0.25, 0.5, 1, 2, 5, 10, 30, 60]

    last_refresh_time = 0.0

    @thread_property
    def live_image(self):
        """Display a live image"""
        from thread_property_2 import cancelled
        while not cancelled():
            self.update_live_image()
            self.live_image_wait_for_next_update()
        self.connected = False

    def live_image_wait_for_next_update(self):
        from time import sleep, time
        next_refresh_time = self.last_refresh_time + self.refresh_interval
        while time() < next_refresh_time and self.live_image:
            wait_time = min(max(next_refresh_time - time(), 0), 0.25)
            sleep(wait_time)
            next_refresh_time = self.last_refresh_time + self.refresh_interval

    live_image_filename = ""

    def update_live_image(self):
        """Display a live image"""
        from os.path import exists
        filename = ""
        if self.show_data_collection_image:
            if self.data_collection_image_filename:
                filename = self.data_collection_image_filename
        else:
            if self.image_filename:
                filename = self.image_filename
        if filename and exists(filename):
            if filename != self.live_image_filename:
                self.show_image(filename)

    def show_image(self, filename):
        """Tell ADXV to display an image"""
        if filename:
            from tcp_client import query, connected
            from time import time
            query(self.ip_address, "load_image %s" % filename, count=0)
            self.is_connected = connected(self.ip_address)
            if self.is_connected:
                self.live_image_filename = filename
                self.last_refresh_time = time()
        else:
            from tcp_client import disconnect
            disconnect(self.ip_address)
            self.is_connected = False
            self.live_image_filename = ""

    image_filename = alias_property("rayonix_detector.last_filename")
    data_collection_image_filename = alias_property("rayonix_detector.last_saved_image_filename")

    @property
    def rayonix_detector(self):
        from rayonix_detector import rayonix_detector
        return rayonix_detector(self.domain_name)

    is_connected = False

    def get_connected(self):
        return self.is_connected

    def set_connected(self, connected):
        if connected:
            from tcp_client import connect
            connect(self.ip_address)
            self.is_connected = False
        else:
            from tcp_client import disconnect
            disconnect(self.ip_address)
            self.is_connected = True

    connected = property(get_connected, set_connected)

    online = connected


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")

    domain_name = "BioCARS"
    self = ADXV_live_image(domain_name)

    print('self.ip_address = %r' % self.ip_address)
    print('self.refresh_interval = %r' % self.refresh_interval)
    print('')
    print('self.live_image = True')
    print('self.update_live_image()')
