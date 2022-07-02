"""
One-dimensional scans

Run simulation:

 from sim_scan import *
 data=rscan(sim_taby,-0.2,0.2,20,sim_flux)
 COM(data)
 app = wx.App()
 Plot(data)

Run electronic test:

 tmode.value = 1
 trigger="pulses.value=1;sleep(0.1)"
 data=rscan (sim_taby,-0.2,0.2,10,xray_pulse,trigger=trigger)

Center the laser beam:

 data=rscan (LaserZ,-1,1,50,laser_pulse,plot=True)
 data=rscan (LaserX,-0.4,0.4,40,laser_pulse,plot=True)

Tweak the optical table with single X-ray pulses:

 tmode.value = 1
 trigger="pulses.value=1;sleep(0.1)"
 data=rscan (TableY,-0.05,0.05,10,xray_pulse,trigger=trigger,plot=True)
 COM(data)

Measure the X-ray beam profile:

 data=rscan (sx,-0.25,0.25,50,xray_pulse,plot=True)

 data=read_xy("J:\\anfinrud_0803\\Scans\\2008.03.14 X-ray Y proj 2.txt")
 FWHM(data),COM(data),CFWHM(data)

Feb 28 2018 Valentyn Stadnytskyi
version 1.6 - Added analysis of the slit scan.
                slit_scan_analysis_1d(data)
            This code takes "data", takes derivative and fits it with 2 gaussians.
            The initial parameters for the fit are taken:
            amplitudes: max/min values
            positions: max/min argument
            width: 200 um <- I have tested with 56 um as well. It always finds nice fit.

version 1.7 -   March 1, 2018, Valentyn
            added compensation for the pulse fluctuations
            in the X-Ray hutch Lecroy ps laser ch4 area
            (search for Valentyn March 1, 2018)
            Later commented it out since it wasn't doing much(this line added on July 4, 2018)

Friedrich Schotte, 2008-12-03/2015-07-23
Valentyn Stadnytskyi, 2018-02-28/2018-03-01

Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2008-03-18
Date last modified: 2022-05-01
Revision comment: Cleanup: Formatting, typos, static code analysis warnings
"""
__version__ = "1.8.1"

from logging import info
from time import time
from threading import Thread
from typing import List, Union

from numpy import sqrt, isnan, nan

from Plot import Plot
from sleep import sleep


