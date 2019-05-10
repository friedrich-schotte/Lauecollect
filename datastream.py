#!/bin/env python
"""Extract images and detector readings from an LCLS datastream
Setup: source /reg/g/psdm/etc/ana_env.sh

Chris O'Grady, Jan 22, 2016
Friedrich Schotte, Jan 25, 2016 - Mar 2, 2016
"""
from logging import warn,info,debug,error
from time import time
from numpy import nan,inf,isnan

__version__ = "1.0.2" # date_time

class DataStream:
    exp_run = None
    event_number = -1
    serial_number = -1
    detector_name = ""
    event = None

    def image(self,exp_run_event):
        """exp_run_event: contains experiment number, run number and event number
        'exp=xppj1216:run=17:event=0' or 'exp=xppj1216:run=17:event=rayonix,0'
        """
        return self.detector(exp_run_event,"rayonix:data16")
            
    def detectors(self,exp_run):
        """What are the names of the detectors in the datastream?
        exp_run: contains experiment number, run number, e.g. 'exp=xppj1216:run=17'
        """
        from psana import DataSource
        ds = DataSource(exp_run)
        es = ds.env().epicsStore()
        names = []
        for evt in ds.events():
            keys = evt.keys()
            for d in keys:
                # E.g. d.src(): DetInfo(NoDetector.0:Evr.0), d.alias(): 'evr0'
                name = str(d.src()).split("(")[-1].split(")")[0]
                if name and not name in names: names += [name]
                name = d.alias()
                if name and not name in names: names += [name]
                for name in es.pvNames():
                    if not name in names: names += [name]
                for name in es.aliases():
                    if not name in names: names += [name]
        return names

    def detector(self,exp_run_event,detector_name):
        """exp_run_event: contain experiment number, run number and event number
        'exp=xppj1216:run=17:event=0' or 'exp=xppj1216:run=17:event=rayonix,0'
        detector_name: detector name e.g. "XppEnds_Ipm0:sum" or "rayonix:data16"
        suffix "sum": get the sum of all four channels of a 4-quadrant detector
        suffix "channel": get all four channels of a 4-quadrant detector
        suffix "channel:0": the first channel of a 4-quadrant detector
        suffix "data16": get an image with 16 bit depth
        suffix "data16:0,0": get pixle (0,0) of an image
        """
        full_detector_name = detector_name
        attr = ""
        item = None
        if detector_name.count(":") == 1:
            detector_name,attr = detector_name.split(":")
        if detector_name.count(":") == 2:
            detector_name,attr,item = detector_name.split(":")
            try: item = eval(item)
            except: pass
        
        self.find_event(exp_run_event)
        if self.event is None: return None
        for d in self.event.keys():
            # E.g. d.src(): DetInfo(NoDetector.0:Evr.0), d.alias(): 'evr0'
            names = str(d.src()).split("(")[-1].split(")")[0],d.alias()
            if detector_name in names:
                value = self.event.get(d.type(),d.src())
                if attr == "": return value
                value = getattr(value,attr)()
                if item is not None: value = value[item]
                return value
        # Is detector name an EPICS process variable?
        value = self.es.value(full_detector_name)
        if value is not None: return value
        warn("Detector %r not recorded for event=%s,%s:serial_number=%s" %
            (detector_name,self.detector_name,self.event_number,
            self.serial_number))
        return None
    get = detector # shortcut

    def timestamp(self,exp_run_event):
        """Seconds since 1970-01-01 00:00:00 UTC"""
        from psana import EventId
        self.find_event(exp_run_event)
        if self.event is not None:
            s,ns = self.event.get(EventId).time()
            t = s+ns*1e-9
        else: t = nan
        return t

    def fiducial(self,exp_run_event):
        """360-Hz SLAC time stamp, 17-bit integer"""
        from psana import EventId
        self.find_event(exp_run_event)
        if self.event is not None:
            i = self.event.get(EventId).fiducials()
        else: i = nan
        return i

    def get_event_number(self,exp_run_event):
        """exp_run_event: contains experiment number, run number and event number
        'exp=xppj1216:run=17:event=0' or 'exp=xppj1216:run=17:event=rayonix,0'
        Reurn value: 0-based integer.
        """
        self.find_event(exp_run_event)
        return self.serial_number

    def find_event(self,exp_run_event):
        """exp_run_event: contain experiment number, run number and event
        number
        'exp=xppj1216:run=17:event=0' or 'exp=xppj1216:run=17:event=rayonix,0'
        """
        fields = []
        event_number = nan; detector_name = ""
        for f in exp_run_event.split(':'):
            if f.startswith("event="):
                detector_event = f.replace("event=","")
                if "," in detector_event:
                    detector_name = ",".join(detector_event.split(",")[0:-1])
                    event_number = int(detector_event.split(",")[-1])
                else: event_number = int(detector_event)
            else: fields += [f]
        exp_run = ":".join(fields)
        if exp_run != self.exp_run or detector_name != self.detector_name \
            or event_number < self.event_number:
            start = time()
            try:
                from psana import DataSource
                self.ds = DataSource(exp_run)
                self.es = self.ds.env().epicsStore()
            except Exception,msg:
                error('Failed to open datasource: %s: %s' % (exp_run,msg))
                return None
            self.exp_run = exp_run
            self.event_number = -1
            self.serial_number = -1
            self.detector_name = detector_name
            debug('Opened %r in %g seconds' % (exp_run,time()-start))
        if event_number == self.event_number: return
        for event in self.ds.events():
            self.event = event
            self.serial_number += 1
            # If a detector name is specified, count only event for which
            # this detector is recorded. 
            if detector_name != "":
                for d in self.event.keys():
                    names = str(d.src()).split("(")[-1].split(")")[0],d.alias()
                    if detector_name in names:
                        self.event_number += 1
                        break
            else: self.event_number += 1
            if event_number == self.event_number:
                break
        if not (event_number == self.event_number):
            error('Event event=%s,%s not found' % (detector_name,event_number))
            self.event = None
        else:
            from psana import EventId
            debug('found event=%s,%s:serial_number=%s:fiducial=%s' %
                (self.detector_name,self.event_number,self.serial_number,
                 self.event.get(EventId).fiducials()))

    starting_times = {} # starting time for each run

    def starting_time(self,exp_run):
        """exp_run: contains experiment number, run number, e.g.
        'exp=xppj1216:run=17'"""
        from tempfile import gettempdir
        from pickle import load,dump

        if self.starting_times == {}:
            try: self.starting_times = load(file(gettempdir()+"/datastream.starting_times.pkl"))
            except: pass

        if exp_run in self.starting_times:
            return self.starting_times[exp_run]
        from psana import DataSource,EventId
        try:
            ds = DataSource(exp_run)
            for event in ds.events():
                s,ns = event.get(EventId).time()
                t = s+ns*1e-9
                debug("%s: %s" % (exp_run,date_time(t)))
                break
        except Exception,msg:
            debug("%s: %s" % (exp_run,msg))
            t = nan
        self.starting_times[exp_run] = t
        dump(self.starting_times,file(gettempdir()+"/datastream.starting_times.pkl","w"))

        return t

    def exists(self,exp_run):
        """exp_run: contains experiment number, run number, e.g.
        'exp=xppj1216:run=17'"""
        if exp_run in self.exists_run: return self.exists_run[exp_run]
        from psana import DataSource
        debug("checking %s" % exp_run)
        try: DataSource(exp_run); exists = True
        except: exists = False
        self.exists_run[exp_run] = exists
        return exists

    exists_run = {} 

    def run(self,exp,timestamp):
        """In which run is the given timestamp?
        exp: e.g. 'exp=xppj1216'
        timestamp: time since 1 Jan 1970 00:00 UTC in seconds
        """
        run = 1
        exp_run = "%s:run=%d" % (exp,run)
        t = self.starting_time(exp_run)
        while t <= timestamp:
            run += 1
            exp_run = "%s:run=%d" % (exp,run)
            t = self.starting_time(exp_run)
        return run-1

