"""Display a live image during data collection
Friedrich SCohtte, Jun 28, 2017 - Jun 29, 2017
"""
__version__ = "1.0"

from ImageViewer import show_images
from ADXV_live_image import show_image

if __name__ == "__main__":
    from rayonix_detector_continuous import ccd
    print('show_image(ccd.temp_image_filename)')
