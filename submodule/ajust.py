import pandas as pd
import numpy as np
import math
from scipy import interpolate
from scipy import optimize
from scipy import signal
from submodule import ajust
import matplotlib.pyplot as plt

from submodule import parameter as PARAM
from submodule import curvature_culc_func as ccf

#リストと間引き間隔を入れると、マッチング用の点列を出してくれる関数
def input_match(xyzdist_ls,span): #対象緯度経度点列リストと、間引き間隔を指定
    export_list = [] #最終的に出力するリスト
    dist_sum = 0
    temp_list = [xyzdist_ls[0]] #1リクエスト用に100点ごとに区切ったリスト,最初に初期点が入る
    for i in range(1,len(xyzdist_ls)-1):
        temp_dist = xyzdist_ls[i][3]
        dist_sum= dist_sum + temp_dist
        if dist_sum > span:
            temp_list += [xyzdist_ls[i-1]]
            dist_sum = temp_dist
    temp_list += [xyzdist_ls[len(xyzdist_ls)-1]]
    
    return(temp_list)

def interpolate_to_5(points,n):
    x = np.linspace(0, 1, len(points))
    y = np.array(points)

    new_x = np.linspace(0, 1, n)
    new_y = np.interp(new_x, x, y)

    return new_y.tolist()


#三次元のB-スプライン曲線
def B_spline(x, y ,z):
    # B-Spline 補間
    n = len(x)
    dist_all = 0
    for i in range(1,n):
        dist = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2 + (z[i]-z[i-1])**2)
        dist_all += dist
    dist_int = int(dist_all/2)
    t=np.linspace(0,1,n-2,endpoint=True)
    t=np.append([0,0,0],t)
    t=np.append(t,[1,1,1])
    tck2=[t,[x,y,z],3]
    u3=np.arange(0,int(dist_all),PARAM.POINT_GENERATION_INTERVAL)/dist_all
    #u3=np.linspace(0,1,n,endpoint=True)
    out = interpolate.splev(u3,tck2)
    return out

def B_spline2(x, y ,z):
    # B-Spline 補間
    S = 1

    n = len(x)
    dist_all = 0
    for i in range(1,n):
        dist = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2 + (z[i]-z[i-1])**2)
        dist_all += dist
    dist_int = int(dist_all)
    t=np.linspace(0,1,n-2,endpoint=True)
    t=np.append([0,0,0],t)
    t=np.append(t,[1,1,1])
    tck2=[t,[x,y,z],3]
    u3=np.linspace(0,1,n*S,endpoint=True)
    out = interpolate.splev(u3,tck2)
    return out


def func_residual(param,s,dist):
    residual =  s-(param[0]*dist**5 + param[1]*dist**4 + param[2]*dist**3 + param[3]*dist**2 + param[4]*dist +param[5])
    return residual

def func_residual_3D(param,s,dist):
    residual =  s-(param[0] + param[1]*dist + param[2]*dist**2 + param[3]*dist**3)
    return residual

def func_temp(param,dist):
    s = param[0]*dist**5 + param[1]*dist**4 + param[2]*dist**3 + param[3]*dist**2 + param[4]*dist +param[5]
    return s

#使っていない
def fitting_xyz(x,y,z):
    s_list = [x,y,z]
    
    n = len(x)
    param_x = [0,0,0,0,0,0]
    param_y = [0,0,0,0,0,0]
    param_z = [0,0,0,0,0,0]
    params = [param_x,param_y,param_z]

    dist = [0]
    for i in range(1,n):
        dist_one = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2 + (z[i]-z[i-1])**2)
        dist += [dist_one+dist[i-1]]

    dist_temp = np.arange(0,dist[-1],1)

    result = []
    for i in range(3):
        optimized_param = optimize.leastsq(func_residual,(params[i]),args=(np.array(s_list[i]),np.array(dist)))
        result_one=[]
        for j in range(len(dist_temp)):
            result_one += [func_temp(optimized_param[0],dist_temp[j])]
        result += [result_one]

    return result

#標高のフィッティング
def fitting_z(x,y,z):

    n = len(z)
    param_z = [0,0,0,0,0,0]

    dist = [0]
    for i in range(1,n):
        dist_one = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2 + (z[i]-z[i-1])**2)
        dist += [dist_one+dist[i-1]]

    #dist_temp = np.arange(0,dist[-1],1)

    result = []
    print(z[i])
    optimized_param = optimize.leastsq(func_residual,(param_z),args=(np.array(z),np.array(dist)))
    result_one=[]
    for j in range(len(dist)):
        result_one += [func_temp(optimized_param[0],dist[j])]
    result += [result_one]

    return result

#標高の三次多項式近似のパラメータを求める
def fitting_3D_elev(x,y,z,s_position):

    n = len(z)
    param_z = [0,0,0,0]

    dist = [0]

    for i in range(1,n):
        dist_one = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2)
        dist += [dist_one+dist[i-1]]

    dist = [x - dist[s_position] for x in dist]

    optimized_param = optimize.leastsq(func_residual_3D,(param_z),args=(np.array(z),np.array(dist)))

    if s_position < 3:
        param_s = dist[s_position + 1]
    else:
        param_s = 0

    return optimized_param[0], param_s

###合流境界線の標高フィッティング##############################################################################################    
def func_border_residual(param,s,dist):
    n = len(s)
    if n > 5:
        residual =  s-(param[0]*dist**5 + param[1]*dist**4 + param[2]*dist**3 + param[3]*dist**2 + param[4]*dist +param[5])
    elif n== 5:
        residual =  s-(param[0]*dist**4 + param[1]*dist**3 + param[2]*dist**2 + param[3]*dist +param[4])
    elif n == 4:
        residual =  s-(param[0]*dist**3 + param[1]*dist**2 + param[2]*dist +param[3])
    elif n ==3:
        residual =  s-(param[0]*dist**2 + param[1]*dist +param[2])
    elif n ==2:
        residual =  s-(param[0]*dist +param[1])
    return residual

