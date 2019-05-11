"""Friedrich Schotte, 9 Nov 2012"""

def interpolate_2D(PHI,Z,OFFSET,phi,z):
    """Perform two-dimensional interpolation of data define on a rectangular
    grid.
    PHI,Z: arrays, define grid of support points.
    OFFSET: array, defines value at support points.
    phi,z: where to interpolate
    Return value: OFFSET at (phi,z)"""
    from numpy import concatenate,mean,nan,unique,sort
    if len(OFFSET) == 0: return nan
    
    # Take into account that angles are periodic.    
    phi %= 360
    PHI %= 360
    PHI = concatenate((PHI-360,PHI,PHI+360))
    Z = concatenate((Z,Z,Z))
    OFFSET = concatenate((OFFSET,OFFSET,OFFSET))

    # Find the next smaller and larger phi.
    # If interpolation is not possible, extrapolate.
    phis = unique(PHI)
    if phi < min(phis):   phi1,phi2 = phis[0:2][0],phis[0:2][-1]
    elif phi > max(phis): phi1,phi2 = phis[-2:][0],phis[-2:][-1]
    else: phi1,phi2 = max(phis[phis<=phi]),min(phis[phis>=phi])

    # Find the next smaller and larger z for both phis.
    # If interpolation is not possible, extrapolate.
    zs1 = unique(Z[PHI==phi1])
    zs2 = unique(Z[PHI==phi2])
    if z < min(zs1):   z11,z12 = zs1[0:2][0],zs1[0:2][-1]
    elif z > max(zs1): z11,z12 = zs1[-2:][0],zs1[-2:][-1]
    else: z11,z12 = max(zs1[zs1<=z]),min(zs1[zs1>=z])

    if z < min(zs2):   z21,z22 = zs2[0:2][0],zs2[0:2][-1]
    elif z > max(zs2): z21,z22 = zs2[-2:][0],zs2[-2:][-1]
    else: z21,z22 = max(zs2[zs2<=z]),min(zs2[zs2>=z])

    # Look up the offset at the four support points.
    offset11 = mean(OFFSET[(PHI==phi1) & (Z==z11)])
    offset12 = mean(OFFSET[(PHI==phi1) & (Z==z12)])
    offset21 = mean(OFFSET[(PHI==phi2) & (Z==z21)])
    offset22 = mean(OFFSET[(PHI==phi2) & (Z==z22)])

    # Interpolate in z.
    if z12 == z11: offset1 = offset11
    else: offset1 = offset11*(z12-z)/(z12-z11) + offset12*(z-z11)/(z12-z11)
    if z22 == z21: offset2 = offset21
    else: offset2 = offset21*(z22-z)/(z22-z21) + offset22*(z-z21)/(z22-z21)
    # Interpolate in phi.
    if phi1 == phi2: offset = offset1
    else: offset = offset1*(phi2-phi)/(phi2-phi1) + offset2*(phi-phi1)/(phi2-phi1)
    return offset


if __name__ == "__main__":
    import lauecollect_new as lauecollect
    from numpy import array
    lauecollect.param.path = "//id14bxf/data/anfinrud_1211/Data/Laue/PYP-E46Q-H/PYP-E46Q-H46.1-288K"
    PHI,Z,X,Y,OFFSET = array(lauecollect.align_table())[0:5]
    ##PHI,Z,OFFSET = PHI[0:2],Z[0:2],OFFSET[0:2]
    phi,z = 0+1,6.814-0
    offset = interpolate_2D(PHI,Z,OFFSET,phi,z)
    print offset
