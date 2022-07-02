"""
Author: Friedrich Schotte
Date created: 2022-06-09
Date last modified: 2022-06-09
Revision comment:
"""
__version__ = "1.0"
 
import logging


def capitalize(string):
    """'BioCARS test' -> 'BioCARS Test'"""
    words = string.split(" ")
    words = [capitalize_word(word) for word in words]
    return " ".join(words)


def capitalize_word(word):
    return word[0:1].upper() + word[1:]


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
