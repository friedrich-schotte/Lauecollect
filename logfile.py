#!/bin/env python
"""Log file
Author: Friedrich Schotte, Mar 2, 2016 - Oct 7, 2017
"""
__version__ = "1.1.5" # caching
from logging import debug,warn,info,error

class LogFile(object):
    name = "logfile"
    from persistent_property import persistent_property
    filename = persistent_property("filename","")

    def __init__(self,name="logfile",columns=["date time","value"],filename=None):
        """filename: where to save
        columns: list of strings"""
        self.name = name
        self.columns = columns
        if filename is not None: self.filename = filename
        from thread import allocate_lock
        self.lock = allocate_lock()

    def log(self,*args,**kwargs):
        """Append to logfile
        time: time in seconds since 1970-01-01 00:00:00 UTC
        """
        from time import time
        from time_string import date_time
        from normpath import normpath
        from os.path import exists,dirname; from os import makedirs

        values = args
        if "time" in kwargs: timestamp = kwargs["time"]
        else: timestamp = time()

        with self.lock: # Allow only one thread at a time inside this function.
            filename = normpath(self.filename)
            if not exists(dirname(filename)): makedirs(dirname(filename))
            if not exists(filename): header = "#"+"\t".join(self.columns)+"\n"
            else: header = ""
            fields = [date_time(timestamp)]+[str(v) for v in values]
            line = "\t".join(fields)+"\n"
            file(filename,"ab").write(header+line)

    def history(self,*args,**kwargs):
        """time_range: tmin,tmax: time in seconds since 1970-01-01 00:00:00 UTC
        range: imin,imax: all vaues from imin to imax, including imax
        (Negative integers count from the end, -1 = last.)
        count: last N
        *args: column names"""
        from numpy import nan
        if "count" in kwargs:
            count = kwargs["count"]
            lines = self.lines(self.last_lines_range(count))
        if "time_range" in kwargs:
            time_range = kwargs["time_range"]
            lines = self.lines(self.timestamp_range(time_range))
        column_names = args
        column_indices = [self.columns.index(name) for name in column_names]
        values = []
        for i in range(0,len(lines)):
            if len(lines[i]) == len(column_names):
                try:
                    row_values = [convert(lines[i][j],name) for (j,name)
                        in zip(column_indices,column_names)]
                    values += [row_values]
                except Exception, msg:
                    warn("logfile: line %d/%d %r: %s" % (i+1,len(lines),lines[i],msg))
        values = zip(*values) # organize data in rows
        if values == []: values = [[]]*len(column_names)
        return values

    def lines(self,(start,end)):
        """Part of the file.
        start: byte offset (self.contents[start] is the first character included)
        end: byte offset (self.contents[end] will not be included)
        Return value: list of lists of strings, each list representing a line
        """
        lines = self.content[start:end].split("\n")
        # Get rid of empty lines.
        if lines[:1] == ['']: lines = lines[1:]
        if lines[-1:] == ['']: lines = lines[:-1]
        # Get rid of comment lines.
        while len(lines)>0 and lines[0].startswith("#"): lines = lines[1:]
        lines = [l.split("\t") for l in lines]
        return lines

    def last_lines_range(self,count):
        """Where are the last n lines from the end of the file?
        Return value: tuple of byte offsets: begin,end
        """
        content = self.content
        j = len(content)
        if content[j-1:j] == "\n": j -= 1
        i = j
        for n in range(0,count):
            i2 = content.rfind("\n",0,i)
            if i2<0: break
            i = i2
        i += 1
        return i,j

    def timestamp_range(self,(t1,t2)):
        """Start and end byte offsets of a time range
        t1: seconds since 1970-01-01T00:00:00+00
        t2: seconds since 1970-01-01T00:00:00+00
        """
        return [self.timestamp_location(t) for t in (t1,t2)]

    def timestamp_location(self,timestamp):
        """First line with a time stamp later to the given time stamp.
        Return value: byte offset from the beginning of the file.
        Length of file if all timestamp in the file are earlier
        timestamp: seconds since 1970-01-01T00:00:00+00"""
        from numpy import isnan,clip
        text = self.content
        offset = len(text)/2
        step = len(text)/4
        while step > 0:
            ##debug("offset %r, step %r" % (offset,step))
            t = self.next_timestamp(text,offset)
            if isnan(t): offset = len(text); break
            if t <= timestamp: offset += step
            else: offset -= step
            offset = clip(offset,0,len(text))
            step = (step+1)/2 if step > 1 else 0
        return offset

    @staticmethod
    def next_timestamp(text,offset):
        from time_string import timestamp
        from numpy import nan
        i = text.find("\n",offset)+1
        if i < 0: t = nan
        else:
            j = text.find("\t",i)
            if j < 0: t = nan
            else: t = timestamp(text[i:j])
        return t
        
    @property
    def content(self):
        from normpath import normpath
        filename = normpath(self.filename)
        from mmap import mmap,ACCESS_READ
        try:
            f = file(filename)
            content = mmap(f.fileno(),0,access=ACCESS_READ)
        except IOError: content = ""
        return content

    @property
    def content(self):
        from os.path import exists,getsize
        from normpath import normpath
        filename = normpath(self.filename)
        if exists(filename):
            size_change = getsize(filename) - len(self.cached_content) 
            if size_change > 0:
                ##debug("Logfile: Reading %d bytes" % size_change)
                f = file(filename)
                f.seek(len(self.cached_content))
                self.cached_content += f.read()
            elif size_change < 0:
                ##debug("Logfile: Reading %d bytes" % getsize(filename))
                self.cached_content = file(filename).read()
        else: self.cached_content = "" 
        return self.cached_content

    def get_cached_content(self):
        if self.filename in self.file_cache:
            content = self.file_cache[self.filename]
        else: content = ""
        return content
    def set_cached_content(self,content):
        self.file_cache[self.filename] = content
    cached_content = property(get_cached_content,set_cached_content)

    file_cache = {}

    @property
    def start_time(self):
        from time_string import timestamp
        from time import time
        lines = self.lines((0,80))
        try: t = timestamp(lines[0][0])
        except: t = time()
        return t

    def __len__(self): return self.content[:].count("\n")-1

logfile = LogFile


def convert(x,name):
    """Try to convert string to a Python object.
    if not possible return a string
    name: if "date time", force conversion from string to seconds"""
    if name == "date time": return timestamp(x)
    try: return float(x)
    except: pass
    try: return timestamp(x)
    except: pass
    return x

def timestamp(date_time):
    """Convert a date string to number of seconds since 1 Jan 1970 00:00 UTC
    date_time: e.g. "2017-10-04 20:17:34.286479-0500"
    or "2017-10-04 20:17:34-0500"
    """
    from datetime import datetime
    if date_time[-5] in "+-": date_time,TZ = date_time[:-5],date_time[-5:] 
    else: TZ = "+0000"
    if "." in date_time: format = "%Y-%m-%d %H:%M:%S.%f"
    else: format = "%Y-%m-%d %H:%M:%S"
    utc_dt = datetime.strptime(date_time,format)
    timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds()
    TZ_offset = int(TZ[0:3])*3600
    timestamp -= TZ_offset
    return timestamp

##from time_string import timestamp

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging; logging.basicConfig(level=logging.DEBUG)
    from channel_archiver import channel_archiver
    from time import time
    self = channel_archiver.logfile("NIH:TEMP.RBV")
    print('t=time(); x=self.history("date time","value",time_range=(time()-10*60,time())); time()-t')
    print('len(self.content)')
    print('t=time(); x=self.content; time()-t')
