"""Author: Friedrich Schotte
Date created: 2019-03-18
Date modified: 2019-03-18
"""
__version__ = "1.0"

def sorted_lists(lists):
    """Sort lists by order of first list"""
    from numpy import argsort
    order = argsort(lists[0])
    def reorder(list,order): return [list[i] for i in order]
    sorted_lists = [reorder(list,order) for list in lists]
    return sorted_lists

def sorted_description(description):
    description = ",".join(sorted(description.split(",")))
    return description

def diff(s1,s2):
    from difflib import context_diff,ndiff
    s1 = s1.splitlines(True)
    s2 = s2.splitlines(True)
    report = context_diff(s1,s2)
    report = [l for l in report if l[0] != " " and l[1] == " "]
    report = "".join(report).rstrip("\n")
    return report

from Ensemble_SAXS_pp_old import Ensemble_SAXS,Sequence
Ensemble_SAXS.cache_size = 0
description_old = sorted_description(Sequence().description)
registers_old,counts_old = sorted_lists(Sequence().register_counts)
from Ensemble_SAXS_pp import Ensemble_SAXS,Sequence
Ensemble_SAXS.cache_size = 0
description = sorted_description(Sequence().description)
registers,counts = sorted_lists(Sequence().register_counts)

diff_report = diff(description_old.replace(",","\n"),description.replace(",","\n"))
if diff_report: print(diff_report) 
print("Description matches: %s" % (description_old == description))
print("Registers match: %s" % (registers_old == registers))
print("Counts match: %s" % (counts_old == counts))
