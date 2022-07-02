"""
Author: Friedrich Schotte
Date created: 2022-05-05
Date last modified: 2022-05-05
Revision comment:
"""
__version__ = "1.0"
 
import logging


def split_list(s):
    """Split a comma-separated list, without breaking up list elements
    enclosed in brackets or parentheses"""
    start = 0
    level = 0
    elements = []
    for i in range(0, len(s)):
        if s[i] in ["(", "[", '{']:
            level += 1
        if s[i] in [")", "]", '}']:
            level -= 1
        if s[i] == "," and level == 0:
            end = i
            element = s[start:end].strip()
            if element:
                elements += [element]
            start = i + 1
    end = len(s)
    element = s[start:end].strip()
    if element:
        elements += [element]
    return elements


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
