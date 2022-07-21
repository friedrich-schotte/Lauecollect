"""
Author: Friedrich Schotte
Date created: 2022-06-07
Date last modified: 2022-07-12
Revision comment: Comparison discriminates between Timestamps and scalar argument
"""
__version__ = "1.0.7"

import logging


class Timestamps:
    def __init__(self, values=None):
        self.values = []
        if values is not None:
            self.values = list(values)

    def __repr__(self):
        values = ", ".join([to_string(value) for value in self.values])
        return f"{type(self).__name__}([{values}])"

    @property
    def last(self):
        last_values = [getattr(value, "last", value) for value in self]
        if len(last_values) > 0:
            last = max(last_values)
        else:
            last = 0.0
        return last

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()

    def __getitem__(self, i):
        return self.values[i]

    def __eq__(self, other):
        if isinstance(other, Timestamps):
            if len(self) == len(other):
                result = all([t1 == t2 for (t1, t2) in zip(self, other)])
            else:
                result = self.last == other.last
        else:
            result = self.last == other
        return result

    def __ge__(self, other):
        if isinstance(other, Timestamps):
            if len(self) == len(other):
                result = all([t1 >= t2 for (t1, t2) in zip(self, other)])
            else:
                result = self.last >= other.last
        else:
            result = self.last >= other
        return result

    def __le__(self, other):
        if isinstance(other, Timestamps):
            if len(self) == len(other):
                result = all([t1 <= t2 for (t1, t2) in zip(self, other)])
            else:
                result = self.last <= other.last
        else:
            result = self.last <= other
        return result

    def __gt__(self, other):
        if isinstance(other, Timestamps):
            if len(self) == len(other):
                all_ge = all([t1 >= t2 for (t1, t2) in zip(self, other)])
                any_gt = any([t1 > t2 for (t1, t2) in zip(self, other)])
                result = all_ge and any_gt
            else:
                result = self.last > other.last
        else:
            result = self.last > other
        return result

    def __lt__(self, other):
        if isinstance(other, Timestamps):
            if len(self) == len(other):
                all_le = all([t1 <= t2 for (t1, t2) in zip(self, other)])
                any_lt = any([t1 < t2 for (t1, t2) in zip(self, other)])
                result = all_le and any_lt
            else:
                result = self.last < other.last
        else:
            result = self.last < other
        return result

    def check_for_issues(self):
        if self.issues:
            logging.warning(f"{self}: Issues: {self.issues}")

    @property
    def issues(self):
        issues = []
        for t in self:
            if isinstance(t, Timestamps):
                issue = t.issues
                if issue:
                    issues.append(issue)
            elif hasattr(t, "__iter__"):
                issue = f"{t!r}: Expecting float or Timestamps"
                issues.append(issue)
        issues = ", ".join(issues)
        return issues


def to_string(timestamps_or_time):
    from date_time import date_time
    if isinstance(timestamps_or_time, Timestamps):
        s = repr(timestamps_or_time)
    elif hasattr(timestamps_or_time, "__iter__"):
        s = "["+", ".join([to_string(t) for t in timestamps_or_time])+"]"
    else:
        s = date_time(timestamps_or_time)
    return s


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    t1 = Timestamps([0, Timestamps([0.2, 1])])
    t2 = Timestamps([0, Timestamps([0.5, 1])])
    t = Timestamps(range(0, 100, 1))
    print("t2 > t1")
    print("t1.last")
