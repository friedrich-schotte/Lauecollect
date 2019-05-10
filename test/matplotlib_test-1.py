from pylab import *
from table import table
from datetime import datetime

filename = '//id14bxf/data/anfinrud_1006/Data/Test/Test1/backup/Test1 (corrupted).log'
logfile = table(filename,separator="\t")

def seconds(date_time):
    "Convert a date string to number of seconds til 1 Jan 1970."
    from time import strptime,mktime
    return mktime(strptime(date_time,"%d-%b-%y %H:%M:%S"))

t = map(seconds,logfile.date_time)
nom_delay = logfile.nom_delay
act_delay = logfile.act_delay
dt = act_delay - nom_delay
table(filename,separator="\t")
date = [date2num(datetime.fromtimestamp(x)) for x in t]
plot(date,dt/1e-12,'.')
show()
