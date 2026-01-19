from submodule import B_spline
import pandas as pd
import numpy as np

def reculc_line(in_df):
#
    out_df = None
    count  = 0
#
    for i in pd.unique(in_df["ID"]):
        x,y,z,tmp_array,id  ="","","","",""
        bool_list     = in_df["ID"] == i
        id            = in_df[bool_list]["ID"].reset_index()
        x             = in_df[bool_list]["X"].to_list()
        y             = in_df[bool_list]["Y"].to_list()
        z             = in_df[bool_list]["elev"].to_list()
        temp_array    = np.transpose(B_spline.B_spline(x, y ,z))
        B_spline_df   = pd.DataFrame(temp_array)
        temp_df       = pd.merge(id,B_spline_df, left_index=True, right_index=True)
        if count == 0:
            out_df        = temp_df
        else:
           out_df = pd.concat([out_df,temp_df])
        count = count + 1
#
    out_df = out_df.reset_index()
    out_df = out_df.drop('index',axis=1)
    out_df = out_df.drop('level_0',axis=1)
    out_df = out_df.rename(columns={0: "X",1:"Y",2:"elev"})
#
    return out_df
