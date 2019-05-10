"""Display a live image during data collection
Friedrich Schotte, Jun 28, 2017 - Jun 29, 2017
"""
__version__ = "1.0"

def show_image(filename):
    """Tall ADSV to dsiplay an image"""
    from thread import start_new_thread
    start_new_thread(show_image_bgk,(filename,))

address = "id14b4.cars.aps.anl.gov:8100"

def show_image_bgk(filename):
    from tcp_client import query,disconnect
    if filename: query(address,"load_image %s" % filename,count=0)
    else: disconnect(address)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    
    from rayonix_detector_continuous import ccd
    print('show_image(ccd.temp_image_filename)')
