#必要なライブラリの読み込み
import math

#サブフォルダから読み込み
from submodule import culc_latlon_etc as cle


#★★これが、本ファイルの統合ファイルで、基本的に外部からはこの関数を使う★★
#入力：南西、北東の緯度経度、出力：call用の緯度経度リスト
def call_latlon_out_list(lat0,lon0,lat1,lon1):
    out_list = []
    for i in devide_latlon_list(lat0,lon0,lat1,lon1):
        out_list.append(call_latlon_list(i[0],i[1],i[2],i[3]))
    
    return(out_list)


#入力：南西、北東の緯度経度、出力：サーバーCallごとの南西緯度経度、北東緯度経度のリスト
#道路を取得する範囲を取得、広すぎるとメモリーがオーバーフローするかも･･･
def devide_latlon_list(lat0,lon0,lat1,lon1):
    #南北方向の区域分けを実施、これに従いサーバーにコール
    Y_dist = cle.latlon_dist(lat0,lon0,lat1,lon0)    #南北方向の距離を計算
    Y_div = math.ceil(Y_dist / ( 700 * 4 ))          #半径500mの円の内接正方形を700mとし、いくつで区切れるか計算
    Y_len = ((lat1 - lat0) / Y_div)
    #東西方向の区域分けを実施、これに従いサーバーにコール
    X_dist = cle.latlon_dist(lat0,lon0,lat0,lon1)    #南北方向の距離を計算
    X_div = math.ceil(X_dist / ( 700 * 5 ))          #半径500mの円の内接正方形を700mとし、いくつで区切れるか計算
    X_len = ((lon1 - lon0) / X_div)
    #出力するリストの作成、X、Y、それぞれの方向で繰り返し
    devide_list = []
    for i in range(Y_div):
        for j in range(X_div):
            devide_list.append([lat0 + Y_len * i,lon0 + X_len * j,lat0 + Y_len * (i+1),lon0 + X_len * (j + 1)])
    return(devide_list)

#入力：Callごとの南西緯度経度、北東緯度経度、出力:Callに利用する、入力緯度経度点列リスト
def call_latlon_list(lat0,lon0,lat1,lon1):
    #経度方向5地点、緯度方向4地点の計20地点をリクエスト地点として入力するように分割
    lat_len = (lat1 - lat0) / 4
    lon_len = (lon1 - lon0) / 5
    call_list = []
    for i in range(4):
        for j in range(5):
            call_list.extend([round(lat0 + (0.5 + i ) * lat_len , 7) ,round(lon0 + (0.5 + j ) * lon_len , 7 ) ])
    return(call_list)

