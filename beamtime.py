"""
Author: Friedrich Schotte
Date created: 2021-09-07
Date last modified: 2021-10-22
Revision comment: Issue: Dataset directories without .conf file skipped
    e.g. 2021.10/WAXS/Pb-CaM/Pb-CaM-Buffer_Tramp_B-1
"""
__version__ = "1.0.1"


class Beamtime:
    def __init__(self, directory):
        self.directory = directory

    def __repr__(self):
        return f"{type(self).__name__}({self.directory!r})"

    @property
    def datasets(self):
        from find import find
        from os.path import dirname
        from corrected_dataset import Corrected_Dataset
        files = find(self.directory, name="*.log", exclude=["*/.AppleDouble/*", "*/backup/*", "*backup*"])
        directories = [dirname(file) for file in files]
        datasets = [Corrected_Dataset(directory) for directory in directories]
        return datasets


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # directory = "/net/femto-data2/C/Data/2021.07/WAXS"
    # directory = "/net/femto-data2/C/Data/2021.10/WAXS/Pb-CaM"
    directory = "/net/femto-data2/C/Data/2021.10/WAXS"
    self = Beamtime(directory)
    print("self.datasets")