datastream = DataStream()


def timestamp(date_time):
    """Convert a date string to number of seconds since 1 Jan 1970 00:00 UTC
    date: e.g. "2016-01-27 12:24:06.302724692-08"
    """
    from dateutil.parser import parse
    t0 = parse("1970-01-01 00:00:00+0000")
    t = parse(date_time)
    return (t-t0).total_seconds()

def date_time(seconds,timezone="US/Pacific"):
    """Date and time as formatted ASCII text, precise to 1 ms
    seconds: time elapsed since 1 Jan 1970 00:00:00 UTC
    e.g. '2016-02-01 19:14:31.707016-08:00' """
    from datetime import datetime
    import pytz
    if not isnan(seconds):
        timeUTC = datetime.utcfromtimestamp(seconds)
        timezoneLocal = pytz.timezone(timezone)
        utc = pytz.utc
        timeLocal = utc.localize(timeUTC).astimezone(timezoneLocal)
        date_time = str(timeLocal)
        # Time zone should be formatted "-0800" not "-08:00"
        if date_time.endswith(":00"): date_time = date_time[:-3]+"00"
    else: date_time = ""
    return date_time

if __name__ == "__main__": # for testing
    # Same as running from an interactive Python session.
    from time import time
    from pdb import pm # for debugging
    import logging; logging.basicConfig(level=logging.DEBUG)
    self = datastream

    exp = "exp=xppj1216:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"    
    exp_run = exp+":run=310" # 25,48
    date = "2016-01-27 12:24:06.302724692-08" # (1453926246, 302724692)

    def test():
        start = time()
        n = 0
        for i in range(0,20):
            image_id = "%s:event=rayonix,%d" % (exp_run,i)
            img = datastream.image(image_id)
            if img is not None:
                n += 1
                info("%s %s" % (image_id,img.shape))
            else: info("%s not found" % image_id)
        print "%d images, %.1f images/s" % (n,n/(time()-start))
    print("test()")
    print("datastream.detectors(exp_run)")
    print('datastream.find_event("%s:event=rayonix,0")' % exp_run)
    print('datastream.detector("%s:event=rayonix,0","XppSb3_Ipm:sum")' % exp_run)
    print('datastream.detector("%s:event=rayonix,0","XppEnds_Ipm0:channel:0")' % exp_run)
    print('datastream.detector("%s:event=rayonix,0","XPP:TIMETOOL:FLTPOS_PS")' % exp_run)
    print('image = datastream.detector("%s:event=rayonix,0","rayonix:data16")' % exp_run)
    print('datastream.run(%r,timestamp(%r))' % (exp,date))

