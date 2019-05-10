import sys
sys.path = ["../TWAX/Philip","../TReX/Python","../TWAX/Friedrich"] + sys.path
from dataset import Dataset

parameter_file = \
    "/net/id14bxf/data/anfinrud_1110/Analysis/WAXS/Friedrich/parameters.twax"
dataset = Dataset(parameter_file)

logfile = dataset.combined_logfile
t = logfile["timestamp"]
I0 = logfile["x-ray"]
I = logfile["bunch-current[mA]"]

import matplotlib
matplotlib.use('PDF') # on ID14B6, default is "WxAgg", which is broken.
from pylab import *
from matplotlib.backends.backend_pdf import PdfPages

if True:
    PDF_file = PdfPages(dataset.analysis_root+"/beamline_stability.pdf")

    fig = figure(figsize=(7.5,3))
    fig.subplots_adjust(bottom=0.25,top=0.97,left=0.075,right=0.97)
    from datetime import datetime
    date = array([date2num(datetime.fromtimestamp(x)) for x in t])
    plot(date,I0,".",ms=1)
    gca().xaxis_date()
    formatter = DateFormatter('%a %d %Hh')
    gca().xaxis.set_major_formatter(formatter)
    xticks(rotation=90,fontsize=8)
    grid()
    ylim(0,1.2)
    yticks(fontsize=8)
    ylabel("X-ray I0 [norm.]",fontsize=8)
    PDF_file.savefig(fig)

    fig = figure(figsize=(7.5,3))
    fig.subplots_adjust(bottom=0.25,top=0.97,left=0.075,right=0.97)
    from datetime import datetime
    date = array([date2num(datetime.fromtimestamp(x)) for x in t])
    plot(date,I,".",ms=1)
    gca().xaxis_date()
    formatter = DateFormatter('%a %d %Hh')
    gca().xaxis.set_major_formatter(formatter)
    xticks(rotation=90,fontsize=8)
    grid()
    ylim(ymin=0,ymax=max(I)*1.2)
    yticks(fontsize=8)
    ylabel("bunch current [mA]",fontsize=8)
    PDF_file.savefig(fig)

    fig = figure(figsize=(7.5,3))
    fig.subplots_adjust(bottom=0.25,top=0.97,left=0.075,right=0.97)
    plot(date,I0/(I/average(I)),".",ms=1)
    gca().xaxis_date()
    formatter = DateFormatter('%a %d %Hh')
    gca().xaxis.set_major_formatter(formatter)
    xticks(rotation=90,fontsize=8)
    grid()
    ylim(0,1.2)
    yticks(fontsize=8)
    ylabel("X-ray I0 scaled by bunch current",fontsize=8)
    PDF_file.savefig(fig)

    PDF_file.close()