def func_border_temp(param,dist):
    n = len(param)
    if n > 5:
        s = param[0]*dist**5 + param[1]*dist**4 + param[2]*dist**3 + param[3]*dist**2 + param[4]*dist +param[5]
    elif n == 5:
        s = param[0]*dist**4 + param[1]*dist**3 + param[2]*dist**2 + param[3]*dist +param[4]
    elif n == 4:
        s = param[0]*dist**3 + param[1]*dist**2 + param[2]*dist +param[3]
    elif n ==3:
        s = param[0]*dist**2 + param[1]*dist +param[2]
    elif n ==2:
        s = param[0]*dist +param[1]
    return s

def fitting_border(x,y):
    s_list = [x,y]
    n = len(x)

    #元データの点数によって、近似の次数を変える。6点以上は5次近似、3点以上は2次近似、2点は直線補完を行う。
    if n>5:
        param_x = [0,0,0,0,0,0]
        param_y = [0,0,0,0,0,0]
    elif n==5:
        param_x = [0,0,0,0,0]
        param_y = [0,0,0,0,0]
    elif n==4:
        param_x = [0,0,0,0]
        param_y = [0,0,0,0]
    elif n==3:
        param_x = [0,0,0]
        param_y = [0,0,0]
    else:
        param_x = [0,0]
        param_y = [0,0]
    params = [param_x,param_y]

    dist = [0]
    for i in range(1,n):
        dist_one = math.sqrt((x[i] - x[i-1])**2 + (y[i]-y[i-1])**2)
        dist += [dist_one+dist[i-1]]
    dist_temp = np.arange(0,dist[-1],1)

    result = []
    for i in range(2):
        optimized_param = optimize.leastsq(func_border_residual,(params[i]),args=(np.array(s_list[i]),np.array(dist)))
        result_one=[]
        for j in range(len(dist_temp)):
            result_one += [func_border_temp(optimized_param[0],dist_temp[j])]
        result += [result_one]

    return result


def smooth_xyz(x,y,z):
    s_list = [x,y,z]
    #フィルター処理開始
    window=len(x)
    deg=3
    print(x)
    smooth_x=signal.savgol_filter(x, window, deg)
    smooth_y = signal.savgol_filter(y, window, deg)
    smooth_z = signal.savgol_filter(z, window, deg)
    result = [smooth_x, smooth_y, smooth_z]

    return result

#曲率計算のための円フィッティング
def func_circle_residual(param, x, y):
    residual = x**2 + y**2 + param[0]*x + param[1]*y + param[2]
    return residual

def fitting_circle(x,y):
    param = [0, 0, 0]
    
    r_list = []
    #評価関数は(x-a)**2 + (y-b)**2 -r**2 →　x**2 + y**2 + αx + βy + γ　(α=-2a, β=-2b, γ=a**2 + b**2 - r**2)として、
    #optimized_paramには[α、β、γ]が返ってくる
    optimized_param = optimize.leastsq(func_circle_residual,(param),args=(np.array(x),np.array(y)))
    a = -optimized_param[0][0]/2
    b = -optimized_param[0][1]/2
    r = math.sqrt(abs(a**2 + b**2 - optimized_param[0][2]))

    rab = [r, a, b]

    return r



def make_combine_road_data(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset):

    # raise ValueError("This is a special case")
    # plt.plot(x_curve1, y_curve1, linestyle="--", color="yellow")
    # plt.plot(x_curve2, y_curve2, linestyle="--", color="yellow")

    if round(x_curve1[-1],3) == round(x_curve2[0],3) and round(y_curve1[-1],3) == round(y_curve2[0],3):

        print("This case does not require editing.")

    else:

        x_middle = (start_point[0] + end_point[0]) / 2
        y_middle = (start_point[1] + end_point[1]) / 2

        middle = (x_middle, y_middle)

        # plt.plot(x_middle,y_middle,marker='o',color='red')

        dist_list_1 = []
        for i in range(len(x_curve1)):
            dist_list_1.append(
                (x_curve1[i] - middle[0]) ** 2
                + (y_curve1[i] - middle[1]) ** 2
            )
        min_id_1 = dist_list_1.index(min(dist_list_1))

        if min_id_1 == 0:
            raise ValueError(1)
        
        for i in range(len(x_curve1) - min_id_1):
            x_curve1.pop(-1)
            y_curve1.pop(-1)
        # plt.plot(x_curve1,y_curve1,linestyle='--',color='blue')

        dist_list_2 = []
        for i in range(len(x_curve2)):
            dist_list_2.append(
                (x_curve2[i] - x_curve1[-1]) ** 2
                + (y_curve2[i] - y_curve1[-1]) ** 2
            )
        min_id_2 = dist_list_2.index(min(dist_list_2))
        for i in range(min_id_2):
            x_curve2.pop(0)
            y_curve2.pop(0)
        # plt.plot(x_curve2,y_curve2,linestyle='--',color='blue')

        if min_id_1 == len(x_curve1) - 1 or min_id_2 == 0 or len(x_curve1) < 20 or len(x_curve2) < 20:
            raise ValueError("This is a special case")
        

        # x_curve11 = x_curve1.copy()
        # y_curve11 = y_curve1.copy()
        # x_curve22 = x_curve2.copy()
        # y_curve22 = y_curve2.copy()

        middle = ((x_curve2[0] + x_curve1[-1]) / 2, (y_curve2[0] + y_curve1[-1]) / 2)

        # dist_x = (x_curve2[0] - x_curve1[-1]) / 2
        # dist_y = (y_curve2[0] - y_curve1[-1]) / 2

        # for i in range(len(y_curve1)):
        #     x_curve1[i] = x_curve1[i] + (dist_x / (len(x_curve1) - 1)) * i
        #     y_curve1[i] = y_curve1[i] + (dist_y / (len(y_curve1) - 1)) * i
        # for i in range(len(y_curve2)):
        #     x_curve2[i] = x_curve2[i] - (dist_x / (len(x_curve2) - 1)) * (
        #         len(x_curve2) - 1 - i
        #     )
        #     y_curve2[i] = y_curve2[i] - (dist_y / (len(y_curve2) - 1)) * (
        #         len(y_curve2) - 1 - i
        #     )

        # x_curve11, y_curve11 = ajust.rotate_polyline(middle, (x_curve11, y_curve11), True)
        # x_curve22, y_curve22 = ajust.rotate_polyline(middle, (x_curve22, y_curve22), False)

        x_curve1, y_curve1 = ajust.rotate_polyline(middle, (x_curve1, y_curve1), True)
        x_curve2, y_curve2 = ajust.rotate_polyline(middle, (x_curve2, y_curve2), False)


        # plt.plot(x_curve1, y_curve1, linestyle="--", color="blue")
        # plt.plot(x_curve2, y_curve2, linestyle="--", color="red")

        # plt.plot(x_curve11, y_curve11, linestyle="-.", color="green")
        # plt.plot(x_curve22, y_curve22, linestyle="-.", color="pink")

    # x_curve1, y_curve1,x_curve2, y_curve2 = ajust.make_adjust_road_caused_offset(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

    return x_curve1, y_curve1, x_curve2, y_curve2

