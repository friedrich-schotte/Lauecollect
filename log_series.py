from numpy import floor,ceil,log10

class X(object):
    def log_timepoint(t):
        """If a time point of a 'logarithmic' time series is rounded to three
        decimal digits precision, this retores the excact missing digits,
        assuming that there are an integer number of points per decade,
        to a maximum of 20 points per decade."""
        if t <= 0: return t
        logt = log10(t)
        magnitude = 10**floor(logt)
        for n in range (1,21):
            T = 10**(round(logt*n)/n)
            if abs(t-T)/magnitude < 0.005: return T
        return t
    log_timepoint = staticmethod(log_timepoint)

if __name__ == "__main__":
    print X.log_timepoint(-1e-9)
    print X.log_timepoint(0)
    print X.log_timepoint(1e-9)
    print X.log_timepoint(1.78e-9)
    print X.log_timepoint(3.16e-9)
    print X.log_timepoint(5.62e-9)
    print X.log_timepoint(5.63e-9)
