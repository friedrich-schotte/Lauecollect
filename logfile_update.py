"""
Add missing entries to a Lauecollect log file or remove supernumerary entries
Author: Friedrich Schotte
Date created: 2019-06-18
Date last modified: 2019-06-21
"""
__version__ = "1.2"

from logging import debug,warn,info,error
# FutureWarning: Conversion of the second argument of issubdtype from `str` to `str` is deprecated
import numpy;

import date_time

numpy.warnings.filterwarnings('ignore', r'Conversion of the second argument of issubdtype')

class Dataset(object):
    def __init__(self,logfile_name):
        self.logfile_name = logfile_name

    @property
    def directory(self):
        from os.path import dirname
        return dirname(self.logfile_name)

    @property
    def xray_image_basenames(self):
        from os import listdir
        filenames = listdir(self.directory+"/xray_images")
        from numpy import array,chararray
        filenames = array(filenames).view(chararray)
        is_image_file = filenames.find(".mccd") >= 0
        filenames = filenames[is_image_file]
        return filenames

    @property
    def xray_image_filenames(self):
        return self.directory+"/xray_images/"+self.xray_image_basenames

    @property
    def xray_image_timestamps(self):
        from os.path import getmtime
        from numpy import array
        return array([getmtime(f) for f in self.xray_image_filenames])

    @property
    def xray_image_filenames_sorted(self):
        from numpy import argsort
        order = argsort(self.xray_image_timestamps)
        return self.xray_image_filenames[order]

    @property
    def xray_image_basenames_sorted(self):
        from numpy import argsort
        order = argsort(self.xray_image_timestamps)
        return self.xray_image_basenames[order]

    @property
    def xray_image_timestamps_sorted(self):
        from numpy import sort
        return sort(self.xray_image_timestamps)

    def get_logfile(self): return self.logfile_original
    def set_logfile(self,logfile): self.logfile_updated = logfile
    logfile = property(get_logfile,set_logfile)

    def get_logfile_original(self):
        from os.path import exists
        logfile_name = self.logfile_original_name
        if not exists(self.logfile_original_name): logfile_name = self.logfile_name
        from table import table
        return table(logfile_name,separator="\t")
    def set_logfile_original(self,logfile):
        logfile.save(self.logfile_original_name)
    logfile_original = property(get_logfile_original,set_logfile_original)

    def get_logfile_updated(self):
        from table import table
        logfile = table(self.logfile_name,separator="\t")
        return logfile
    def set_logfile_updated(self,logfile):
        self.logfile_create_backup()
        if self.logfile_backed_up:
            info("Saving logfile...")
            logfile.save(self.logfile_name)
    logfile_updated = property(get_logfile_updated,set_logfile_updated)

    def logfile_create_backup(self):
        if not self.logfile_backed_up:
            from shutil import copy2
            copy2(self.logfile_name,self.logfile_original_name)

    @property
    def logfile_backed_up(self):
        from os.path import exists
        return exists(self.logfile_original_name)

    @property
    def logfile_original_name(self):
        return self.logfile_name+".original"

    def update_logfile(self):
        logfile = self.logfile
        logfile = self.update(logfile)
        self.logfile = logfile

    def update(self,logfile):
        logfile = self.remove_duplicates(logfile)
        logfile = self.remove_missing_images(logfile)
        logfile = self.add_missing_images(logfile)
        logfile = self.sort(logfile)
        return logfile

    def remove_duplicates(self,logfile):
        filenames = logfile.file
        keep = [filenames[i] not in filenames[i+1:] for i in range(0,len(filenames))]
        logfile = logfile[keep]
        return logfile

    def remove_missing_images(self,logfile):
        filenames = self.xray_image_basenames
        logged_filenames = logfile.file
        keep = [f in filenames for f in logged_filenames]
        logfile = logfile[keep]
        return logfile

    def add_missing_images(self,logfile):
        filenames = self.xray_image_basenames_sorted
        timestamps = self.xray_image_timestamps_sorted
        logged_filenames = logfile.file
        add = [f not in logged_filenames for f in filenames]
        j = len(logfile)
        logfile = logfile.copy()
        logfile.resize(len(logfile)+sum(add))
        from date_time import date_time
        from numpy import where
        image_numbers_to_add = where(add)[0]
        for i in image_numbers_to_add:
            logfile.file[j] = filenames[i]
            logfile.started[j] = date_time(timestamps[i-1]) if i-1 > 0 else ""
            logfile.finished[j] = date_time(timestamps[i])
            date_time.date_time[j] = logfile.finished[j]
            j += 1
        return logfile

    def sort(self,logfile):
        from time_string import timestamp
        time = [timestamp(t) for t in date_time.date_time]
        from numpy import argsort
        order = argsort(time)
        logfile = logfile[order]
        return logfile
        
    

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S%z",
    )
    logfile_name = "/net/femto-data/C/Data/2019.06/WAXS/Reference/Reference-2/Reference-2.log"
    ##logfile_name = "/net/femto-data/C/Data/2019.06/WAXS/RNA-Hairpin/RNA-Hairpin-4BP/RNA-Hairpin-4BP-CG-Closing-Loop/RNA-Hairpin-4BP-CG-Closing-Loop-ramp-1/RNA-Hairpin-4BP-CG-Closing-Loop-ramp-1.log"
    dataset = Dataset(logfile_name)
    self = dataset
    from instrumentations import BioCARS
    print("BioCARS.channel_archiver.directory = %r" % BioCARS.channel_archiver.directory)
    print("")
    print("len(dataset.xray_image_filenames)")
    print("len(dataset.logfile.file)")
    print("len(dataset.updated_logfile.file)")
    print("logfile = dataset.logfile")
    print("dataset.update_logfile()")