def make_new_combine_road_data(start_point, end_point, offset):

    distant = math.sqrt((end_point[0] - start_point[0])** 2 + (end_point[1] - start_point[1])** 2)
    total_point = int(distant)

    if total_point < 10:
        total_point = total_point * 2

    point_list = []
    point_list_x = []
    point_list_y = []
    point_list_z = []

    step_x = (end_point[0] - start_point[0])/(total_point-1)
    step_y = (end_point[1] - start_point[1])/(total_point-1)
    step_z = (end_point[2] - start_point[2])/(total_point-1)

    for i in range(total_point):
        x = start_point[0] + i*step_x
        y = start_point[1] + i*step_y
        z = start_point[2] + i*step_z
        point_list.append([x,y,z])
        point_list_x.append(x)
        point_list_y.append(y)
        point_list_z.append(z)

    curve = []
    # OpenDrive化時に用いる、z方向の三次多項式近似のパラメータを求める
    for j in range(len(point_list)):
        dic_latlonelev = {
            "x": 0,
            "y": 0,
            "elevation": 0,
            "elev_param": {"s": 0, "a": 0, "b": 0, "c": 0, "d": 0},
        }
        if j > 0 and len(point_list) - 2 > j:
            x_ls = point_list_x[j - 1 : j + 3]
            y_ls = point_list_y[j - 1 : j + 3]
            z_ls = point_list_z[j - 1 : j + 3]
            s_position = 1
        elif j == 0:
            x_ls = point_list_x[j : j + 4]
            y_ls = point_list_y[j : j + 4]
            z_ls = point_list_z[j : j + 4]
            s_position = 0
        elif j == len(point_list) - 2:
            x_ls = point_list_x[-4:]
            y_ls = point_list_y[-4:]
            z_ls = point_list_z[-4:]
            s_position = 2
        elif j == len(point_list) - 1:
            x_ls = point_list_x[-4:]
            y_ls = point_list_y[-4:]
            z_ls = point_list_z[-4:]
            s_position = 3

        if len(x_ls) > 3:
            (
                optimized_elev_param,
                optimized_elev_param_s,
            ) = ajust.fitting_3D_elev(x_ls, y_ls, z_ls, s_position)

            dic_latlonelev["elev_param"]["s"] = optimized_elev_param_s
            dic_latlonelev["elev_param"]["a"] = optimized_elev_param[0]
            dic_latlonelev["elev_param"]["b"] = optimized_elev_param[1]
            dic_latlonelev["elev_param"]["c"] = optimized_elev_param[2]
            dic_latlonelev["elev_param"]["d"] = optimized_elev_param[3]

        else:
            dic_latlonelev["elev_param"]["s"] = 1
            dic_latlonelev["elev_param"]["a"] = point_list_z[j]
            dic_latlonelev["elev_param"]["b"] = 0
            dic_latlonelev["elev_param"]["c"] = 0
            dic_latlonelev["elev_param"]["d"] = 0

        dic_latlonelev["x"] = point_list[j][0]
        dic_latlonelev["y"] = point_list[j][1]
        dic_latlonelev["elevation"] = point_list[j][2]

        curve += [dic_latlonelev]

    x_curve1 = []
    y_curve1 = []
    z_curve1 = []
    z_param_curve1 = []
    x_curve2 = []
    y_curve2 = []
    z_curve2 = []
    z_param_curve2 = []

    for i in range(len(curve)):
        x_center = curve[i]["x"]
        y_center = curve[i]["y"]
        z_center = curve[i]["elevation"]
        z_param_center = curve[i]["elev_param"]

        if i < int(len(point_list)/2):
            x_curve1.append(x_center)
            y_curve1.append(y_center)
            z_curve1.append(z_center)
            z_param_curve1.append(z_param_center)
        else:
            x_curve2.append(x_center)
            y_curve2.append(y_center)
            z_curve2.append(z_center)
            z_param_curve2.append(z_param_center)


    x_curve1.append(x_curve2[0])
    y_curve1.append(y_curve2[0])
    z_curve1.append(z_curve2[0])
    z_param_curve1.append(z_param_curve2[0])

    # plt.plot(x_curve1,y_curve1,linestyle='--',color='blue')
    # plt.plot(x_curve2,y_curve2,linestyle='--',color='red')

    # x_curve1, y_curve1,x_curve2, y_curve2 = ajust.make_adjust_road_caused_offset(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset)

    return x_curve1, y_curve1, z_curve1, z_param_curve1, x_curve2, y_curve2, z_curve2, z_param_curve2



