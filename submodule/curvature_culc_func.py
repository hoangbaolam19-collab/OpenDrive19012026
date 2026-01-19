import math
import numpy as np
import math

o_list = [] #出力する曲率リストの宣言

def culc_curveture(x,y,posi,length):
#事前準備
#曲率計算入力用の点列の位置
    temp_x = []
    temp_y = []
#
    a = 0
    for i in range(500):
        if posi - i < 0:
            temp_x.append(x[posi-i+1])
            temp_y.append(y[posi-i+1])
            break
        a = math.sqrt((x[posi]-x[posi-i])**2 + (y[posi]-y[posi-i]) **2)
        if a > length:
            temp_x.append(x[posi-i])
            temp_y.append(y[posi-i])
            break;
#
    temp_x.append(x[posi]);
    temp_y.append(y[posi]);
#
    for i in range(500):
        if posi + i > len(x) - 1:
            temp_x.append(x[posi + i - 1])
            temp_y.append(y[posi + i - 1])
            break
        a = math.sqrt((x[posi]-x[posi+i])**2 + (y[posi]-y[posi+i]) **2)
        if a > length:
            temp_x.append(x[posi+i])
            temp_y.append(y[posi+i])
            break
#
    cx,cy,re = CircleFitting(temp_x,temp_y)
    #cx,cy,re,cv = calc_curvature_circle_fitting(temp_x, temp_y, 1)
#曲率の方向を求める、右曲がりなら正、左曲がりなら不
    arrow_1 = np.array([temp_x[1]-temp_x[0],temp_y[1]-temp_y[0]])
    arrow_2 = np.array([cx-temp_x[0],cy-temp_y[0]])
    gaiseki = np.cross(arrow_1,arrow_2)
    if gaiseki < 0:
        re = re * -1
        re = round(re,3)
        cx = round(cx,3)
        cy = round(cy,3)       
    #
    return(re,cx,cy)

def calc_curvature_circle_fitting(x, y, npo=1):
    """
    Calc curvature
    x,y: x-y position list
    npo: the number of points using Calculation curvature
    ex) npo=1: using 3 point
        npo=2: using 5 point
        npo=3: using 7 point
    """

    cv = []
    n_data = len(x)

    for i in range(n_data):
        lind = i - npo
        hind = i + npo + 1

        if lind < 0:
            lind = 0
        if hind >= n_data:
            hind = n_data

        xs = x[lind:hind]
        ys = y[lind:hind]
        (cxe, cye, re) = CircleFitting(xs, ys)

        if len(xs) >= 3:
            # sign evaluation
            c_index = int((len(xs) - 1) / 2.0)
            sign = (xs[0] - xs[c_index]) * (ys[-1] - ys[c_index]) - (
                    ys[0] - ys[c_index]) * (xs[-1] - xs[c_index])

            # check straight line
            a = np.array([xs[0] - xs[c_index], ys[0] - ys[c_index]])
            b = np.array([xs[-1] - xs[c_index], ys[-1] - ys[c_index]])
            theta = math.degrees(math.acos(
                np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))))

            if theta == 180.0:
                cv.append(0.0)  # straight line
            elif sign > 0:
                cv.append(1.0 / -re)
            else:
                cv.append(1.0 / re)
        else:
            cv.append(0.0)

    return cxe,cye,re,cv


def CircleFitting(x, y):
    """Circle Fitting with least squared
        input: point x-y positions  
        output  cxe x center position
                cye y center position
                re  radius of circle 
    """
    area = x[0] * (y[1] - y[2]) + x[1] * (y[2] - y[0]) + x[2] * (y[0] - y[1])
    if abs(area) < 0.01:
        y = [y[0], y[1], y[2] + 0.1]
        area = x[0] * (y[1] - y[2]) + x[1] * (y[2] - y[0]) + x[2] * (y[0] - y[1])
        if abs(area) < 0.01:
            x = [x[0], x[1], x[2] + 0.1]
            
    sumx = sum(x)
    sumy = sum(y)
    sumx2 = sum([ix ** 2 for ix in x])
    sumy2 = sum([iy ** 2 for iy in y])
    sumxy = sum([ix * iy for (ix, iy) in zip(x, y)])

    F = np.array([[sumx2, sumxy, sumx],
                  [sumxy, sumy2, sumy],
                  [sumx, sumy, len(x)]])

    G = np.array([[-sum([ix ** 3 + ix * iy ** 2 for (ix, iy) in zip(x, y)])],
                  [-sum([ix ** 2 * iy + iy ** 3 for (ix, iy) in zip(x, y)])],
                  [-sum([ix ** 2 + iy ** 2 for (ix, iy) in zip(x, y)])]])

    """
    try:
        T = np.linalg.inv(F).dot(G)
    except np.linalg.LinAlgError:
        return 0, 0, float("inf")
    """

    T = np.linalg.pinv(F).dot(G)

    cxe = float(T[0] / -2)
    cye = float(T[1] / -2)

    if cxe ** 2 + cye ** 2 - T[2] < 0:
        return cxe, cye, float("inf")
    try:
        re = math.sqrt(cxe ** 2 + cye ** 2 - T[2])
    except np.linalg.LinAlgError:
        return cxe, cye, float("inf")
    return cxe, cye, re