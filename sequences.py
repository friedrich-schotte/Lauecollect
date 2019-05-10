"""
Find repeating patterns in sequences
Friedrich Schotte, Feb 6, 2016 - Feb 7, 2016

Reference:
Detecting a repeating cycle in a sequence of numbers
http://stackoverflow.com/questions/8672853/detecting-a-repeating-cycle-in-a-sequence-of-numbers-python
"""
__version__ = "1.0.2" # linear ranges
import re
from logging import debug,info,warn,error

# (.+ .+) will match at least two numbers (as many as possible) and place the
# result into capture group 1.
# ( \1)+ will match a space followed by the contents of capture group 1, at
# least once.
# (.+ .+) will originally match the entire string, but will give up
# characters off the end because ( \1)+ will fail, this backtracking will
# occur until (.+ .+) cannot match at the beginning of the string at which
# point the regex engine will move forward in the string and try again.
regex_parts = re.compile(r'(.+,.+)(,\1)+')
regex_parts = re.compile(r'(.+)([,+]\1)+')

def parts(string):
    match = regex_parts.search(string)
    if match:
        begin,end = match.start(),match.start()+len(match.group(0))
        part = match.group(1)
        count = len(match.group(0)+",")/len(match.group(1)+",")
        head,tail = string[0:begin],string[end:]
        debug("head %r, part %r, count %r, tail %r" % (head,part,count,tail))
        if head.endswith("["): head = head[:-1]
        if head.endswith(","): head = head[:-1]
        if len(head)>0 and head[-1] not in "+*[],": head = head+"]"
        if head == "[]": head = ""
        if head.endswith("]"): head = head+"+"
        if tail == "]": tail = ""
        if tail.startswith("]"): tail = tail[1:]
        if tail.startswith(","): tail = tail[1:]
        if len(tail)>0 and tail[0] not in "+*[],": tail = "["+tail
        if tail == "[]": tail = ""
        if tail.startswith("["): tail = "+"+tail
        debug("head %r, part %r, count %r, tail %r" % (head,part,count,tail))
        string = ""
        if head: string += head
        string += "["+part+"]*"+str(count)
        if tail: string += tail
    return string

regex_simplify1 = re.compile(r'([0-9]+)\*([0-9]+)')

def simplify1(string):
    """e.g. '2*2' -> '4'"""
    match = regex_simplify1.search(string)
    if match:
        n,m = match.groups()
        begin,end = match.start(),match.start()+len(match.group(0))
        string = string[0:begin]+str(int(n)*int(m))+string[end:]
    return string

regex_simplify2 = re.compile(r'\[([^\[\]]+)\]\*([0-9]+)\+\[\1\]')

def simplify2(string):
    """e.g. '[0]*4+[0]' -> '[0]*5'"""
    match = regex_simplify2.search(string)
    if match:
        part,n = match.groups()
        begin,end = match.start(),match.start()+len(match.group(0))
        string = string[0:begin]+"["+part+"]*"+str(int(n)+1)+string[end:]
    return string

regex_list = re.compile(r'(?<=\[)[0-9]+(,[0-9]+){2,}(?=\])')

def simplify3(string):
    """[1,2..4]+[6] -> [1,2..4,6]"""
    string = string.replace("]+[",",")
    return string

def mark_linear_range(string):
    """Replace stretches where the values chages linearly wirg "range(start,step,end)"""
    match = regex_list.search(string)
    if match:
        begin,end = match.start(),match.start()+len(match.group(0))
        list = match.group(0)
        string = string[0:begin]+mark_linear_ranges(list)+string[end:]
    return string

