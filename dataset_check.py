"""
Check a dataset collected with PP collect for consistency and completemess
Author: Friedrich Schotte
Date created: 2019-03-19
Date last modified: 2019-03-20
"""
__version__ = "1.0"

from logging import debug,info,warn,error

from collect import Collect
class Dataset(Collect):
    """PP Collect generated datset"""
    name = "Collect"

    @property
    def n_expected(self):
        """Number of images attempeted to collect, whether sucessful or not"""
        if self.collection_finished: n = self.n
        else: n = self.n_finished
        return n

    @property
    def n_finished(self):
        """Number of images attempeted to collect, whether sucessful or not"""
        logged = self.logfile_has_entries(self.xray_image_filenames)
        from numpy import where
        i = where(logged)[0]
        n = i[-1]+1 if len(i) > 0 else 0
        return n

    @property
    def collection_finished(self):
        from time import time
        finished = file_timestamp(self.logfile_name) < time()-20
        finished = finished and self.dataset_started
        return finished

    @property
    def logfile_entries_missing(self):
        logged = self.logfile_has_entries(self.xray_image_filenames)
        logged = logged[0:self.n_expected]
        n_missing = sum(logged == False)
        return n_missing

    @property
    def logged(self):
        logged = self.logfile_has_entries(self.xray_image_filenames)
        logged = logged[0:self.n_expected]
        return logged

    @property
    def xray_image_time_differences(self):
        from numpy import array
        dt = []
        for f in dataset.xray_images_collected:
            dt += [file_timestamp(f) - dataset.logfile_timestamp(f)]
        dt = array(dt)
        return dt

    @property
    def xray_images_expected(self):
        return self.xray_image_filenames[0:self.n_expected]

    @property
    def xray_images_missing(self):
        from exists import exist_files
        filenames = self.xray_image_filenames[0:self.n_expected]
        return ~exist_files(filenames)

    @property
    def xray_scope_traces_expected(self):
        n_expected = self.n_expected * self.sequences_per_xray_image
        return self.xray_scope_trace_filenames[0:n_expected]

    @property
    def xray_scope_traces_missing(self):
        from exists import exist_files
        return ~exist_files(self.xray_scope_traces_expected)

    @property
    def xray_scope_trace_time_differences(self):
        N = self.sequences_per_xray_image
        sequence = self.sequences[0]
        T = sequence.period*sequence.tick_period()
        
        dt = []
        for i,f in enumerate(dataset.xray_scope_trace_filenames):
            offset = (i % N - (N-1)) * T
            dt += [file_timestamp(f) - (dataset.logfile_timestamp(f)+offset)]
        from numpy import array
        dt = array(dt)
        return dt

    @property
    def laser_scope_traces_expected(self):
        n_expected = self.n_expected * self.sequences_per_xray_image
        return self.laser_scope_trace_filenames[0:n_expected]

    @property
    def laser_scope_traces_missing(self):
        from exists import exist_files
        return ~exist_files(self.laser_scope_traces_expected)

    @property
    def laser_scope_trace_time_differences(self):
        N = self.sequences_per_xray_image
        sequence = self.sequences[0]
        T = sequence.period*sequence.tick_period()
        
        dt = []
        for i,f in enumerate(dataset.laser_scope_trace_filenames):
            offset = (i % N - (N-1)) * T
            dt += [file_timestamp(f) - (dataset.logfile_timestamp(f)+offset)]
        from numpy import array
        dt = array(dt)
        return dt

    @property
    def report(self):
        report = ""
        if self.collection_finished: status = "finished"
        elif self.dataset_started: status = "in progress"
        else: status = "not started"
        report += "Dataset: %s\n" % self.basename
        report += "Path: %s\n" % shortened_path(self.directory)

        report += "Progress: %s/%s (%s)\n" % (dataset.n_finished,dataset.n,status)

        logged = self.logged
        report += "Logfile entries: %r/%r \n" % (sum(logged),len(logged))

        expected = self.xray_images_expected
        collected = self.xray_images_collected
        missing = self.xray_images_missing
        report += "X-ray image files: %r/%r " % (len(collected),len(expected))
        if sum(missing) >= 1:
            from numpy import where
            first_missing = where(missing)[0][0]
            first_file_missing = expected[first_missing]
            from os.path import basename
            report += "(missing: %d %r" % (first_missing+1,basename(first_file_missing))
            if sum(missing) >= 2: report += ", ..."
            report += ")"
        report += "\n"

        expected = self.xray_scope_traces_expected
        collected = self.xray_scope_traces_collected
        missing = self.xray_scope_traces_missing
        report += "X-ray scope traces: %r/%r " % (len(collected),len(expected))
        if sum(missing) >= 1:
            from numpy import where
            first_missing = where(missing)[0][0]
            first_file_missing = expected[first_missing]
            from os.path import basename
            report += "(missing: %d %r" % (first_missing+1,basename(first_file_missing))
            if sum(missing) >= 2: report += ", ..."
            report += ")"
        report += "\n"

        expected = self.laser_scope_traces_expected
        collected = self.laser_scope_traces_collected
        missing = self.laser_scope_traces_missing
        report += "Laser scope traces: %r/%r " % (len(collected),len(expected))
        if sum(missing) >= 1:
            from numpy import where
            first_missing = where(missing)[0][0]
            first_file_missing = expected[first_missing]
            from os.path import basename
            report += "(missing: %d %r" % (first_missing+1,basename(first_file_missing))
            if sum(missing) >= 2: report += ", ..."
            report += ")"
        report += "\n"
        
        dt = self.xray_image_time_differences
        report += "X-ray image timestaps: offset %.3f s, sdev %.3f s\n" \
            % (nanmean(dt),nanstd(dt))
        dt = self.xray_scope_trace_time_differences
        report += "X-ray scope trace timestaps: offset %.03f s, sdev %.3f s\n" \
            % (nanmean(dt),nanstd(dt))
        dt = self.laser_scope_trace_time_differences
        report += "Laser scope trace timestaps: offset %.03f s, sdev %.3f s\n" \
            % (nanmean(dt),nanstd(dt))

        report = report.replace("offset nan s","-")
        report = report.replace("sdev nan s","-")
        report = report.replace(" 0/"," -/")
        report = report.replace("/0 ","/- ")

        return report

    def monitor(self):
        """Keep generating reports"""
        import autoreload
        from sleep import sleep
        from sys import stdout
        try:
            while True:
                report = "\n\n"+self.report+"\n"
                report += "[Updating in 10 s... Control-C to end]"
                stdout.write(report)
                sleep(10)
        except KeyboardInterrupt: pass
        stdout.write("\n\n")

dataset = Dataset()

def nanmean(a):
    from numpy import mean,nan,isnan,any
    try:
        valid = ~isnan(a)
        return mean(a[valid]) if any(valid) else nan
    except: return nan

def nanstd(a):
    from numpy import std,nan,isnan,any
    try:
        valid = ~isnan(a)
        return std(a[valid]) if any(valid) else nan
    except: return nan

def file_timestamp(filename):
    from os.path import getmtime
    from numpy import nan
    try: timestamp = getmtime(filename)
    except: timestamp = nan
    return timestamp

def shortened_path(pathname,max_length=40):
    from os.path import basename,dirname
    shortened_path = ""
    while len(basename(pathname)+"/"+shortened_path) <= max_length+1:
        shortened_path = basename(pathname)+"/"+shortened_path
        pathname = dirname(pathname)
    shortened_path = shortened_path.rstrip("/")
    return shortened_path


if __name__ == "__main__":
    from pdb import pm # for debugging
    self = dataset # for debugging

    ##dataset.monitor()

    ##print("dataset.directory")
    print("dataset.xray_image_time_differences")
    print("dataset.xray_scope_trace_time_differences")
    print("print(dataset.report)")
