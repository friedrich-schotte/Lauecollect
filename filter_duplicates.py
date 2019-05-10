"""
Based on:
https://stackoverflow.com/questions/44691558/suppress-multiple-messages-with-same-content-in-python-logging-module-aka-log-co

Author: Friedrich Schotte
Date created: 2018-11-20
"""
__version__ = "1.0"

import logging

class DuplicateFilter(logging.Filter):

    def filter(self, record):
        # add other fields if you need more granular comparison, depends on your app
        current_log = (record.module, record.levelno, record.msg)
        if current_log != getattr(self, "last_log", None):
            self.last_log = current_log
            return True
        return False

def filter_duplicates():
    import logging
    logger = logging.getLogger()  # get the root logger
    logger.addFilter(DuplicateFilter())  # add the filter to it
    

if __name__ == "__main__":
    import logging

    logging.warn("my test")
    logging.warn("my repeated test")
    logging.warn("my repeated test")
    logging.warn("my repeated test")
    logging.warn("my other test")

    logger = logging.getLogger()  # get the root logger
    logger.addFilter(DuplicateFilter())  # add the filter to it

    logging.warn("my test")
    logging.warn("my repeated test")
    logging.warn("my repeated test")
    logging.warn("my repeated test")
    logging.warn("my other test")
