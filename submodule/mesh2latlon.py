import glob
import sys
import os

import pandas as pd
import numpy as np
import geopandas as gpd

import glob


MESHCODE = 'Z533935'
NODENO = 25584


PATH = r'../2202DB'

#NODEからnode番号、緯度経度を取得
def load_node(meshcode,nodeno):
    db_path = glob.glob(PATH+'\*')
    for path in db_path:
    #df_node = pd.read_csv(self.path + r'\CSV\\' + self.file + '\\'+self.file+'_NODE.csv', sep=',')

        if os.path.isfile(path + r"\\SHAPE\\25K\\" + meshcode + '\\'+meshcode+'_NODE.dbf'):
            df_node = gpd.read_file(path + r"\\SHAPE\\25K\\" +meshcode + '\\'+meshcode+'_NODE.dbf', sep=',')
            df_node.iloc[:, [2, 3]]/= 1000*3600
            df_node_data = df_node.loc[:,['meshcode','nodeno','x','y']] #ノード読み込み

            node_data = df_node_data[df_node_data['nodeno'] == nodeno].drop_duplicates().reset_index(drop=True)
            print(node_data)
            return node_data


if __name__ == "__main__": 
    load_node(MESHCODE,NODENO)