def make_adjust_road_caused_offset(x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset):

    # region Adjust the road data to correct deviations caused by the offset value

    # plt.plot(x_curve1, y_curve1, linestyle="--", color="blue")
    # plt.plot(x_curve2, y_curve2, linestyle="--", color="red")

    distant = math.sqrt((end_point[0] - start_point[0])** 2 + (end_point[1] - start_point[1])** 2)
      
    tan_value1 = ((end_point[0] - start_point[0])/ (end_point[1] - start_point[1]))
    angle_value1 = math.atan(tan_value1)

    sin_value2 = (offset)/distant
    angle_value2 = math.asin(sin_value2)

    #   offset < 0 

    if (end_point[0]-start_point[0]) > 0 and (end_point[1]-start_point[1]) > 0 and offset < 0: #OK
        angle_value = angle_value1 - angle_value2
        dist_x = ((offset)  * math.cos(angle_value)) / 2 
        dist_y = ((offset)  * math.sin(angle_value)) / 2  

    elif (end_point[0]-start_point[0]) > 0 and (end_point[1]-start_point[1]) < 0 and offset < 0: #OK
        angle_value = angle_value1 - angle_value2 
        dist_x = ((offset)  * math.cos(angle_value)) / 2
        dist_y = - ((offset)  * math.sin(angle_value)) / 2 

    elif (end_point[0]-start_point[0]) < 0 and (end_point[1]-start_point[1]) < 0 and offset < 0:
        print("Adjust the sign of the dist_x and dist_y values if this case is incorrect.")
        print("offset, end_point[0]-start_point[0], end_point[1]-start_point[1] ",offset, (end_point[0]-start_point[0]),(end_point[1]-start_point[1]))
        angle_value = angle_value1 - angle_value2 
        dist_x = - ((offset)  * math.cos(angle_value)) / 2
        dist_y = - ((offset)  * math.sin(angle_value)) / 2

    elif (end_point[0]-start_point[0]) < 0 and (end_point[1]-start_point[1]) > 0 and offset < 0: #OK
        angle_value = angle_value1 - angle_value2
        dist_x = - ((offset)  * math.cos(angle_value)) / 2
        dist_y = ((offset)  * math.sin(angle_value)) / 2    

    #   offset > 0 

    elif (end_point[0]-start_point[0]) > 0 and (end_point[1]-start_point[1]) > 0 and offset > 0: #OK
        angle_value = math.pi - angle_value1 - angle_value2
        dist_x = ((offset)  * math.cos(angle_value)) / 2
        dist_y = - ((offset)  * math.sin(angle_value)) / 2

    elif (end_point[0]-start_point[0]) > 0 and (end_point[1]-start_point[1]) < 0 and offset > 0: #OK
        angle_value = math.pi - angle_value1 - angle_value2
        dist_x = - ((offset)  * math.cos(angle_value)) / 2
        dist_y = - ((offset)  * math.sin(angle_value)) / 2 

    elif (end_point[0]-start_point[0]) < 0 and (end_point[1]-start_point[1]) < 0 and offset > 0: #OK
        angle_value = math.pi - angle_value1 - angle_value2
        dist_x = - ((offset)  * math.cos(angle_value)) / 2 #-
        dist_y = ((offset)  * math.sin(angle_value)) / 2

    elif (end_point[0]-start_point[0]) < 0 and (end_point[1]-start_point[1]) > 0 and offset > 0: #OK
        angle_value = math.pi - angle_value1 - angle_value2
        dist_x = ((offset)  * math.cos(angle_value)) / 2
        dist_y = ((offset)  * math.sin(angle_value)) / 2 #+


    # if offset != 0:
    #     # print("end_point[0]-start_point[0], end_point[1]-start_point[1]  ",(end_point[0]-start_point[0]),(end_point[1]-start_point[1]) )
    #     # print("tan_value1,angle_value1  ",tan_value1,angle_value1)
    #     # print("offset, sin_value2,angle_value2  ",offset, sin_value2, angle_value2)
    #     # print("angle_value,dist_x,dist_y  ",angle_value,dist_x,dist_y)

    #     for i in range(len(y_curve1)):
    #         x_curve1[i] = x_curve1[i] + (dist_x / (len(x_curve1) - 1)) * i
    #         y_curve1[i] = y_curve1[i] + (dist_y / (len(y_curve1) - 1)) * i
    #     for i in range(len(y_curve2)):
    #         x_curve2[i] = x_curve2[i] - (dist_x / (len(x_curve2) - 1)) * (len(x_curve2) - 1 - i)
    #         y_curve2[i] = y_curve2[i] - (dist_y / (len(y_curve2) - 1)) * (len(y_curve2) - 1 - i)
    # # else:
    # #     print("offset == 000000000000000000000000000")

    # # endregion

    # # plt.plot(x_curve1, y_curve1, marker='o', color="blue")
    # # plt.plot(x_curve2, y_curve2, marker='o', color="red")

    # A = (x_curve1[-2], y_curve1[-2])
    # B = (x_curve1[-1], y_curve1[-1])

    # D = (x_curve2[0], y_curve2[0])

    # # plt.plot([A[0],B[0]],[A[1],B[1]],marker='o',color='green')
    # # plt.plot(D[0],D[1],marker='o',color='green')

    # C = ajust.find_point_c(A, B, offset, D)

    # # dist_x = C[0] - x_curve2[0] 
    # # dist_y = C[1] - y_curve2[0] 

    # # for i in range(len(x_curve2)):
    # #     x_curve2[i] = x_curve2[i] + (dist_x / (len(x_curve2) - 1)) * (len(x_curve2) - 1 - i)
    # #     y_curve2[i] = y_curve2[i] + (dist_y / (len(y_curve2) - 1)) * (len(y_curve2) - 1 - i)

    # x_curve2, y_curve2 = ajust.rotate_polyline((C[0], C[1]), (x_curve2, y_curve2), False)


    # # plt.plot(x_curve2, y_curve2, marker='o', color="blue")



    return x_curve1, y_curve1, x_curve2, y_curve2

def find_point_c(A, B, offset, D):
    # Calculate the slope of AB
    slope_AB = (B[1] - A[1]) / (B[0] - A[0]) if B[0] != A[0] else None

    # The slope of BC (perpendicular to AB) is the negative reciprocal of the slope of AB
    if slope_AB is not None:
        slope_BC = -1 / slope_AB
    else:
        slope_BC = 0

    # Calculate the angle of BC with respect to the x-axis
    angle_BC = math.atan(slope_BC)

    # Calculate the coordinates of C
    C_x_1 = B[0] - offset * math.cos(angle_BC)
    C_y_1 = B[1] - offset * math.sin(angle_BC) 

    C_x_2 = B[0] + offset * math.cos(angle_BC)
    C_y_2 = B[1] + offset * math.sin(angle_BC)  

    dist_1 = math.sqrt((C_x_1 - D[0])** 2 + (C_y_1 - D[1])** 2)
    dist_2 = math.sqrt((C_x_2 - D[0])** 2 + (C_y_2 - D[1])** 2)

    if dist_1 < dist_2:
        C_x = C_x_1
        C_y = C_y_1
    else:
        C_x = C_x_2
        C_y = C_y_2

    return (C_x, C_y)



