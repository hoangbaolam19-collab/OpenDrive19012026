# -*- coding: utf-8 -*-
import math as mt

class latlon2grid:
    def grid1st(lon, lat):  # 1次メッシュ(4桁) 分割なし
        return int(mt.floor(lat*1.5)) * 100 + int(mt.floor(lon-100))

    def grid2nd(lon, lat):  # 2次メッシュ(6桁) 8分割
       return (int(mt.floor(lat*12       / 8))   * 10000 + int(mt.floor((lon-100)*8         / 8))  * 100   +   
               int(mt.floor(lat*12 %  8     ))   * 10    + int(mt.floor((lon-100)*8))  %  8               )  

    def grid3rd(lon, lat):  # 3次メッシュ(8桁) 8分割x10分割=80分割
        return (int(mt.floor(lat*120      / 80)) * 1000000 + int(mt.floor((lon-100))             ) * 10000 +  # 1次メッシュ
                int(mt.floor(lat*120 % 80 / 10)) * 1000    + int(mt.floor((lon-100)*80 % 80 / 10)) * 100 +    # 2次メッシュ
                int(mt.floor(lat*120 % 10))      * 10      + int(mt.floor((lon-100)*80)) % 10               ) 

    def grid4th(lon, lat):  # 4次メッシュ(9桁) 8分割x10分割x2分割=160分割
        return (int(mt.floor(lat*240       / 160)) * 10000000 + int(mt.floor((lon-100)*160       / 160)) * 100000 +    # 1次メッシュ
                int(mt.floor(lat*240 % 160 / 20))  * 10000    + int(mt.floor((lon-100)*160 % 160 / 20))  * 1000   +    # 2次メッシュ
                int(mt.floor(lat*240 % 20  / 2))   * 100      + int(mt.floor((lon-100)*160 % 20  / 2))   * 10     +    # 3次メッシュ
                int(mt.floor(lat*240)) % 2         * 2        + int(mt.floor((lon-100)*160)) % 2                  + 1) # 4次メッシュ

if __name__ == "__main__":
    lon = 139.74954 # 虎ノ門ヒルズ
    lat = 35.666863 # 虎ノ門ヒルズ
    print('1次メッシュ： ', latlon2grid.grid1st(lon, lat))  # 5339
    print('2次メッシュ： ', latlon2grid.grid2nd(lon, lat))  # 533945
    print('基準地域メッシュ： ', latlon2grid.grid3rd(lon, lat))  # 53394509
    print('4次メッシュ： ', latlon2grid.grid4th(lon, lat))  # 533945092