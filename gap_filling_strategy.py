"""Gap filling strategy: Given a list of angles already collected
What is the optimal choice of angles to complete the data set?
Friedrich Schotte, 4 Jul 2010"""

from numpy import *
__version__ = "1.1"

# Orientations already collected
angles = 0,79,118,148,187,218,257,288,323,96,72,103,141,173,212,244,281,314,351
# If rotating about a symmetry axis, reciprocal space symmetry period
period = 60.
# total orientations to collect
nangles = 40
increment = 36.

def mod_abs_diff(a,b,m): return minimum((a-b) % m,(b-a) % m)

angles = array(angles)
a = angles % period

for i in range(len(a),nangles):
    # Fill in largest gap.
    a = sort(a)
    gaps = mod_abs_diff(a,roll(a,1),period)
    largest_gap = argmax(gaps)
    a1,a2 = a[largest_gap-1],a[largest_gap]
    new_a = (a1 + 0.5 * ((a2-a1) % period)) % period
    a = concatenate((a,[new_a]))
a = sort(a)
gaps = minimum((a-roll(a,1)) % period,(roll(a,1)-a) % period)
modular_new_angles = sort(list(set(a)-set(angles % period)))

# Cover the range 0 360 deg with maximum spacing.
n = len(modular_new_angles)
offset = angles[-1]+increment
ideal_new_angles = (offset+arange(0,n)*increment) % 360
da = array([min(mod_abs_diff(a,ideal_new_angles,period)) for a in modular_new_angles])
# Assign the angles with the largest error first.
order = argsort(-da)
new_angles = zeros(n)*nan
available_indices = arange(0,n)
for k in range(0,n):
    a = modular_new_angles[order][k]
    # Pick the best matching ideal angle.
    candidates = arange(a-period,max(ideal_new_angles)+period,period)
    a2 = array([nan]*len(available_indices))
    for j in range(0,len(available_indices)):
        ideal_angle = ideal_new_angles[available_indices][j]
        a2[j] = candidates[argmin(abs(candidates-ideal_angle))]
    da = abs(a2-ideal_new_angles[available_indices])
    i = available_indices[argmin(da)]
    new_angles[i] = a2[argmin(da)]
    available_indices = available_indices[available_indices != i]
# Calculate figure of merit.
da2 = mod_abs_diff(ideal_new_angles,new_angles,360)
rms_da = sqrt(average(da2**2))

for a in angles: print "%g,"%a,
for a in rint(new_angles) % 360: print "%g,"%a,
print "\nrms_da",rms_da
