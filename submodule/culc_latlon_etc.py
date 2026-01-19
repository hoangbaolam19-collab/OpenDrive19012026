#計算のためのライブラリを読み込み
import math

#lat0,lon0→lat1,lon1の方位角
def latlon_dir(lat0,lon0,lat1,lon1):
#
    PI = math.pi                        #π
    Rx = 6378137                        #赤道半径(m)
    E2 = 6.69437999019758E-03           #第2離心率(e^2)
#
    di = lat1 - lat0
    dk = lon1 - lon0
    i = (lat0 + lat1) / 2
#
    w = math.sqrt(1 - E2 * math.sin(i * PI / 180) ** 2)
    m = Rx * (1 - E2) / w ** 3
    n = Rx / w
#
    ddi = di * PI / 180 * m
    ddk = dk * PI / 180 * n * math.cos(i * PI / 180)
#
    dir = (math.atan2(ddk,ddi) * 180 / PI + 360)
    if dir >= 360:
        dir = dir - 360
    return(dir)
#
#
#
#lat0,lon0→lat1,lon1の距離

def latlon_dist(lat0,lon0,lat1,lon1):
#
    PI = math.pi			#π
    Rx = 6378137			#赤道半径(m)
    E2 = 6.69437999019758E-03	#第2離心率(e^2)
#
    di = lat1 - lat0
    dk = lon1 - lon0
    i = (lat0 + lat1) / 2
#
    w = math.sqrt(1 - E2 * math.sin(i * PI / 180) ** 2)
    m = Rx * (1 - E2) / w ** 3
    n = Rx / w
#
    Dist = math.sqrt((di * PI / 180 * m) ** 2 + (dk * PI / 180 * n * math.cos(i * PI / 180)) ** 2)
#
    return(Dist)
