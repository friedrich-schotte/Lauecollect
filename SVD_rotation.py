"""
Perform a basis rotation on SVD results, optimizing temporal auto-correlation
of the SVD time courses

Based on:
Eric Henry and James Hofrichter, "Singular Value Decomposition:
Application to Analysis of Experimental Data", Meth. Enzymol. 210,129 (1992)

Wikipedia article "Principal component analysis",
section 6 "Computing PCA using the covariance method"
https://en.wikipedia.org/wiki/Principal_component_analysis#Computing_PCA_using_the_covariance_method

Friedrich Schotte, 5 Dec 2009 - 7 Apr 2017
"""
__version__ = "2.2" # 2D auto-correaction, diagnostics output
from logging import debug,info,warn,error
import glogging as g

def SVD_rotation_max_V_auto_correlation(U,s,V):
    """"Maximize the auto-correlation of the V vectors"""
    from numpy import array,argsort,dot,diag
    from numpy.linalg import eig

    S = diag(s)
    # Calculate auto-correlation.
    N = len(V)
    C = array([sum(V[i,:-1]*V[i,1:]) for i in range(N)])
    # Sort the V vectors by auto-correlation.
    order = argsort(C)[::-1]
    C = C[order]
    V = V[order,:]
    U = U[:,order]
    # Find the rotation matrix optimizing the auto-correlation.
    X = array([[sum(V[i,:-1]*V[j,1:]) for i in range(N)] for j in range(N)])
    Xs = (X + X.T)/2
    w,R = eig(Xs)
    # Sort eigenvectors according to eigenvalues
    order = argsort(w)[::-1] # descending order
    w = w[order] 
    R = R[:,order]

    # Apply the basis rotation.
    USR = dot(dot(U,S),R)
    RTV = dot(R.T,V)
    return USR,RTV

def SVD_rotation_max_V_2D_auto_correlation(U,s,V,(NX,NY),diagnostics=None):
    """"Maximize the auto-correlation of the V vectors
    NX,NY: shape of V"""
    from numpy import array,argsort,dot,diag,sum
    from numpy.linalg import eig

    Nsvd,N = V.shape
    V = V.reshape((Nsvd,NX,NY))
    def corr(Vi,Vj):
        # 2D auto-correlation: sum of horizontal and vertical auto-correlation
        return sum(Vi[:,:-1]*Vj[:,1:])+sum(Vi[:-1,:]*Vj[1:,:])
    
    S = diag(s)
    # Calculate auto-correlation.
    N = len(V)
    C = array([corr(V[i],V[i]) for i in range(N)])
    # Sort the V vectors by auto-correlation.
    order = argsort(C)[::-1]
    C = C[order]
    V = V[order,:]
    U = U[:,order]
    s = s[order]
    S = diag(s)
    # Find the rotation matrix optimizing the auto-correlation.
    X = array([[corr(V[i],V[j]) for i in range(N)] for j in range(N)]) # eq. A.4
    Xs = (X + X.T)/2 # syymetricize cross-correlction matrix
    w,R = eig(Xs)
    # Sort eigenvectors according to eigenvalues
    order = argsort(w)[::-1] # descending order
    w = w[order] 
    R = R[:,order]
                   
    # Apply the basis rotation.
    V = V.reshape((Nsvd,NX*NY))
    USR = dot(dot(U,S),R)
    RTV = dot(R.T,V)

    if diagnostics:
        g.debug("matrix",X,"max 2D auto-correlation before")
        RTV2 = RTV.reshape((Nsvd,NX,NY))
        X = array([[corr(RTV2[i],RTV2[j]) for i in range(N)] for j in range(N)])
        g.debug("matrix",X,"max 2D auto-correlation after")

    return USR,RTV

