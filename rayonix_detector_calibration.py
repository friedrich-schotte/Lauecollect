"""
Author: Friedrich Schotte
Date created: 2022-08-17
Date last modified: 2022-08-17
Revision comment:
"""
__version__ = "1.0"

from rayonix_image import rayonix_image
from subprocess import call

image_size = 3840
directory = "/net/mx340hs/data/pub/friedrich"
# Original location of calibration files: //mx340hs/opt/rayonix/calibration/
correction_table_filename = f"{directory}/calibration/ccdctb_mx340hs-0108.{image_size}"
post_flat_field_filename = f"{directory}/calibration/ccdpff_mx340hs-0108.{image_size}"
input_filename = f"{directory}/input_image.rx"
background_filename = f"{directory}/background_image.rx"
output_filename = f"{directory}/output_image.rx"

image = rayonix_image(shape=(image_size, image_size))
image.data[:] = 10000
image.save(input_filename)
image = rayonix_image(shape=(image_size, image_size))
image.save(background_filename)

# usage: correct_frames -c filename -p filename -b filename -o filename [options] filename [filename ...]
#          --output            -o string    Ouput base filename (number will be appended)
#          --CorrectionName    -C basename  Correction table base filename
#          --correction        -c filename  Correction table filename
#          --background        -b filename  Background filename
#          --defectmap         -d filename  Defect map filename
#          --postflat          -p filename  Post-flatfield filename
#          --flatfield         -f filename  Flatfield filename
#          --mask              -m filename  Mask filename
#          --do_flatfield      -F           Apply Flatfield to input frame
#          --do_mask           -M           Apply Mask to input frame
#          --input_bias        -A value     Subtract input_bias from frame before processing [0]
#          --output_bias       -B value     Add output_bias to frame after processing [0]
#          --reorient          -R code      reorient frame after processing [R0]
#          --do_mask           -M           Apply Mask to input frame
#          --create_mask       -T           Create mask frame from input frame
#          --ff_correction     -Z           Create flatfield only correction table
#          --gain              -g           Calculate relative gains from input frame
#          --fast_pixels       -x pixels    Number of pixels in fast direction of each sensor
#          --slow_pixels       -y pixels    Number of pixels in fast direction of each sensor
#          --fast_sensors      -X sensors   Number of sensors in fast direction of detector
#          --slow_sensors      -Y sensors   Number of sensors in slow direction of detector
#          --interlace         -i code      Code for deinterlacing frames [default = 0x1]
#          --cuda_device       -D device    Device number of CUDA processor to use
#          --cuda_dimension                 Modify structure  of cuda block
#          --processor         -P           Show CUDA processor details and exit
#          --threads           -t threads   Maximum number of threads in a CUDA block
#          --version           -V           Print version
#          --verbose           -v           Verbose (repeated options raises verbosity)

command = f"ssh hsuser@mx340hs correctFrames -c {correction_table_filename} -p {post_flat_field_filename} -b {background_filename} -o {output_filename} {input_filename}"
print(f"{command}")
call(command, shell=True)