def rscan(
    motors,
    begins: Union[float, List[float]],
    ends: Union[float, List[float]],
    nsteps,
    counters=None,
    averaging_time=0.0,
    logfile=None,
    trigger=None,
    plot=False,
    verbose=True,
    data=None,
):
    """
    Performs a relative scan around the current position.
    This moves 'motor' from the current position - 'begin' to
    the current position + 'end' in 'nsteps' steps, while
    reading 'counters' each time the motor stops.
    The number of scan points acquired is nsteps+1. 
    The motor returns to the initial position after the scan is complete.
    If 'averaging_time' (in seconds) is given the motor stops for the given
    time at each scan point, while the counter result is averaged.
    'counters' can be either a single counter or list of counters (in square
    brackets).
    'trigger' is a python command to be executed before each scan point.
    If 'plot' is True the scan data is displayed a curve in a graphics window
    during the scan.
    If 'verbose' is True scan data is printed in the terminal window during
    the scan.
    If 'data' is given, this list is used to store the scan result, rather than
    creating a new one.
    """
    if counters is None:
        counters = []

    if not isinstance(motors, list):
        motors = [motors]
    nm = len(motors)

    if not isinstance(begins, list):
        begins = [begins]
    while len(begins) < nm:
        begins.append(begins[-1])
    for i in range(0, nm):
        begins[i] = float(begins[i])

    if not isinstance(ends, list):
        ends = [ends]
    while len(ends) < nm:
        ends.append(ends[-1])
    for i in range(0, nm):
        ends[i] = float(ends[i])

    nsteps = int(round(nsteps))
    if not isinstance(counters, list):
        counters = [counters]
    nc = len(counters)
    steps = list(range(0, nm))
    for i in range(0, nm):
        steps[i] = (ends[i] - begins[i]) / nsteps
    if logfile is not None:
        logfile = open(logfile, "w")

    if data is None:
        data = []
        return_data = True
    else:
        while len(data) > 0:
            data.pop()
        return_data = False

    cancelled = False

    # Record initial motor positions.
    starting_positions = list(range(0, nm))
    for i in range(0, nm):
        starting_positions[i] = motors[i].value

    # Write scan header.
    line = "#"
    for i in range(0, nm):
        if hasattr(motors[i], "name"):
            line += motors[i].name
        else:
            line += "pos"
        if hasattr(motors[i], "unit") and motors[i].unit != "":
            line += "/" + motors[i].unit
        line += "\t"
    for i in range(0, nc):
        if hasattr(counters[i], "name"):
            line += counters[i].name
        else:
            line += "\tcount"
        if hasattr(counters[i], "unit") and counters[i].unit != "":
            line += "/" + counters[i].unit
        line += "\t"
    line.strip("\t")
    if verbose:
        print(line)
    if logfile is not None:
        logfile.write(line + "\n")
        logfile.flush()

    # Open plot window.
    if plot:
        StartMyMainLoop()
        plot_data.append([[0, 0], [1, 1]])

    positions = list(range(0, nm))
    counts = list(range(0, nc))

    try:
        for j in range(0, nsteps + 1):
            try:
                # Move motors
                for i in range(0, nm):
                    motors[i].value = starting_positions[i] + begins[i] + steps[i] * j
                # Wait for motors to stop
                while 1:
                    moving = False
                    for i in range(0, nm):
                        if hasattr(motors[i], "moving"):
                            moving = moving or motors[i].moving
                    if not moving:
                        break
                    sleep(0.01)
                for i in range(0, nm):
                    positions[i] = motors[i].value
                # Acquire scan point
                if averaging_time == 0:
                    if trigger:
                        exec(trigger)
                    for i in range(0, nc):
                        counts[i] = counters[i].value  # /laser_scope.measurement(1).value
                    # line above March 1, 2018 Valentyn added /laser_scope.measurement(1).value 
                else:
                    for i in range(0, nc):
                        if hasattr(counters[i], "count_time"):
                            counters[i].count_time = averaging_time
                            # laser_scope.measurement(1).count_time = averaging_time
                    for i in range(0, nc):
                        if hasattr(counters[i], "start"):
                            counters[i].start()
                            # laser_scope.measurement(1).start()
                            # line above March 1, 2018, Valentyn added
                    if trigger:
                        exec(trigger)
                    sleep(averaging_time)
                    for i in range(0, nc):
                        if hasattr(counters[i], "stop"):
                            counters[i].stop()
                            # laser_scope.measurement(1).stop()
                            # line above March 1, 2018, Valentyn added
                    for i in range(0, nc):
                        if hasattr(counters[i], "average"):
                            counts[i] = counters[i].average  # /laser_scope.measurement(1).average
                        # line above March 1, 2018, Valentyn added /laser_scope.measurement(1).average
                        else:
                            counts[i] = counters[i].value

                # Write scan record
                line = ""
                for i in range(0, nm):
                    line += str(positions[i]) + "\t"
                for i in range(0, nc):
                    line += str(counts[i]) + "\t"
                line.strip("\t")
                if verbose:
                    print(line)
                if logfile is not None:
                    logfile.write(line + "\n")
                    logfile.flush()

                # Skip 'Not a Number' values (problems with plotting)
                skip = False
                for val in positions + counts:
                    if isnan(val):
                        skip = True
                if not skip:
                    data.append(positions + counts)

                # Update plot window
                if plot:
                    plot_data[-1] = data + []

            except KeyboardInterrupt:
                cancelled = True
                break

        # Return motors to the starting positions
        for i in range(0, nm):
            motors[i].value = starting_positions[i]
        # Wait for motors to stop
        while not cancelled:
            try:
                moving = False
                for i in range(0, nm):
                    if hasattr(motors[i], "moving"):
                        moving = moving or motors[i].moving
                if not moving:
                    break
                sleep(0.01)
            except KeyboardInterrupt:
                break

        # Restart the counter after than scan is done (useful for oscilloscope-based counters)
        for i in range(0, nc):
            if hasattr(counters[i], "start"):
                counters[i].start()
                laser_scope.measurement(1).start()

        if return_data:
            return data
    except KeyboardInterrupt:
        info("Returning motors to the starting positions.")
        for i in range(0, nm):
            motors[i].value = starting_positions[i]
    finally:
        info("Returning motors to the starting positions.")
        for i in range(0, nm):
            motors[i].value = starting_positions[i]