def make_adjust_road_caused_offset__(
    x_curve1, y_curve1, x_curve2, y_curve2, start_point, end_point, offset
):
    
    if offset != 0:
        
        B = (x_curve2[0],y_curve2[0])
        
        distant1 = (math.sqrt((x_curve1[-2] - x_curve1[-1]) ** 2 + (y_curve1[-2] - y_curve1[-1]) ** 2))*(len(x_curve1)-1)
        distant2 = (math.sqrt((x_curve2[0] - x_curve2[1]) ** 2 + (y_curve2[0] - y_curve2[1]) ** 2))*(len(x_curve2)-1)

        # plt.plot(x_curve1, y_curve1, linestyle="--", color="blue")
        # plt.plot(x_curve2, y_curve2, linestyle="--", color="red")

        k = (y_curve2[1] - y_curve1[-2])/(x_curve2[1] - x_curve1[-2])
        
        x_A = x_curve1[-2]
        y_A = y_curve1[-2]
        x = np.linspace(x_A-200,x_A+200, 100)
        y = k * (x - x_A) + y_A
        # plt.plot(x, y, color='green')
        # plt.plot(x_curve1[-2],y_curve1[-2],marker='o',color='yellow')
        # plt.plot(x_curve2[1],y_curve2[1],marker='o',color='black')


        a = 1
        b = -2*B[0]
        c = B[0]**2 - distant1**2/(1+k**2)
        try:        
            solutions = ajust.solve_quadratic(a, b, c)
            
            if len(solutions) == 2:
                # print(f"The solutions are: A_x1 = {solutions[0]}, A_x2 = {solutions[1]}")
                A_x1 = solutions[0]
                A_y1 = k*A_x1 - k*x_curve1[-2] +  y_curve1[-2]

                A_x2 = solutions[1]
                A_y2 = k*A_x2 - k*x_curve1[-2] +  y_curve1[-2]

            else:
                print("ERROR in here")
        
        except ValueError as ve:
            print(ve)

        dist_1 = math.sqrt((A_x1 - x_curve1[0]) ** 2 + (A_y1 - y_curve1[0]) ** 2)
        dist_2 = math.sqrt((A_x2 - x_curve1[0]) ** 2 + (A_y2 - y_curve1[0]) ** 2)
        if dist_1 < dist_2:
            A_x = A_x1
            A_y = A_y1
        else:
            A_x = A_x2
            A_y = A_y2
        A = (A_x, A_y)

        # plt.plot(A_x1, A_y1,marker='o',color='yellow')
        # plt.plot(A_x2, A_y2,marker='o',color='black')

        a = 1 
        b = -2*B[0]
        c = B[0]**2 - distant2**2/(1+k**2)
        try:        
            solutions = ajust.solve_quadratic(a, b, c)
            
            if len(solutions) == 2:
                # print(f"The solutions are: C_x1 = {solutions[0]}, C_x2 = {solutions[1]}")
                C_x1 = solutions[0]
                C_y1 = k*C_x1 - k*x_curve1[-2] +  y_curve1[-2]

                C_x2 = solutions[1]
                C_y2 = k*C_x2 - k*x_curve1[-2] +  y_curve1[-2]

            else:
                print("ERROR in here")
        
        except ValueError as ve:
            print(ve)


        dist_1 = math.sqrt((C_x1 - x_curve2[-1]) ** 2 + (C_y1 - y_curve2[-1]) ** 2)
        dist_2 = math.sqrt((C_x2 - x_curve2[-1]) ** 2 + (C_y2 - y_curve2[-1]) ** 2)
        if dist_1 < dist_2:
            C_x = C_x1
            C_y = C_y1
        else:
            C_x = C_x2
            C_y = C_y2
        C = (C_x, C_y)



        R = abs(offset)

        # plt.plot([A[0], B[0]], [A[1], B[1]], marker='o') 
        # plt.plot([A[0], C[0]], [A[1], C[1]], marker='s') 
        # plt.plot(A[0],A[1],marker='o',color='yellow', label='A')
        # plt.plot(B[0],B[1],marker='o',color='black', label='B')
        # plt.plot(C[0],C[1],marker='o',color='red', label='C')



        x, y = C
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = x + R * np.cos(theta)
        y_circle = y + R * np.sin(theta)
        # plt.plot(x_circle, y_circle)


        m = C[0] - A[0]
        n = C[1] - A[1]
        a = R**2 - m**2
        b = 2*m*n
        c = R**2 - n**2
        try:        
            solutions = ajust.solve_quadratic(a, b, c)
            
            if len(solutions) == 2:
                # print(f"The solutions are: k1 = {solutions[0]}, k2 = {solutions[1]}")
                k1 = solutions[0]
                k2 = solutions[1]

            else:
                print("ERROR in here")
        
        except ValueError as ve:
            print(ve)

        x_A, y_A = A
        x = np.linspace(x_A-10,x_A+200, 100)
        y = k1 * (x - x_A) + y_A
        # plt.plot(x, y, color='blue')


        x_C, y_C = C
        x = np.linspace(x_C-100,x_C+20, 100)
        y = k1 * (x - x_C) + y_C
        # plt.plot(x, y, color='green')


        x_B, y_B = B
        x = np.linspace(x_B-2,x_B+2, 10)
        y = (-1/k1) * (x - x_B) + y_B
        # plt.plot(x, y, color='red')

        B_list = []


        dxx = B[0] - A[0]
        dyy = B[1] - A[1]

        a = math.sqrt(dxx ** 2 + dyy ** 2)/0.5

        B_new_x = A[0] + dxx*(a-1)/a
        B_new_y = A[1] + dyy*(a-1)/a

        for i in range(len(solutions)):

            k = solutions[i]

            a1 = k
            b1 = -1
            c1 = k*A[0] - A[1]

            d1 = k*C[0] - C[1]

            a2 = 1/k
            b2 = 1
            c2 = B[0]/k + B[1]

            d2 = B[0]/k + B[1]
            # d2 = B_new_x/k + B_new_y

            B1_x = -(b1*c2 - b2*c1) / (a1*b2 - a2*b1)
            B1_y = -(a1*c2 - a2*c1) / (a2*b1 - a1*b2)
            B1 = (B1_x,B1_y)

            B_list += [B1]

            B2_x = -(b1*d2 - b2*d1) / (a1*b2 - a2*b1)
            B2_y = -(a1*d2 - a2*d1) / (a2*b1 - a1*b2)
            B2 = (B2_x,B2_y)

            B_list += [B2]


        A = np.array([A[0],A[1]])
        B = np.array([B[0],B[1]])
        B1 = np.array([B_list[0][0],B_list[0][1]])
        B2 = np.array([B_list[1][0],B_list[1][1]])
        B3 = np.array([B_list[2][0],B_list[2][1]])
        B4 = np.array([B_list[3][0],B_list[3][1]])
        
        # Vector AB
        AB = B - A
        # Kiểm tra vị trí của C1 và C2
        position_B1 = point_position(AB, A, B1)
        position_B3 = point_position(AB, A, B3)
        
        # print(f"Position of B1 relative to AB: {position_B1}")
        # print(f"Position of B3 relative to AB: {position_B3}")
        
        # plt.plot(B1[0],B1[1],marker='o',color='red', label='B1')
        # plt.plot(B3[0],B3[1],marker='o',color='blue', label='B3')
        # plt.plot(B2[0],B2[1],marker='s',color='red', label='B2')
        # plt.plot(B4[0],B4[1],marker='s',color='blue', label='B4')

        # plt.xlabel('X')
        # plt.ylabel('Y')        
        # plt.grid(True)
        # plt.legend()
        # plt.show()

        if offset < 0:
            if position_B1 == "right":
                B11 = B1
                B22 = B2
            else:
                B11 = B3
                B22 = B4
        else:
            if position_B1 == "right":
                B11 = B3
                B22 = B4
            else:
                B11 = B1
                B22 = B2


        dist11_x = B11[0] - B[0]
        dist11_y = B11[1] - B[1]

        dist22_x = B22[0] - B[0]
        dist22_y = B22[1] - B[1]

        for i in range(len(y_curve1)):
            x_curve1[i] = x_curve1[i] + (dist11_x / (len(x_curve1) - 1)) * i
            y_curve1[i] = y_curve1[i] + (dist11_y / (len(y_curve1) - 1)) * i

        for i in range(len(x_curve2)):
            x_curve2[i] = x_curve2[i] + (dist22_x / (len(x_curve2) - 1)) * (len(x_curve2) - 1 - i)
            y_curve2[i] = y_curve2[i] + (dist22_y / (len(y_curve2) - 1)) * (len(y_curve2) - 1 - i)
            

        
        # k11 = (B11[1] - A[1])/(B11[0] - A[0])

        # a1 = k11
        # b1 = -1
        # c1 = k11*A[0] - A[1]

        # a2 = 1/k11
        # b2 = 1
        # c2 = x_curve1[-2]/k11 + y_curve1[-2]

        # x_curve1[-2] = -(b1*c2 - b2*c1) / (a1*b2 - a2*b1)
        # y_curve1[-2] = -(a1*c2 - a2*c1) / (a2*b1 - a1*b2)


        # k22 = (B22[1] - C[1])/(B22[0] - C[0])

        # a1 = k22
        # b1 = -1
        # c1 = k22*C[0] - C[1]

        # a2 = 1/k22
        # b2 = 1
        # c2 = x_curve2[1]/k22 + y_curve2[1]

        # x_curve2[1] = -(b1*c2 - b2*c1) / (a1*b2 - a2*b1)
        # y_curve2[1] = -(a1*c2 - a2*c1) / (a2*b1 - a1*b2)


        # plt.plot(x_curve1, y_curve1, linestyle="-.", color="blue")
        # plt.plot(x_curve2, y_curve2, linestyle="-.", color="red")
        # plt.show()

    elif offset == 1 :

        (x_curve1[-1],y_curve1[-1]) = (x_curve2[0],y_curve2[0])

        # plt.plot(x_curve1, y_curve1, linestyle="-.", color="blue")
        # plt.plot(x_curve2, y_curve2, linestyle="-.", color="red")

        # plt.plot([x_curve1[-7], x_curve2[6]], [y_curve1[-7], y_curve2[6]], marker='o') 

        point_list = []

        if len(x_curve1) > 8 and len(x_curve2) > 8:

            point_list += [(x_curve1[-6],y_curve1[-6])]
            point_list += [(x_curve1[-5],y_curve1[-5])]
            point_list += [(x_curve1[-4],y_curve1[-4])]
            point_list += [(x_curve1[-3],y_curve1[-3])]
            point_list += [(x_curve1[-2],y_curve1[-2])]
            point_list += [(x_curve1[-1],y_curve1[-1])]

            point_list += [(x_curve2[0],y_curve2[0])]
            point_list += [(x_curve2[1],y_curve2[1])]
            point_list += [(x_curve2[2],y_curve2[2])]
            point_list += [(x_curve2[3],y_curve2[3])]
            point_list += [(x_curve2[4],y_curve2[4])]
            point_list += [(x_curve2[5],y_curve2[5])]


        # else:

        #     point_list += [(x_curve1[-3],y_curve1[-3])]
        #     point_list += [(x_curve1[-2],y_curve1[-2])]
        #     point_list += [(x_curve1[-1],y_curve1[-1])]

        #     point_list += [(x_curve2[0],y_curve2[0])]
        #     point_list += [(x_curve2[1],y_curve2[1])]
        #     point_list += [(x_curve2[2],y_curve2[2])]

        point_list_new = []

        for i in range(len(point_list)):
            X = point_list[i]
            k = (y_curve2[6]-y_curve1[-7])/(x_curve2[6]-x_curve1[-7])

            a1 = k
            b1 = -1
            c1 = k*x_curve2[6] - y_curve2[6]

            a2 = 1/k
            b2 = 1
            c2 = X[0]/k + X[1]

            X_x = -(b1*c2 - b2*c1) / (a1*b2 - a2*b1)
            X_y = -(a1*c2 - a2*c1) / (a2*b1 - a1*b2)
            point_list_new += [(X_x,X_y)]

            # plt.plot(X_x,X_y, marker='o',color='blue', label='X')


        if len(x_curve1) > 8 and len(x_curve2) > 8:

            (x_curve1[-6],y_curve1[-6]) = point_list_new[0]
            (x_curve1[-5],y_curve1[-5]) = point_list_new[1]
            (x_curve1[-4],y_curve1[-4]) = point_list_new[2]
            (x_curve1[-3],y_curve1[-3]) = point_list_new[3]
            (x_curve1[-2],y_curve1[-2]) = point_list_new[4]
            (x_curve1[-1],y_curve1[-1]) = point_list_new[5]

            (x_curve2[0],y_curve2[0]) = point_list_new[6]
            (x_curve2[1],y_curve2[1]) = point_list_new[7]
            (x_curve2[2],y_curve2[2]) = point_list_new[8]
            (x_curve2[3],y_curve2[3]) = point_list_new[9]
            (x_curve2[4],y_curve2[4]) = point_list_new[10]
            (x_curve2[5],y_curve2[5]) = point_list_new[11]

        # else:

        #     (x_curve1[-3],y_curve1[-3]) = point_list_new[0]
        #     (x_curve1[-2],y_curve1[-2]) = point_list_new[1]
        #     (x_curve1[-1],y_curve1[-1]) = point_list_new[2]

        #     (x_curve2[0],y_curve2[0]) = point_list_new[3]
        #     (x_curve2[1],y_curve2[1]) = point_list_new[4]
        #     (x_curve2[2],y_curve2[2]) = point_list_new[5]

        # plt.plot(x_curve1, y_curve1, linestyle="-", color="blue")
        # plt.plot(x_curve2, y_curve2, linestyle="-", color="red")

    return x_curve1, y_curve1, x_curve2, y_curve2

