"""This tells the number of seconds to the next top-up.
This is needed to decide whether it is necessary to postpone the next image
until after the next top-up, to avoid collecting data during a top-up. """
__version__ = "1.0"
from CA import PV

time_to_next_refill = PV("Mt:TopUpTime2Inject")