def peak_info(data):
    """Generate a report about peak width and position"""
    return "FWHM %.3f mm at %.3f mm, COM %.3f mm, peak %.2g at %.3f mm" % \
           (FWHM(data), CFWHM(data), COM(data), peak(data), peak_pos(data))


def peak(data):
    """Returns the maximum y of a curve given as list of [x,y] values"""
    return max(yvals(data))


def peak_to_peak(data):
    """Returns peak to peak difference of the y values of a curve given as
    list of [x,y] values"""
    return max(yvals(data)) - min(yvals(data))


def peak_pos(data):
    """Returns the x value of the maximum curve given as list of [x,y] values"""
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    if n < 1:
        return nan
    x_at_ymax = x[0]
    ymax = y[0]
    for i in range(0, n):
        if data[i][1] > ymax:
            x_at_ymax = x[i]
            ymax = y[i]
    return x_at_ymax


def COM(data):
    """Calculates the center of mass of the positive peak of a curve
    given as list of [x,y] values"""
    data = subtract_baseline(data)
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    # Subtract baseline
    y0 = min(y)
    for i in range(0, n):
        y[i] -= y0
    sum_xy = 0
    for i in range(0, n):
        sum_xy += x[i] * y[i]
    return sum_xy / sum(y)


def RMSD(data):
    """Calculates root-mean-square deviation width of the positive peak of
    a curve given as list of [x,y] values"""
    data = subtract_baseline(data)
    x0 = COM(data)
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    sum_x2 = 0
    for i in range(0, n):
        sum_x2 += y[i] * (x[i] - x0) ** 2
    return sqrt(sum_x2 / sum(y))


def FWHM(data):
    """Calculates full-width at half-maximum of a positive peak of a curve
    given as list of [x,y] values"""
    if len(data) >= 3:
        x = xvals(data)
        y = yvals(data)
        n = len(data)
        HM = (min(y) + max(y)) / 2
        for i in range(0, n):
            if y[i] > HM:
                break
        else:
            i = 1
        x1 = interpolate_x((x[i - 1], y[i - 1]), (x[i], y[i]), HM)
        for i in range(n-1, -1, -1):
            if y[i] > HM:
                break
        else:
            i = n-2
        x2 = interpolate_x((x[i + 1], y[i + 1]), (x[i], y[i]), HM)
        FWHM = abs(x2 - x1)
    else:
        FWHM = nan
    return FWHM


def CFWHM(data):
    """Calculates the center of the full width half of the positive peak of
    a curve given as list of [x,y] values"""
    if len(data) >= 3:
        x = xvals(data)
        y = yvals(data)
        n = len(data)
        HM = (min(y) + max(y)) / 2
        for i in range(0, n):
            if y[i] > HM:
                break
        else:
            i = 1
        x1 = interpolate_x((x[i - 1], y[i - 1]), (x[i], y[i]), HM)
        for i in range(n-1, -1, -1):
            if y[i] > HM:
                break
        else:
            i = n-2
        x2 = interpolate_x((x[i + 1], y[i + 1]), (x[i], y[i]), HM)
        CFWHM = (x2 + x1) / 2.
    else:
        CFWHM = nan
    return CFWHM


def remove_NaN(data):
    """Filters out 'Not a Number' values from a list of [x,y] values"""
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    data2 = []
    for i in range(0, n):
        if not isnan(x[i]) and not isnan(y[i]):
            data2.append([x[i], y[i]])
    return data2


def subtract_baseline(data):
    """Baseline-correct a curve given as list of [x,y] values"""
    x = xvals(data)
    y = yvals(data)
    n = len(data)
    y0 = min(y)
    for i in range(0, n):
        y[i] -= y0
    return list(zip(x, y))


def interpolate_x(p1, p2, y):
    """Linear interpolation between two points"""
    (x1, y1) = p1
    (x2, y2) = p2
    # In case result is undefined, midpoint is as good as any value.
    if y1 == y2:
        return (x1 + x2) / 2.
    x = x1 + (x2 - x1) * (y - y1) / float(y2 - y1)
    # print "interpolate_x [%g,%g,%g][%g,%g,%g]" % (x1,x,x2,y1,y,y2)
    return x


def xvals(xy_data):
    """xy_data = list of (x,y)-tuples. Returns list of x values only."""
    xvals = []
    for i in range(0, len(xy_data)):
        xvals.append(xy_data[i][0])
    return xvals


