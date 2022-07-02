"""
Author: Friedrich Schotte
Date created: 2021-09-07
Date last modified: 2021-02-11
Revision comment: new beamtime
"""
__version__ = "1.0.1"

import logging


def correct_beamtime_xray_image_filenames(beamtime_directory, dry_run=False):
    from beamtime import Beamtime
    for dataset in Beamtime(beamtime_directory).datasets:
        logging.info(f"Dataset {dataset.directory_name!r}")
        dataset.correct_xray_image_filenames(dry_run)


def check_beamtime_xray_image_timestamps(beamtime_directory):
    from beamtime import Beamtime
    from numpy import nanmin, nanmax, nan
    for dataset in Beamtime(beamtime_directory).datasets:
        dt = dataset.xray_image_timing_errors
        dt = nanmax(dt) - nanmin(dt) if len(dt) > 0 else nan
        logging.info(f"{dataset.directory_name}: {dt:.6f} s")


def check_beamtime_xray_image_order(beamtime_directory):
    from beamtime import Beamtime
    for dataset in Beamtime(beamtime_directory).datasets:
        ordered = dataset.xray_images_ordered
        logging.info(f"{dataset.directory_name}: {'Ordered' if ordered else 'Irregular'}")


def check_beamtime_duplicate_xray_images(beamtime_directory):
    from beamtime import Beamtime
    for dataset in Beamtime(beamtime_directory).datasets:
        duplicate_count = dataset.duplicate_xray_image_count
        logging.info(f"{dataset.directory_name}: {duplicate_count}")


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # beamtime_directory = "/net/femto-data2/C/Data/2021.06/WAXS"
    # beamtime_directory = "/net/femto-data2/C/Data/2021.07/WAXS"
    # beamtime_directory = "/net/femto-data2/C/Data/2021.10/WAXS"
    # beamtime_directory = "/net/femto-data2/C/Data/2022.02/WAXS"
    # beamtime_directory = "/net/femto-data2/C/Data/2022.03/WAXS/GB3/GB3_PumpProbe_PC0-1"
    beamtime_directory = "/net/mx340hs/data/hekstra_2206/Test/test_1a"

    print("from save_rename_files import rollback_directory")
    print("rollback_directory(beamtime_directory, dry_run=True)")
    print("")
    print("check_beamtime_xray_image_timestamps(beamtime_directory)")
    print("check_beamtime_xray_image_order(beamtime_directory)")
    print("check_beamtime_duplicate_xray_images(beamtime_directory)")
    print("")
    print("correct_beamtime_xray_image_filenames(beamtime_directory, dry_run=True)")