def solve_quadratic(a, b, c):
    # Check if a is zero, which means it's not a quadratic equation
    if a == 0:
        raise ValueError("Coefficient 'a' must not be zero")

    # Calculate the discriminant
    discriminant = b**2 - 4*a*c

    # Compute solutions based on the value of discriminant
    if discriminant > 0:
        # Two real roots
        x1 = (-b + math.sqrt(discriminant)) / (2*a)
        x2 = (-b - math.sqrt(discriminant)) / (2*a)
        return x1, x2
    elif discriminant == 0:
        # One real root (double root)
        x = -b / (2*a)
        return x,
    else:
        # Complex roots
        real_part = -b / (2*a)
        imaginary_part = math.sqrt(abs(discriminant)) / (2*a)
        return (real_part + imaginary_part * 1j, real_part - imaginary_part * 1j)
    
def point_position(AB, A, C):
    # AB: vector AB
    # A: điểm A
    # C: điểm C
    
    # Vector từ A đến C
    AC = C - A
    
    # Tính tích vô hướng AB và AC
    cross_product = np.cross(AB, AC)
    
    if cross_product > 0:
        return "left"
    elif cross_product < 0:
        return "right"
    else:
        return "on the line"

    # Calculate the slope of AB
    slope_AB = (B[1] - A[1]) / (B[0] - A[0]) if B[0] != A[0] else None

    # The slope of BC (perpendicular to AB) is the negative reciprocal of the slope of AB
    if slope_AB is not None:
        slope_BC = -1 / slope_AB
    else:
        slope_BC = 0

    # Calculate the angle of BC with respect to the x-axis
    angle_BC = math.atan(slope_BC)

    # Calculate the coordinates of C
    C_x_1 = B[0] - offset * math.cos(angle_BC)
    C_y_1 = B[1] - offset * math.sin(angle_BC) 

    C_x_2 = B[0] + offset * math.cos(angle_BC)
    C_y_2 = B[1] + offset * math.sin(angle_BC)  

    dist_1 = math.sqrt((C_x_1 - D[0])** 2 + (C_y_1 - D[1])** 2)
    dist_2 = math.sqrt((C_x_2 - D[0])** 2 + (C_y_2 - D[1])** 2)

    if dist_1 < dist_2:
        C_x = C_x_1
        C_y = C_y_1
    else:
        C_x = C_x_2
        C_y = C_y_2

    return (C_x, C_y)



