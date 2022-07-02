directory = "/net/femto-data/C/Data/2019.06/WAXS/RNA-Hairpin/RNA-Hairpin-4BP/RNA-Hairpin-4BP-CG-Closing-Loop/RNA-Hairpin-4BP-CG-Closing-Loop-Buffer-1/xray_images"
from os import listdir
files = listdir(directory)
files = [file for file in files if file.endswith(".mccd")]
files = [file for file in files if not file.startswith(".")]
files.sort()
files = [directory+"/"+file for file in files]
files = files[0:80]
from os.path import getmtime
from numpy import array
file_timestamps = array([getmtime(file) for file in files])
from rayonix_image_timestamp import rayonix_image_timestamp
header_timestamps = array([rayonix_image_timestamp(file) for file in files])
from numpy import diff
print("diff(file_timestamps)")
print("diff(header_timestamps)")
print("file_timestamps - header_timestamps")
