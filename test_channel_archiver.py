from channel_archiver import channel_archiver
from time_string import timestamp

start_time = timestamp("2020-12-16 08:00:00-0500")
end_time = timestamp("2020-12-16 12:00:00-0500")
t, RH = channel_archiver("LaserLab").history("BigBox:RH", start_time, end_time)