def add_curvature_info(imp_df, hdg_start = 10, hdg_end = 10):  # 三橋さんサンプル(書き方は修正が必要)
        # imp_df = self.df_polyline
        o_list = []  # dataframe作成用のからリスト
        iter = len(imp_df)  # 繰り返し回数
        length = [20, 10, 0]

        """"""
        for i in range(1, iter - 1):
            for j in length:
                r, cx, cy = ccf.culc_curveture(imp_df["X"], imp_df["Y"], i, j)
                rr = 1 / r
                if j < abs(r):
                    o_list.append(
                        [
                            int(imp_df["ID"][i]),
                            imp_df["X"][i],
                            imp_df["Y"][i],
                            r,
                            cx,
                            cy,
                            rr,
                        ]
                    )
                    break

        """"""

        # 始点と終点は曲率をコピー
        o_list.insert(
            0,
            [
                int(imp_df["ID"][0]),
                imp_df["X"][0],
                imp_df["Y"][0],
                o_list[0][3],
                o_list[0][4],
                o_list[0][5],
                o_list[0][6],
            ],
        )
        o_list.append(
            [
                int(imp_df["ID"][iter - 1]),
                imp_df["X"][iter - 1],
                imp_df["Y"][iter - 1],
                o_list[-1][3],
                o_list[-1][4],
                o_list[-1][5],
                o_list[-1][6],
            ]
        )

        hdg_list = []

        for i in range(len(o_list)):
            tmp_rad = math.atan2(
                o_list[i][2] - o_list[i][5], o_list[i][1] - o_list[i][4]
            )
            if o_list[i][3] < 0:  # 曲率がマイナスの場合方位を反転(曲率半径の点の位置が反転するため)
                tmp_rad = tmp_rad + math.pi
            rad = tmp_rad + math.pi / 2  # 90度オフセット。円の中心への方位角から道路中心点の方位角に変換する
            """   
            if rad < 0.5:
                rad = rad+2*math.pi
            """
            hdg_list.append(rad)

        # テスト:急激な方位角ギャップを平滑化するため、前後の方位角との平均を取る
        """
        hdg_list_smooth = [hdg_list[0]]
        for i in range(len(hdg_list)-2):
            hdg_list_smooth.append((hdg_list[i]+hdg_list[i+1]+hdg_list[i+2])/3)
        hdg_list_smooth.append(hdg_list[-1])
        """

        if hdg_start != 10:
            # print(hdg_list[0])
            hdg_list[0] = hdg_start
            hdg_list[1] = hdg_start
            hdg_list[2] = hdg_start
            # print(hdg_start)

        if hdg_end != 10:
            hdg_list[-1] = hdg_end
            hdg_list[-2] = hdg_end
            hdg_list[-3] = hdg_end
            hdg_list[-4] = hdg_end


        for i in range(len(o_list)):
            o_list[i].extend([hdg_list[i]])

        for i in range(len(o_list)):
            o_list[i].append(imp_df["elev"][i])
            o_list[i].append(imp_df["elev_a"][i])
            o_list[i].append(imp_df["elev_b"][i])
            o_list[i].append(imp_df["elev_c"][i])
            o_list[i].append(imp_df["elev_d"][i])
            o_list[i].append(imp_df["elev_s"][i])

        for i in range(int(len(o_list)) - 1):
            # cv_len = abs(math.atan2(o_list[i][5] - o_list[i][2],o_list[i][4] - o_list[i][1])-math.atan2(o_list[i][5] - o_list[i+1][2],o_list[i][4] - o_list[i+1][1]))*abs(o_list[i][3])
            # 一時的な対応（今のところ問題はなさそうに思えるが要相談）
            a = np.array((o_list[i][2], o_list[i][1]))
            b = np.array((o_list[i + 1][2], o_list[i + 1][1]))
            cv_len = np.linalg.norm(a - b)
            shape = (
                "arc"
                if o_list[i][3] == o_list[i + 1][3]
                else "line"
                if abs(o_list[i][3]) > 5000
                else "spiral"
            )
            o_list[i].extend([shape])
        o_df = pd.DataFrame(o_list)
        o_df = o_df.rename(
            columns={
                0: "ID",
                1: "x",
                2: "y",
                3: "curvature_radius",
                4: "cx",
                5: "cy",
                6: "curvature",
                7: "hdg",
                8: "elev",
                9: "elev_a",
                10: "elev_b",
                11: "elev_c",
                12: "elev_d",
                13: "length",
                14: "shape",
            }
        )

        return o_df, hdg_list

