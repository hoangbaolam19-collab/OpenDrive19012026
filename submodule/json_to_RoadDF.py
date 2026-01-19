#必要なライブラリのインポート
import json
import pandas as pd
import sys

#自作のライブラリのインポート
from submodule import culc_latlon_etc as cle

#pandasの小数点表示桁数を7桁に変更
pd.options.display.precision = 7

def JsonToDF(json_text):
    #JSONファイルの読み込み
    j_data = json.loads(json_text) #txtの場合はjson.loadsを使用
    #
    #
    #Wayのリストを準備
    #
    way_id = []              #WayのID（100000から開始）
    code = []                #リンクID
    init_latlon = []         #リンク先頭の緯度,経度
    end_latlon = []          #リンク末端の緯度,経度
    center_list = []
    node_index = []          #緯度経度のインデックス列
    roadType = []            #道路種別コード
    roadType_t = []          #道路種別名称
    limitedHihway = []       #自動車専用道フラグ
    numberOfLanes = []       #車線数
    roadWidth = []           #車線幅員
    onewayCode = []          #一方通行フラグ
    generalRoadName1 = []    #一般道路名称
    popularRoadName = []     #popularRoadName
    maxspeed_front = []      #リンクの制限速度
    roadelevation = []       #道路標高の抽出
    road_elev_list = []      #道路標高のデータフレーム用編集値
    max_speed = []           #最高速度情報
    ini_to_sec_dir = []      #始点への方向
    end_to_sec_dir = []      #終点への方向
    gradient = []            #始点→終点勾配
    #
    #Way作成用のリストに各情報を格納
    #
    way_id_num = 100000
    #
    for i in j_data["item"]:
        for link_data in i:
            way_id.append(way_id_num);way_id_num += 1
            code.append(link_data["link"]["code"])
            init_latlon.append([link_data["link"]["line"][0],link_data["link"]["line"][1]])
            end_latlon.append([link_data["link"]["line"][-2],link_data["link"]["line"][-1]])
            center_list.append([link_data["link"]["line"][:len(link_data["link"]["line"])]])
            roadType.append(link_data["link"]["roadType"]["code"])
            roadType_t.append(link_data["link"]["roadType"]["text"])
            limitedHihway.append(link_data["link"]["limitedHighway"])
            numberOfLanes.append(link_data["link"]["numberOfLanes"])
            roadWidth.append(link_data["link"]["roadWidth"])
            onewayCode.append(link_data["link"]["onewayCode"])
            generalRoadName1.append(link_data["link"]["generalRoadName1"])
            popularRoadName.append(link_data["link"]["popularRoadName"])
            roadelevation.append(link_data["link"]["adas"]["roadelevation"])
            #制限速度情報の付与
            max_speed_val = 0
            speed_val_front = 0
            try:
                if link_data["link"]["	adas"]["maxspeedFront"][0]["limit"] is not None: speed_val_front = link_data["link"]["adas"]["maxspeedFront"][0]["limit"]
            except:
                speed_val_front = 0
            try:
                if link_data["link"]["adas"]["maxspeedBack"][0]["limit"] is not None: speed_val_Back = link_data["link"]["adas"]["maxspeedBack"][0]["limit"]
            except:
                speed_val_Back = 0
            max_speed_val = speed_val_front if speed_val_front > 0 else speed_val_Back if speed_val_Back > 0 else 60
            max_speed.append(max_speed_val)
            ini_to_sec_dir.append(round(cle.latlon_dir(link_data["link"]["line"][2],link_data["link"]["line"][3],link_data["link"]["line"][0],link_data["link"]["line"][1]),2))
            end_to_sec_dir.append(round(cle.latlon_dir(link_data["link"]["line"][-4],link_data["link"]["line"][-3],link_data["link"]["line"][-2],link_data["link"]["line"][-1]),2))
            gradient.append(round((link_data["link"]["adas"]["roadelevation"][-1]["elevation"] - link_data["link"]["adas"]["roadelevation"][0]["elevation"])/1000/link_data["link"]["distance"]*100,3))
    #
    #
    #要素の長さの取得
    way_len = len(code)
    #
    #
    #adasの標高の編集
    for i in roadelevation:
        latlon,ele = [],[]
        for j in i:
            latlon.append([j["lat"],j["lon"]]);ele.append(j["elevation"])
        road_elev_list.append([latlon,ele])
    #
    #
    #adas情報を補正
    correct_ele_list = []
    for i in range(way_len):
        temp_list = []
        #
        link_init = init_latlon[i]
        link_end  = end_latlon[i]
        road_ele_init = road_elev_list[i][0][0]
        road_ele_end  = road_elev_list[i][0][-1]
        ini_d_latlon = [x - y for (x,y) in zip(link_init,road_ele_init)]
        end_d_latlon = [x - y for (x,y) in zip(link_end,road_ele_end)]
        #ここから、リンクの補正を実施
        for j in road_elev_list[i][0]:
            correct_lat = round(j[0] + ((j[0]+0.00000000001 - road_ele_init[0]) / (road_ele_end[0]+0.0000000001 - road_ele_init[0]) * ( end_d_latlon[0]+0.0000000001 - ini_d_latlon[0]) + ini_d_latlon[0]),7)
            correct_lon = round(j[1] + ((j[1]+0.00000000001 - road_ele_init[1]) / (road_ele_end[1]+0.0000000001 - road_ele_init[1]) * ( end_d_latlon[1]+0.0000000001 - ini_d_latlon[1]) + ini_d_latlon[1]),7)
            temp_list.append([correct_lat,correct_lon])
        correct_ele_list.append([temp_list,road_elev_list[i][1]])
    #
    #
    #wayのデータフレームを作成
    #

    way_dict2 = {"code" : code,
    "center": center_list}
    
    #
    way_df = pd.DataFrame.from_dict(way_dict2)
    way_df = way_df.drop_duplicates(subset='code',ignore_index=True)
    #
    return(way_df)


#way_dfから標高情報と補正されたノード情報を出す
def way_df_add_elev(imput_way_df):
    #adasを反映したnodeリストを作成
    lat,lon,ele = [],[],[]
    #
    for i in imput_way_df["roadelevation"]:
        temp_len = len(i[0])
        for j in range(temp_len):
            lat.append(i[0][j][0]);lon.append(i[0][j][1]);ele.append(i[1][j]) 
    
    #nodeのデータフレームを作成
    #
    node_dict = {"lat" : lat,"lon" : lon ,"elevation" : ele }
    node_df = pd.DataFrame.from_dict(node_dict)
    node_df = node_df.drop_duplicates()
    node_df["elevation"] = round(node_df["elevation"] / 1000,3) 
    node_df = node_df.reset_index()
    #
    #Wayデータフレームの構成ノードリストを作成し、反映
    way_node_list = []
    #
    for i in imput_way_df["roadelevation"]:
        temp_list = []
        for j in i[0]:
            temp_list = temp_list + node_df.index[(node_df["lat"] == j[0] ) & (node_df["lon"] == j[1] )].tolist()
        way_node_list.append(temp_list)
    #
    imput_way_df["node_list"] = way_node_list
    return(imput_way_df,node_df)
    