def mark_linear_ranges(string):
    """Replace stretches where the values chages linearly wirg "range(start,step,end)"""
    values = eval(string)
    ranges = linear_ranges(values)
    debug("%s" % str(ranges).replace(" ","")[1:-1])
    strings = []
    for r in ranges:
        if len(r) > 1:
            if len(strings) > 0 and not "]" in strings[-1] and not ")" in strings[-1]:
                strings[-1] += "]"
        if len(r) == 1:
            if len(strings) == 0 or "]" in strings[-1] or ")" in strings[-1]:
                strings += ["[%r" % r[0]]
            else: strings[-1] += ",%r" % r[0]
        elif r[0] == r[-1]: strings += ["[%r]*%d" % (r[0],len(r))]
        elif len(r) == 3: strings += "[%r,%r,%r]" % (r[0],r[1],r[2])
        else:
            start = r[0]; step = r[1]-r[0]; stop = r[-1]+1
            strings += ["range(%r,%r,%r)"%(start,stop,step)]
    if len(strings) > 0 and not "]" in strings[-1] and not ")" in strings[-1]:
        strings[-1] += "]"
    string = "+".join(strings)
    return string

def linear_ranges(values):
    """Break of list of values into lists where the value changes linearly"""
    ranges = []
    def close(x,y): return abs(y-x) < 1e-6
    for i in range(0,len(values)):
        is_linear_before = i >= 2 and \
            close(values[i]-values[i-1],values[i-1]-values[i-2])
        is_linear_after = 1 <= i <= len(values)-2 and \
            close(values[i]-values[i-1],values[i+1]-values[i])
        if is_linear_before or \
            (len(ranges) > 0 and len(ranges[-1]) == 1 and is_linear_after):
            ranges[-1] += [values[i]]
        else: ranges += [[values[i]]]
    return ranges

regex_range = re.compile(r'range\(([0-9+]),([0-9+]),([0-9+])\)')

def replace_range_with_ellipse(string):
    """e.g. 'range(1,5,1)' -> '[1,2..4]'"""
    match = regex_range.search(string)
    if match:
        start,stop,step = match.groups()
        start,stop,step = eval(start),eval(stop),eval(step)
        next = start+step
        last = stop-step
        begin,end = match.start(),match.start()+len(match.group(0))
        string = string[0:begin]+"[%r,%r..%r]"%(start,next,last)+string[end:]
    return string

regex_ellipse = re.compile(r'\[([0-9]),([0-9])\.\.([0-9])\]')

def replace_ellipse_with_range(string):
    """e.g. '[1,2..4]' -> 'range(1,5,1)'"""
    match = regex_ellipse.search(string)
    if match:
        start,next,last = match.groups()
        start,next,last = eval(start),eval(next),eval(last)
        step = next-start
        stop = last+step
        begin,end = match.start(),match.start()+len(match.group(0))
        string = string[0:begin]+"range(%r,%r,%r)"%(start,stop,step)+string[end:]
    return string

def expand(string):
    """e.g. [0]*3+[1] -> [0,0,0,1]"""
    string = str(flatten(eval(string))).replace(" ","")
    return string

def flatten(l):
    """Make a simple list out of list of lists"""
    flattened_list = iterate(flatten1,l)
    return flattened_list

def flatten1(l):
    """Make a simple list out of list of lists"""
    flattened_list = []
    for x  in l:
        if type(x) == list: flattened_list += x
        else: flattened_list += [x]
    return flattened_list

def iterate(function,value):
    """Apply a function of a value repeatedly, until the value does not
    change any more."""
    new_value = function(value)
    while new_value != value:
        value = new_value
        print("%s" % str(value).replace(" ",""))
        new_value = function(value)
    return value


if __name__ == "__main__":
    values = [0,0,0,0,0,1,2,3,4,6,1,2,3,4,6,1,2,3,4,6,4,5,4]
    string = str(values).replace(" ","")
    ##string = "0,0"
    ##match = regex_parts.search(string)
    ##if match: print("Found at pos %r: %r = repeat(%r)" % (match.start(),match.group(0),match.group(1)))
    print("%s" % string)
    ##string = iterate(mark_linear_ranges,string)
    string = iterate(parts,string)
    string = iterate(simplify1,string)
    string = iterate(simplify2,string)
    string = mark_linear_range(string)
    print("%s" % string)
    string = iterate(simplify3,string)
    string = iterate(replace_range_with_ellipse,string)
    string = iterate(replace_ellipse_with_range,string)
    string = expand(string)
    print("%s" % string)
