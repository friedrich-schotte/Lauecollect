#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-30
Date last modified: 2020-12-30
Revision comment:
"""
__version__ = "1.0"


def title(text):
    text = " ".join([capitalize(word) for word in text.split(" ")])
    text = capitalize_always(text)
    return text


def capitalize(word):
    if word not in exceptions:
        word = capitalize_always(word)
    return word


def capitalize_always(word):
    return word[0:1].upper() + word[1:]


exceptions = [
    "a", "an", "the",
    "for", "and", "nor", "but", "or", "yet", "so",
    "at", "around", "by", "after", "along", "for", "from", "of", "on", "to", "with", "without"
]

if __name__ == "__main__":
    print("it's OK in the US".title())
    print(title("it's OK in the US"))
