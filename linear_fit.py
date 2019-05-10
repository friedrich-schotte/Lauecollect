"""
Linear least-squares fit.
Following the procedure oulined in Philip R. Bevington, "Data Reduction and
Error Analysis for the Physical Sciences" (Third Edition, 2003),
Chapter 7.2, "Least Squares Fit to a Polynomial - Matrix Solution"

Friedrich Schotte, 20 May 2008 - 27 Apr 2012
"""

__version__ = "1.3.3"

def linear_fit(y,X):
    """Find the optimal solution to the equation y = a*X
    (Minimize the sum of the squares of the elements of y - a*X).
    Return a*X.
    y is usually used to pass experimental data.
    X is used to pass the fit model. It can be a a set of base functions,
    evaluated at the point for which the experimental data y is available.
    X has to be a matrix, y and a can be both vectors or both matrices.
    """
    from numpy import dot,nan

    # Handle degenerate case by returning NaN rather than throwing an exception.
    if X.shape[0] == 0: return y+nan
    
    a = linear_fit_coeff(y,X)
    fit = dot(a,X)
    return fit

def linear_fit_coeff(y,X):
    """Find the optimal solution to the equation y = a*X
    (Minimize the sum of the squares of the elements of y - a*X).
    Return a.
    y is usually used to pass experimental data.
    X is used to pass the fit model. It can be a a set of base functions,
    evaluated at the point for which the experimental data y is available.
    X has to be a matrix.
    If y is a vector, the returned coefficients a are a vector.
    If y is a matrix, the returned coefficients a are a matrix, too.
    """
    from numpy import nan,dot
    from numpy.linalg import inv

    alpha = dot(X,X.T)
    beta = dot(X,y.T)
    try: epsilon = inv(alpha)
    except: epsilon = alpha*nan
    a = dot(epsilon,beta)
    return a.T

def weighted_linear_fit(y,w,X):
    """Find the optimal solution to the equation y = a*X
    (Minimize the sum of the squares of the elements of y - a*X).
    Return a*X.
    y is usually used to pass experimental data.
    w is the weight for each element of y (recommended: 1/sigma**2)
    X is used to pass the fit model. It can be a a set of base functions,
    evaluated at the point for which the experimental data y is available.
    X has to be a matrix, y and a can be both vectors or both matrices.
    """
    from numpy import dot,nan
    
    # Handle degenerate case by returning NaN rather than throwing an exception.
    if X.shape[0] == 0: return y+nan
    
    a = weighted_linear_fit_coeff(y,w,X)
    fit = dot(a,X)
    return fit

def weighted_linear_fit_coeff(y,w,X):
    """Find the optimal solution to the equation y = a*X
    (Minimize the sum of the squares of the elements of y - a*X).
    Return a.
    y is usually used to pass experimental data.
    w is the weight for each element of y (recommended: 1/sigma**2)
    X is used to pass the fit model. It can be a a set of base functions,
    evaluated at the point for which the experimental data y is available.
    X has to be a matrix.
    If y and sigma is are vectors, the returned coefficients a are a vector.
    If y and sigma is are matrices, the returned coefficients a are a matrix.
    """
    from numpy import where,isnan,nan,dot,array
    from numpy.linalg import inv

    # 'y's that are NaNs should have zero weight.
    w = where(isnan(y),0,w)
    y = where(isnan(y),0,y)
    # Ignore NaNs in 'y' if weight is zero.
    y = where((w==0) & isnan(y),0,y)

    if y.ndim == 1:
        alpha = dot(w * X,X.T)
        beta = dot(X,(w * y).T)
        try: epsilon = inv(alpha)
        except: epsilon = alpha*nan
        a = dot(epsilon,beta)
        return a.T
    else:
        return array([weighted_linear_fit_coeff(y[i],w[i],X)
            for i in range(0,len(y))])

if __name__ == "__main__": # Example for testing
    from time import clock
    from numpy import *

    N = 5
    x = arange(0.0,2.001*pi,2*pi/(N-1))
    y1 = 1 + 0.1*sin(x) + 0.01*cos(2*x)
    y2 = 2 + 0.2*sin(x) + 0.02*cos(2*x)
    y = array([y1,y2])
    sigma = sqrt(y)

    # Basis vectors
    X0 = 1 + 0*x
    X1 = sin(x)
    X2 = cos(2*x)
    X = array([X0,X1,X2])

    ##fit = linear_fit(y,X)
    fit = weighted_linear_fit(y,1/sigma**2,X)
    print "expecting:",y[:5]
    print "result:",fit[:5]
    print "fit residual RMS",std(y-fit)
    ##a = linear_fit_coeff(y,X)
    a = weighted_linear_fit_coeff(y,1/sigma**2,X)
    print "fit residual RMS",std(y - matrix(a)*matrix(X))
