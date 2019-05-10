"""
Rayonix CCD X-ray detector
Author: Friedrich Schotte
Date created: 2019-02-02
Date last modified: 2019-02-02
"""
__version__ = "0.0" 

from logging import debug,info,warn,error

from rayonix_detector import Rayonix_Detector
class Rayonix_Detector_Continous(Rayonix_Detector):
    """Rayonix MX series X-ray Detector"""
    from persistent_property import persistent_property
    scratch_directory = persistent_property("scratch_directory",
        "/net/mx340hs/data/tmp")
    nimages_to_keep = persistent_property("nimages_to_keep",10)
    filenames = persistent_property("filenames",[])
    image_numbers = persistent_property("image_numbers",[])

    def __init__(self):
        Rayonix_Detector.__init__(self)

    @property
    def image_filenames(self):
        """Pathnames of temporarily stored images, sorted by timestamp
        as list of strings"""
        from os import listdir
        from os.path import exists
        dir = self.scratch_directory
        try: files = sorted(listdir(dir))
        except: files = [] 
        files = [dir+"/"+f for f in files]
        return files


rayonix_detector = Rayonix_Detector_Continous()


if __name__ == "__main__": # for debugging
    from pdb import pm
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format=
            "%(asctime)s "
            "%(levelname)s "
            "%(funcName)s"
            ", line %(lineno)d"
            ": %(message)s"
    )

    self = rayonix_detector
    from os import listdir
    print('listdir(self.scratch_directory)')
    print('self.image_filenames')