def SVD_rotation_min_V_cross_correlation(U,s,V,diagnostics=None):
    """minimizing the cross-correlation of the V vectors"""
    from numpy import array,argsort,dot,diag,sum,einsum
    from numpy.linalg import eig

    S = diag(s)
    # Sort the V vectors by auto-correlation.
    N = len(V)
    C = array([sum(V[i]**2*V[i]**2) for i in range(N)])
    order = argsort(C)[::-1]
    C = C[order]
    V = V[order,:]
    U = U[:,order]
    s = s[order]
    S = diag(s)
    # Find the rotation matrix minimizing the cross-correlation.
    ##X = array([[sum(V[i]*V[j]) for i in range(N)] for j in range(N)])
    info("Building matrix...")
    X = einsum('ik,jk->ij',V**2,V**2) # eq. A.4
    info("Building matrix done.")
    Xs = (X + X.T)/2
    w,R = eig(Xs) #  eq. A.9
    # Sort eigenvectors according to eigenvalues
    order = argsort(w)[::-1] # descending order
    w = w[order] 
    R = R[:,order]

    # Apply the basis rotation.
    UR = dot(U,R)
    RtSV = dot(R.T,dot(S,V))

    if diagnostics:
        g.debug("matrix",X,"min cross-correlation before")
        RtV = dot(R.T,V)
        X = einsum('ik,jk->ij',RtV**2,RtV**2)
        g.debug("matrix",X,"min cross-correlation after")

    return UR,RtSV

def SVD_rotation_V_positive_base(U,s,V,(w,h),diagnostics=None):
    """Make sure Vs are positive
    w,h: image size (for diagnsostics)"""
    from numpy import diag,dot,sum,array,amax,argmax,where,argsort,einsum,\
        isnan,average
    from numpy.linalg import norm,eig

    SV = dot(diag(s),V)

    X = einsum('ik,jk->ij',SV,SV)
    g.debug("matrix",X,"positive base cross-correlation initial")

    # Construct a set of positive bases SVb
    SVb = []
    for sv in SV:
        for svb in where(sv>=0,sv,0),where(sv<=0,-sv,0): SVb += [svb]
    SVb = array(SVb)

    rank = array([norm(svb) for svb in SVb])
    order = argsort(rank)[::-1]
    rank = rank[order]
    SVb = SVb[order]
    keep = rank/max(rank) > 0.1
    SVb = SVb[keep]
    g.debug("images",SVb.reshape((SVb.shape[0],w,h)),"positive base initial")

    for i in range(0,len(SVb)):
        for j in range(0,i):
            SVb[i] -= dot(SVb[i],normalized(SVb[j]))*normalized(SVb[j])
            SVb[i] = where(SVb[i]>=0,SVb[i],0)
    g.debug("images",SVb.reshape((SVb.shape[0],w,h)),"positive base refined")
            
    rank = array([norm(svb) for svb in SVb])
    order = argsort(rank)[::-1]
    rank = rank[order]
    SVb = SVb[order]
    keep = rank/max(rank) > 0.1
    SVb = SVb[keep]
    g.debug("images",SVb.reshape((SVb.shape[0],w,h)),"positive base sorted")

    # Find the rotation matrix minimizing the cross-correlation.
    X = einsum('ik,jk->ij',SVb,SVb)
    g.debug("matrix",X,"positive base cross-correlation")
    Xs = (X + X.T)/2
    W,R = eig(Xs) #  eq. A.9
    # Sort eigenvectors according to eigenvalues
    order = argsort(W)[::-1] # descending order
    W = W[order] 
    R = R[:,order]

    # Apply the basis rotation.
    RtSVb = dot(R.T,SVb)
    X = einsum('ik,jk->ij',RtSVb,RtSVb)
    g.debug("matrix",X,"positive base cross-correlation after")
    g.debug("images",RtSVb.reshape((RtSVb.shape[0],w,h)),"positive base rotated")

def normalized(V):
    """Unit vector of V"""
    from numpy.linalg import norm
    V0 = V/norm(V)
    return V0

##    N = len(V)
##    SVb = SVb[0:N]
##    Vb0 = array([svb/norm(svb) for svb in SVb])
##    # Find the transformation matrix from SV to SVb
##    R = array([[dot(v,vb0) for v in V] for vb0 in Vb0])
##    g.debug("matrix",R,"SVD rotation positive base")

## def corr(v1,v2): return sum(v1*v2)**2/(sum(v1**2)*sum(v2**2))
## for svb in where(sv>=0,sv,0),where(sv<=0,-sv,0):
##     C = array([corr(svb,svb0) for svb0 in SVb])
##     if len(C) > 0: info("amax(C) %r" % amax(C))
##     if len(C) > 0 and amax(C) > 0.75: SVb[argmax(C)] += sv
##     else: SVb += [svb]

