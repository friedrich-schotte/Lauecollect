from math import sqrt

phi = (sqrt(5)+1)/2
div = 0.65

def series(n):
  x = [0.,1.]
  for i in range(3,n+1): insert1(x)
  return x
  
def insert1(x):
  n = len(x)
  x.sort()
  dx = [x[i+1]-x[i] for i in range(0,n-1)]
  i = dx.index(max(dx))
  gap = x[i+1]-x[i]
  x.insert(i+1,x[i]+gap*div)

def max_ratio(x):
  n = len(x)
  x.sort()
  dx = [x[i+1]-x[i] for i in range(0,n-1)]
  dx.sort()
  return dx[n-2]/dx[0]

print [max_ratio(series(i)) for i in range(3,11)]
