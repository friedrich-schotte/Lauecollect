"""
Author: Friedrich Schotte
Date created: 2022-06-12
Date last modified: 2022-06-20
Revision comment:
"""
__version__ = "1.0"

import logging

red = (255, 0, 0, 255)
green = (0, 255, 0, 255)
orange = (255, 192, 0, 255)

light_gray = (224, 224, 224, 255)
white = (255, 255, 255, 255)


def mix_colors(color1, color2):
    """E.g. color1, color2 = (128, 255, 128, 255), (200, 200, 255, 255)"""
    from numpy import asarray, concatenate, rint
    rgb1 = asarray(color1[0:3]) / 255
    rgb2 = asarray(color2[0:3]) / 255
    alpha1 = color1[3] / 255
    alpha2 = color2[3] / 255
    rgb1 = 1 - (1 - rgb1) * alpha1
    rgb2 = 1 - (1 - rgb2) * alpha2
    rgb = rgb1 * rgb2
    alpha = 1 - (1 - alpha1) * (1 - alpha2)
    rgba = concatenate((rgb, [alpha]))
    color = tuple(rint(rgba * 255).astype(int))
    # logging.debug(f"{color1}, {color2}: {color}")
    return color


def lightened_color(color, lightness):
    """lightness: 0: retain original, 1: make completely white"""
    from numpy import array, concatenate, rint
    r, g, b, a = color
    rgb = array((r, g, b)) / 255
    alpha = a / 255
    rgb = 1 - (1 - rgb) * (1 - lightness)
    rgba = concatenate((rgb, [alpha]))
    color = tuple(rint(rgba * 255).astype(int))
    return color


def make_transparent(color, transparency):
    """transparency: 0: retain original, 1: make completely invisible"""
    from numpy import rint, clip
    r, g, b, a = color
    a = a * (1 - transparency)
    a = clip(int(rint(a)), 0, 255)
    color = r, g, b, a
    return color


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
