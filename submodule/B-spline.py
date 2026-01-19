import numpy as np
from scipy import interpolate

# B-Spline 補間
S = 1

#三次元のB-スプライン曲線
def B_spline(x, y ,z):
    n = len(x)
    t=np.linspace(0,1,n-2,endpoint=True)
    t=np.append([0,0,0],t)
    t=np.append(t,[1,1,1])
    tck2=[t,[x,y,z],3]
    u3=np.linspace(0,1,n*S,endpoint=True)
    out = interpolate.splev(u3,tck2)
    return out