def rotate_polyline(p_base, p_old_list, flag_rotation):

    x_base, y_base = p_base
    x_list, y_list = p_old_list

    if flag_rotation:

        dist_x = x_base - x_list[-1]
        dist_y = y_base - y_list[-1]

        for i in range(len(y_list)):
            x_list[i] = x_list[i] + (dist_x / (len(x_list) - 1)) * (i)
            y_list[i] = y_list[i] + (dist_y / (len(x_list) - 1)) * (i)

    else:
        dist_x = x_base - x_list[0]
        dist_y = y_base - y_list[0]

        for i in range(len(y_list)):
            x_list[i] = x_list[i] + (dist_x / (len(x_list) - 1)) * (len(x_list) - 1 - i)
            y_list[i] = y_list[i] + (dist_y / (len(x_list) - 1)) * (len(x_list) - 1 - i)
    
    return (x_list, y_list)



def calculate_rotation_angle(p1, p2_old, p2_new):
    """
    Tính toán góc xoay cần thiết để biến điểm cuối cũ p2_old thành điểm cuối mới p2_new,
    xoay quanh điểm đầu p1.
    
    :param p1: Tuple chứa tọa độ của điểm đầu (x1, y1).
    :param p2_old: Tuple chứa tọa độ của điểm cuối cũ (x2_old, y2_old).
    :param p2_new: Tuple chứa tọa độ của điểm cuối mới (x2_new, y2_new).
    :return: Góc xoay tính bằng radian.
    """
    x1, y1 = p1
    x2_old, y2_old = p2_old
    x2_new, y2_new = p2_new
    
    # Tính toán vectơ từ điểm đầu đến điểm cuối cũ và điểm cuối mới
    dx_old = x2_old - x1
    dy_old = y2_old - y1
    dx_new = x2_new - x1
    dy_new = y2_new - y1
    
    # Tính toán tích vô hướng
    dot_product = dx_old * dx_new + dy_old * dy_new
    
    # Tính toán độ dài của các vectơ
    length_old = math.sqrt(dx_old**2 + dy_old**2)
    length_new = math.sqrt(dx_new**2 + dy_new**2)
    
    # Tính toán góc giữa hai vectơ
    cos_theta = dot_product / (length_old * length_new)
    
    # Đảm bảo giá trị cos_theta nằm trong khoảng [-1, 1] để tránh lỗi số học
    cos_theta = max(-1, min(1, cos_theta))
    
    theta = math.acos(cos_theta)
    
    # Xác định hướng của góc xoay
    cross_product = dx_old * dy_new - dy_old * dx_new
    if cross_product < 0:
        theta = -theta
    
    return theta

def rotate_line_points(p1, points_old, p2_new):
    """
    Xoay tất cả các điểm của đoạn thẳng quanh điểm đầu p1 để điểm cuối cũ trở thành điểm cuối mới.
    
    :param p1: Tuple chứa tọa độ của điểm đầu (x1, y1).
    :param points_old: Danh sách các tọa độ điểm của đoạn thẳng cũ.
    :param p2_new: Tuple chứa tọa độ của điểm cuối mới (x2_new, y2_new).
    :return: Danh sách các tọa độ điểm của đoạn thẳng mới.
    """
    # Xác định điểm cuối cũ
    p2_old = points_old[-1]
    
    # Tính toán góc xoay cần thiết
    theta = calculate_rotation_angle(p1, p2_old, p2_new)
    
    # Hàm xoay điểm
    def rotate_point(px, py, theta):
        x1, y1 = p1
        dx = px - x1
        dy = py - y1
        x_new = x1 + dx * math.cos(theta) - dy * math.sin(theta)
        y_new = y1 + dx * math.sin(theta) + dy * math.cos(theta)
        return (x_new, y_new)
    
    # Xoay tất cả các điểm
    points_new = [rotate_point(x, y, theta) for x, y in points_old]
    
    return points_new

# # Ví dụ sử dụng
# p1 = (0, 0)  # Điểm đầu
# points_old = [(0, 0), (1, 0), (2, 0)]  # Danh sách các điểm của đoạn thẳng cũ
# p2_new = (0, 2)  # Điểm cuối mới

# points_new = rotate_line_points(p1, points_old, p2_new)
# print("Danh sách các điểm mới:", points_new)

