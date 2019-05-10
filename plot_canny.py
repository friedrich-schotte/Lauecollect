"""
===================
Canny edge detector
===================

The Canny filter is a multi-stage edge detector. It uses a filter based on the
derivative of a Gaussian in order to compute the intensity of the gradients.The
Gaussian reduces the effect of noise present in the image. Then, potential
edges are thinned down to 1-pixel curves by removing non-maximum pixels of the
gradient magnitude. Finally, edge pixels are kept or removed using hysteresis
thresholding on the gradient magnitude.

The Canny has three adjustable parameters: the width of the Gaussian (the
noisier the image, the greater the width), and the low and high threshold for
the hysteresis thresholding.

Source: http://scikit-image.org/docs/dev/auto_examples/edges/plot_canny.html#sphx-glr-auto-examples-edges-plot-canny-py

modified: Valentyn Stadnytskyi Oct 26 2018
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

from skimage import feature
from PIL import Image
import os

def move_images():
    folder_MAC = "//volumes/data/anfinrud_1810/Data/Laue/"
    folder_analysis = "//volumes/data/anfinrud_1810/Data/Laue/opt_images/"
    list_of_files = os.listdir(folder_MAC)
    for i in range(len(list_of_files)):
        print('name: %r' % list_of_files[i])
        if 'M' in list_of_files[i]:
            print('moving: %r -> %r' %(folder_MAC + list_of_files[i], folder_analysis+'Microscope/'+ list_of_files[i]))
            os.rename(folder_MAC + list_of_files[i], folder_analysis+'Microscope/'+ list_of_files[i])
            print('Done moving')
        elif 'W' in list_of_files[i]:
            print('moving: %r -> %r' %(folder_MAC + list_of_files[i], folder_analysis+'WideField/'+ list_of_files[i]))
            os.rename(folder_MAC + list_of_files[i], folder_analysis+'WideField/'+ list_of_files[i])
            print('Done moving')
# Upload an image

template_APS_MAC_folder = "//volumes/data/anfinrud_1810/Data/Laue/opt_images/Microscope/"
list_of_files = os.listdir(template_APS_MAC_folder)
lst = []
for i in range(len(list_of_files)):
    #1540638546.21_882_'M'_0.21_0.05_0.8.tiff
    #1540639797.991
    #1540642535.745_12_'M'_0.21_0.05_0.8.tiff
    if '1540642535.745' in list_of_files[i]:lst.append(i) #jpg # Dortmund
i = lst[0]
print list_of_files[i]
filename = template_APS_MAC_folder+list_of_files[i]
bkg = np.array(Image.open(filename).convert('L')).astype('float64') # to grayscale

im_name = []
im = []
#background 1540642535.745_12_'M'_0.21_0.05_0.8.tiff
im_name.append("1540642536.731_13_'M'_0.21_0.05_0.8.tiff")
im_name.append("1540642537.71_14_'M'_0.21_0.05_0.8.tiff")
for i in im_name:
    #1540638547.086_883_'M'_0.21_0.05_0.8.tiff
    #'1540639799.802'
    #1540642536.731_13_'M'_0.21_0.05_0.8.tiff
    filename = template_APS_MAC_folder+i

    im.append(np.array(Image.open(filename).convert('L')).astype('float64')) # to grayscale

# Compute the Canny filter for two values of sigma
edges1 = feature.canny(im[0]-bkg)
edges2 = feature.canny(im[0]-bkg, sigma=3)

# display results
fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(8, 3),
                                    sharex=True, sharey=True)

ax1.imshow(im[0] - bkg, cmap=plt.cm.gray)
ax1.axis('off')
ax1.set_title('noisy image', fontsize=20)

ax2.imshow(edges1, cmap=plt.cm.gray)
ax2.axis('off')
ax2.set_title('Canny filter, $\sigma=1$', fontsize=20)

ax3.imshow(edges2, cmap=plt.cm.gray)
ax3.axis('off')
ax3.set_title('Canny filter, $\sigma=3$', fontsize=20)


fig.tight_layout()

plt.show()
