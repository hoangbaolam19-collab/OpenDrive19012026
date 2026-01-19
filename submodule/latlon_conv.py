# -*- coding: utf-8 -*-

def deg2degminsec(coordinate):
    deg = int(coordinate)
    min = int((coordinate - deg)*60)
    sec = ((coordinate - deg)*60 - min)*60
    return deg,min,sec

#def degminsec2deg(lon, lat):  # 1次メッシュ(4桁) 分割なし
    #return int(mt.floor(lat*1.5)) * 100 + int(mt.floor(lon-100))