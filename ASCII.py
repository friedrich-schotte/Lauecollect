"""
Convert unicode to ASCII string
Author: Friedrich Schotte
Date created: 2018-10-19
Date last modified: 2020-04-03
Revision comment: Fix: Python 3 compatibility
"""
__version__ = "1.0.2"

from logging import debug,info,warn,error

def ASCII(string):
    """Limit string to contain only 8-bit extended ASCII characters"""
    # https://stackoverflow.com/questions/816285/where-is-pythons-best-ascii-for-this-unicode-database
    # Maps left and right single and double quotation marks
    # into ASCII single and double quotation marks.
    punctuation = {0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22}
    if isinstance(string,type(u'')):
        ASCII_string = string.translate(punctuation)
        ASCII_string = ASCII_string.encode('ascii','ignore').decode('utf-8')
    else: ASCII_string = string
    ##if ASCII_string != string: debug("converted '%s' to %r" % (string,ASCII_string))
    return ASCII_string

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    text = u'\u201Chello, world!\u201D'
    ##text = u'{enable:111}\u2019'
    print('ASCII(%r)' % text)

