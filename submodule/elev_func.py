from numpy.linalg import solve
import math
#leftはax + by,rightは解、その連立方程式

#S:開始地点からの距離、elev：標高、hdg:方位角（ラジアン）
def cubic_function(s_1,elev_1,hdg_1,s_2,elev_2,hdg_2):
    try:
#すぐにわかる係数の算出
        c = math.tan(hdg_1)
        d = elev_1
#計算用変数の定義
        x2  = s_2 - s_1
        y2  = elev_2 - elev_1
        yd2 = math.tan(hdg_2)
#連立方程式1項目
        la_1 = x2 ** 3
        lb_1 = x2 ** 2
        r_1  = y2 - c * x2
#連立方程式2項目
        la_2 = 3 * x2 ** 2
        lb_2 = 2 * x2
        r_2  = yd2 - c
#連立方程式求解
        left = [[la_1, lb_1],[la_2, lb_2]]
        right = [r_1, r_2]
        a,b = solve(left, right)
    except:
        a,b,c,d = 0,0,0,0
    return a,b,c,d