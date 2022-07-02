"""
Date created: 2022-01-28
Date last modified: 2022-01-31
Authors: Philip Anfinrud, Friedrich Schotte
Revision comment: Formatting
"""
__version__ = "1.0.1"

import logging

from cached_function import cached_function


@cached_function()
def xray_beam_center(domain_name): return XRay_Beam_Center(domain_name)


class XRay_Beam_Center:
    from db_property import db_property
    from alias_property import alias_property
    from monitored_property import monitored_property

    def __init__(self, domain_name):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def db_name(self):
        return f"{self.domain_name}/{self.class_name}"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    nominal_beam_center_x = db_property("nominal_beam_center_x", 1986)
    nominal_beam_center_y = db_property("nominal_beam_center_y", 1973)
    nominal_image_width = db_property("nominal_image_width", 3840)
    nominal_image_height = db_property("nominal_image_height", 3840)
    ROI_size = db_property("ROI_size", 7)
    I_min = db_property("I_min", 800)

    @monitored_property
    def I(self, I_X_Y): return I_X_Y[0]

    @monitored_property
    def X(self, I_X_Y, I_min):
        from numpy import nan
        I, X, Y = I_X_Y
        if I < I_min:
            X = nan
        return X

    @monitored_property
    def Y(self, I_X_Y, I_min):
        from numpy import nan
        I, X, Y = I_X_Y
        if I < I_min:
            Y = nan
        return Y

    @monitored_property
    def I_X_Y(self, ROI):
        I, X, Y = M0_M1X_M1Y_from_roi(ROI)
        return I, X, Y

    @monitored_property
    def ROI(self,
            image_data,
            nominal_beam_center_x,
            nominal_beam_center_y,
            nominal_image_width,
            nominal_image_height,
            ROI_size,
            ):
        from numpy import rint, zeros, uint16

        width, height = image_data.shape
        X0 = int(rint(nominal_beam_center_x * width / nominal_image_width))
        Y0 = int(rint(nominal_beam_center_y * height / nominal_image_height))
        r = (ROI_size-1) // 2
        try:
            ROI = image_data[X0 - r:X0 + r + 1, Y0 - r:Y0 + r + 1]
        except NotImplementedError as x:
            logging.warning(f"{image_data}: {x}")
            ROI = zeros(shape=(ROI_size, ROI_size), dtype=uint16)
        if ROI.shape != (ROI_size, ROI_size):
            logging.warning(f"ROI shape expecting {(ROI_size, ROI_size)}, got {ROI.shape}")
            ROI = zeros(shape=(ROI_size, ROI_size), dtype=uint16)
        return ROI

    @monitored_property
    def image_data(self, image):
        image_data = image.data
        return image_data

    @monitored_property
    def image(self, image_filename):
        from rayonix_image import rayonix_image
        try:
            # logging.info(f"Loading image {image_filename}...")
            image = rayonix_image(image_filename)
        except OSError as x:
            logging.error(f"{image_filename}: {x}")
            image = self.default_image
        return image

    @monitored_property
    def default_image(self, nominal_image_width, nominal_image_height):
        from rayonix_image import rayonix_image
        image = rayonix_image(shape=(nominal_image_width, nominal_image_height))
        return image

    image_filename = alias_property("rayonix_detector.last_filename")

    @property
    def rayonix_detector(self):
        from rayonix_detector import rayonix_detector
        return rayonix_detector(self.domain_name)


def M0_M1X_M1Y_from_roi(roi):
    """Given roi, calculates M0, the background-subtracted integrated
    number of counts in pixels near the center, as well as (M1X,M1Y),
    center-of-mass coordinates relative to the center. """
    # Based on: /net/femto/C/SAXS-WAXS Analysis/SAXS_WAXS_Analysis.py, M0_M1X_M1Y_from_roi
    from numpy import array, indices
    # Define masks needed to determine M0, M1X, and M1Y
    spot = array([[0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 1, 1, 1, 0, 0],
                  [0, 1, 1, 1, 1, 1, 0],
                  [0, 1, 1, 1, 1, 1, 0],
                  [0, 1, 1, 1, 1, 1, 0],
                  [0, 0, 1, 1, 1, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0]])
    bkg = array([[0, 0, 1, 1, 1, 0, 0],
                 [0, 1, 0, 0, 0, 1, 0],
                 [1, 0, 0, 0, 0, 0, 1],
                 [1, 0, 0, 0, 0, 0, 1],
                 [1, 0, 0, 0, 0, 0, 1],
                 [0, 1, 0, 0, 0, 1, 0],
                 [0, 0, 1, 1, 1, 0, 0]])
    s = int((spot.shape[0] - 1) / 2)
    roi_bs = (roi - (roi * bkg).sum() / bkg.sum()) * spot
    M0 = roi_bs.sum()
    # Compute X1 and Y1 beam positions
    x_mask, y_mask = indices(spot.shape) - s
    M1X = (x_mask * roi_bs).sum() / M0
    M1Y = (y_mask * roi_bs).sum() / M0
    return M0, M1X, M1Y


if __name__ == "__main__":
    from reference import reference
    from handler import handler

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = xray_beam_center(domain_name)


    @handler
    def report(event): logging.info(f"{event}")


    print('self.I_X_Y')
    reference(self, "I_X_Y").monitors.add(report)
