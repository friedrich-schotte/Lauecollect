"""Save division without raising an exception using IEEE floating point
rules to signal division by zero.
Author: Friedrich Schotte
Date created: 2020-06-19
Date last modified: 2022-03-24
"""
__version__ = "1.0.1"


def floordiv(nominator, denominator):
    """Save division without raising an exception using IEEE floating point
    rules to signal division by zero
    """
    if denominator == 0:
        from numpy import nan, inf
        result = nan
        if nominator == 0:
            result = nan
        if nominator > 0:
            result = inf
        if nominator < 0:
            result = -inf
    else:
        result = int(nominator // denominator)
    return result


if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
                        )
    print("floordiv(3,2)")
    print("floordiv(0,0)")
    print("floordiv(1,0)")
    print("floordiv(-1,0)")
