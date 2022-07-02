#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-11-15
Date last modified: 2020-11-15
Revision comment:
"""
__version__ = "1.0"

from auto_backup import *


def rollback(date, confirm=True, preview=False):
    try:
        if not preview:
            rollback(date, preview=True)
        for file in files():
            for rollback_file in rollback_files(file, date):
                if copied(rollback_file, file, confirm, preview):
                    break
    except KeyboardInterrupt:
        pass


def rollback_files(file, date):
    files = []
    if file_modified_at_date(file, date):
        backup_file = last_backup_filename(file)
        if backup_file:
            files += [backup_file]
    return files


def file_modified_at_date(file, date):
    return abs(getmtime(file) - date) < 1.0


if __name__ == "__main__":
    # from pdb import pm
    import logging
    from time_string import timestamp

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    date = timestamp("2022-06-16 13:10:37.945430750 -0400")
    confirm = True
    preview = False
    file = "../Lauecollect/Panel_3.py"

    rollback(date)
