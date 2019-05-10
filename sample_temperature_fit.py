"""
Predict sample temperatrue as function of actual temperature measured ny
temperature controller.
F. Schotte, Dec 14, 2016
"""
from numpy import *
__version__ = "1.0"
from table import table
from logging import info
import logging; logging.basicConfig(level=logging.INFO)
from time_string import timestamp
from scipy.integrate import odeint
from scipy.interpolate import interp1d

# Feedback sensor temperatrue of temperature controller (RTD)
Tin_logfile = \
    "//Femto/C/All Projects/APS/Experiments/2016.11/Logfiles/Temperature-4.log"
# Measured sample temperaure (K type thermocouple, Omega thermocouple reader)
T_logfile = \
    "//Femto/C/All Projects/APS/Experiments/2016.11/Logfiles/Sample-Temperature-1.log"
timezone = "-06" # CST

# Parameters
c = 15.0 # sample heat capacity [J/K]
Rin  = 1.0 # thermal resistance heater-sample [K/W]
Rout = 10.0 # thermal resistance sample-ambient [K/W]
sigma1 = 0 #1e-8 # radiative coupling heater-sample [W/K^4]
sigma2 = 0 #1e-9 # radiative coupling sample-ambient [W/K^4]
Tout = 273+29 # ambient temperature

info("Loading data")
Tin_log = table(Tin_logfile,separator="\t")[53180:]
T_log = table(T_logfile,separator="\t")[:-120]

t_Tin = array([timestamp(t+timezone) for t in Tin_log.date_time])
T_Tin = Tin_log.value+273
Tin = interp1d(t_Tin,T_Tin,kind='linear',bounds_error=False)
t = array([timestamp(t+timezone) for t in T_log.date_time])
T = T_log.value+273

def dT_dt(T,t):
    """Derivative of temperature T at time t."""
    Pin  = 1./Rin *(Tin(t)-T) + sigma1*(Tin(t)**4-T**4) # heat float into sample
    Pout = 1./Rout*(T-Tout)   + sigma2*(T**4-Tout**4)   # head flow out of sample
    dT_dt = 1./c*(Pin-Pout) # rate of temperature change
    return dT_dt

info("Integrating")
T0 = average(T[0:10])
T_fit = odeint(dT_dt,T0,t,rtol=1e-4)

info("Plotting")
import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
from matplotlib.backends.backend_pdf import PdfPages
from pylab import rc,figure,subplot,plot,title,grid,xlabel,ylabel,xlim,ylim,\
    xticks,yticks,legend,gca,DateFormatter
PDF_file = PdfPages("sample_temperature_fit.pdf")
fig = figure(figsize=(7,5))
TZ_offset = float(timezone)/24.
def local_days(t): return t/86400. + TZ_offset
plot(local_days(t),Tin(t)-273,"-",color="blue")
plot(local_days(t),T-273,"-",color="red")
plot(local_days(t),T_fit-273,"-",color="green")
legend([
    r"$T_{in} (TEC feedback)$",
    r"$T\ (sample,\ meas.)$",
    r"$T_{fit}\ (sample,\ calc.)$"],
    fontsize=12,loc="upper left")
gca().get_legend().get_frame().set_fill(False)
gca().get_legend().get_frame().set_linewidth(0)
ymin,ymax = min(Tin(t))-273,max(Tin(t))-273
ymin,ymax = floor(ymin/10)*10,ceil(ymax/10)*10
ylim(ymin=ymin,ymax=ymax)
ylabel(r"$Temperature\ [^\circ C]$")
gca().xaxis.set_major_formatter(DateFormatter("%H:%M"))
xlabel(r"$Time\ [UTC%s]$" % timezone)
grid()
PDF_file.savefig(fig)
PDF_file.close()    
