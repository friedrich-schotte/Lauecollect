"""
Perhaps a more human-friendly natural sort
(Python's built-in sort is ASCII sort: z1, z10, 100,z11, z2, z 20, ...)
https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/

https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
Date created: 2020-01-31
Date last modified: 2022-04-04
Author: Friedrich Schotte
Revision comment: Python 3 compatibility
"""
__version__ = "1.0.2"


def naturally_sorted(alist):
    return sorted(alist, key=natural_keys_of_line)


def natural_order(alist):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by user "unutbu"
    return sorted(range(len(alist)), key=natural_key_of_index(alist))


def natural_key_of_index(alist):
    def f(i): return natural_keys_of_line(alist[i])

    return f


def natural_keys_of_line(line):
    """
    sorted(alist,key=natural_keys_of_line) sorts in human order
    https://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [natural_keys(word) for word in line]


def natural_keys(word):
    import re
    if type(word) == str:
        keys = [atoi(c) for c in re.split(r'(\d+)', word)]
    else:
        keys = word
    return keys


def atoi(text):
    return int(text) if text.isdigit() else text


def ordered(alist, order):
    columns = list(map(list, zip(*alist)))
    columns = [[column[j] for j in order] for column in columns]
    rows = list(map(list, zip(*columns)))
    return rows


if __name__ == "__main__":
    alist = [
        ["something1"],
        ["something12"],
        ["something17"],
        ["something2"],
        ["something25"],
        ["something29"],
    ]
    alist2 = [
        ["something1", 2],
        ["something1", 1],
        ["something12", 12],
        ["something17", 17],
        ["something2", 2],
        ["something25", 25],
        ["something29", 29],
    ]

    print("naturally_sorted(alist)")
    print("natural_order(alist)")
    print("ordered(alist,natural_order(alist))")