def yvals(xy_data):
    """xy_data = list of (x,y)-tuples. Returns list of y values only."""
    yvals = []
    for i in range(0, len(xy_data)):
        yvals.append(xy_data[i][1])
    return yvals


def print_xy(xy_data):
    """Displays (x,y) tuples as two columns"""
    for i in range(0, len(xy_data)):
        print("%g\t%g" % (xy_data[i][0], xy_data[i][1]))


def save_xy(xy_data, filename):
    """Write (x,y) tuples as two-column tab separated ASCII file."""
    output = open(filename, "w")
    for i in range(0, len(xy_data)):
        output.write("%g\t%g\n" % (xy_data[i][0], xy_data[i][1]))


def read_xy(filename):
    """Reads two two-column ASCII file and returns as list of floating point
    [x,y] pairs"""
    data = []
    infile = open(filename)
    line = infile.readline()
    while line != '':
        try:
            cols = line.split()
            x = float(cols[0])
            y = float(cols[1])
            data.append([x, y])
        except ValueError:
            pass
        line = infile.readline()
    return data


def timescan(counters=None, waiting_time=1, averaging_time=0, total_time=1e1000,
             logfile=None):
    """Monitor a counter or list of counters at a regular time interval.
    If "waiting_time" is not specified that interval is 1 second.
    "counters" can be either a single counter or list of counters (in square brackets).
    If "total_time" is given, the scan is ended after the specified number of seconds.
    Otherwise, it is ended on keyboard interrupt (Control-C).
    """

    if counters is None:
        counters = []
    if not isinstance(counters, list):
        counters = [counters]
    nc = len(counters)
    if logfile is not None:
        logfile = open(logfile, "w")

    # Write scan header
    line = "#date\ttime/s\t"
    for i in range(0, nc):
        if hasattr(counters[i], "name"):
            line += counters[i].name
        else:
            line += "\tcount"
        if hasattr(counters[i], "unit") and counters[i].unit != "":
            line += "/" + counters[i].unit
        line += "\t"
    line.strip("\t")
    # print line # commented on Feb 28 2018, Valentyn
    if logfile is not None:
        logfile.write(line + "\n")
        logfile.flush()

    counts = list(range(0, nc))
    n = 0
    start = time()

    while time() < start + total_time:
        try:
            t = time()
            # Acquire scan point
            if averaging_time == 0:
                for i in range(0, nc):
                    counts[i] = counters[i].value
            else:
                for i in range(0, nc):
                    if hasattr(counters[i], "count_time"):
                        counters[i].count_time = averaging_time
                for i in range(0, nc):
                    if hasattr(counters[i], "start"):
                        counters[i].start()
                sleep(averaging_time)
                for i in range(0, nc):
                    if hasattr(counters[i], "stop"):
                        counters[i].stop()
                for i in range(0, nc):
                    if hasattr(counters[i], "average"):
                        counts[i] = counters[i].average
                    else:
                        counts[i] = counters[i].value
            # Write scan record
            line = date_string(t) + "\t" + str(t - start) + "\t"
            for i in range(0, nc):
                line += str(counts[i]) + "\t"
            line.strip("\t")
            print(line)
            if logfile is not None:
                logfile.write(line + "\n")
                logfile.flush()
            n = n + 1
            dt = n * waiting_time - (time() - start)
            while dt > 0:
                sleep(min(dt, 0.1))
                dt = n * waiting_time - (time() - start)
        except KeyboardInterrupt:
            break


def date_string(seconds):
    from datetime import datetime
    date = str(datetime.fromtimestamp(seconds))
    return date[:-3]  # omit microseconds


MyMainLoopThread = Thread()


def StartMyMainLoop():
    global MyMainLoopThread
    if not MyMainLoopThread.is_alive():
        MyMainLoopThread = Thread(target=MyMainLoop, name="MyMainLoop")
        MyMainLoopThread.start()


app = None


def MyMainLoop():
    global app
    import wx
    from time import sleep
    app = wx.GetApp() if wx.GetApp() else wx.App()
    event_loop = wx.GUIEventLoop()
    wx.EventLoop.SetActive(event_loop)
    while True:
        while event_loop.Pending():
            event_loop.Dispatch()
        event_loop.ProcessIdle()
        update_plots()
        sleep(0.1)


