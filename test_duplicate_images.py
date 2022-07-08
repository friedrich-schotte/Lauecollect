from os import listdir
from os.path import basename

from rayonix_image_timestamp import rayonix_image_timestamp
from date_time import date_time

directory = "/net/femto-data2/C/Data/2021.07/WAXS/RNA-Poly-U12_Tramp_B-1/xray_images"
logfile = directory+"/RNA-Poly-U12_Tramp_B-1.log"

files = sorted(listdir(directory))
files = [file for file in files if not file.startswith(".")]
files = [file for file in files if file.endswith(".mccd")]
files = [directory+"/"+file for file in files]

# files = files[0:100]
# t_acq = array([rayonix_image_timestamp(file, 'acquire_timestamp') for file in files])
# t_image = array([rayonix_image_timestamp(file, 'header_timestamp') for file in files])
# dt = t_acq - t_image

for file in files:
   print(f"{date_time(rayonix_image_timestamp(file, 'acquire_timestamp'))}\t{date_time(rayonix_image_timestamp(file, 'header_timestamp'))}\t{basename(file)}")