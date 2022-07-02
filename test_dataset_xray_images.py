from dataset import Dataset
from numpy import diff, asarray

dataset_directory = "/net/femto-data2/C/Data/2021.10/WAXS/Ca-CaM/Ca-CaM-Buffer_PumpProbe_B-1"
self = Dataset(dataset_directory)
xray_images = self.logfile_xray_images[0:100]
timestamps = [image.acquire_timestamp for image in xray_images]
xray_images_dt = diff(timestamps)
end_times = asarray(self.end_times).reshape((-1, 44))
dt = diff(end_times)