def gauss(x, a1, x01, fwhm1, a2, x02, fwhm2):
    from numpy import exp
    return a1 * exp(-(x - x01) ** 2 / (2 * (fwhm1 / 2.355) ** 2)) + a2 * exp(-(x - x02) ** 2 / (2 * (fwhm2 / 2.355) ** 2))


def slit_scan_analysis_1d(xy_data, plot=False, img_filename=''):
    from numpy import asarray, gradient
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from numpy import argmin, argmax
    arr = asarray(xy_data)  # create numpy array
    x = arr[:, 0]
    y = arr[:, 1]
    grad_y = gradient(y)
    p_opt, _ = curve_fit(gauss, x, grad_y, p0=[max(grad_y), x[argmax(grad_y)], 0.2, min(grad_y), x[argmin(grad_y)], 0.2])
    print('FWHM_1 = ' + str(round(1000 * p_opt[2], 1)) + ' um' + ' and FWHM_2= ' + str(round(p_opt[5] * 1000, 1)) + ' um' + ' and average of ' + str(
        round(1000 * (0.5 * p_opt[2] + 0.5 * p_opt[5]), 1)) + ' um')
    print('center1 = ' + str(round(p_opt[1], 3)) + ' mm' + ' and center2 = ' + str(round(p_opt[4], 3)) + ' mm' + ' and center at ' + str(
        round(0.5 * p_opt[4] + 0.5 * p_opt[1], 3)) + ' mm')
    # return x, gauss(x,*p_opt), x, grad_y
    plt.plot(x, grad_y, 'o')
    plt.plot(x, gauss(x, *p_opt), linewidth=4)
    plt.title('FWHM_1 = ' + str(round(1000 * p_opt[2], 1)) + ' um' + ' and FWHM_2 = ' + str(round(p_opt[5] * 1000, 1)) + ' um' + '\n and center at' + str(
        round(0.5 * p_opt[4] + 0.5 * p_opt[1], 3)) + ' mm')
    if plot:
        plt.show()
    try:
        plt.savefig(img_filename)
    except OSError:
        print("couldn't save img to a file")


def scan_and_analyse(axis='GonZ', filename='/Laser Z scan-3'):
    """
    filename is a local filename in the folder dir.
    """
    if axis == 'GonZ':
        data = rscan(GonZ, -0.5, +0.5, 200, xray_pulse, 1.0, plot=True)
    elif axis == 'GonY':
        data = rscan(GonY, -2, +2, 160, xray_pulse, 1.0, plot=True)
    elif axis == 'GonX':
        data = rscan(GonX, -2, +2, 40, xray_pulse, 1.0, plot=True)
    else:
        data = []
    if data:
        logfile = directory + filename
        try:
            save_xy(data, logfile + '.txt')
        except OSError:
            print("couldn't save to a file")
        # noinspection PyBroadException
        try:
            slit_scan_analysis_1d(data, plot=True, img_filename=logfile + '.png')
        except Exception:
            print("couldn't plot and analyse")
    return data


plots = []
plot_data = []


def update_plots():
    while len(plots) < len(plot_data):
        plots.append(Plot())
    for plot, data in zip(plots, plot_data):
        try:
            if plot.data != data:
                plot.data = data
                plot.update()
        except RuntimeError:
            pass


if __name__ == "__main__":  # For testing
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from instrumentation import *  # Beamline
    import os

    directory = '/net/mx340hs/data/anfinrud_1807/Scans/2018.07.04 ns laser beam profile'
    logfile = directory + "/Laser Z scan-1.txt"
    if not os.path.exists(directory):
        print("directory didn't exist, creating (%r)" % directory)
        os.mkdir(directory)
    else:
        print('directory %r exists' % directory)
    print('logfile = %r' % logfile)
    print('data = rscan(GonZ,-0.4,+0.4,160,xray_pulse,1.0,plot=True)')
    print('data = rscan(GonY,-2,+2,160,xray_pulse,1.0,plot=True)')
    print('data = rscan(GonX,-2,+2,40,xray_pulse,1.0,plot=True)')
    print('save_xy(data,%r)' % logfile)
    print('"FWHM %.3f @ %.3f" % (FWHM(data),CFWHM(data))')
    print('slit_scan_analysis_1d(data, plot = True) #run analysis and plot the result')
    print('data = scan_and_analyse(axis = "GonZ", filename = "/Laser Z scan-3")')
