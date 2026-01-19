import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pyclothoids

def interpolate_points(points, step=1.0):
    points = np.array(points)
    interpolated_points = [points[0]]
    
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        distance = np.linalg.norm(p2 - p1)
        num_steps = int(np.floor(distance / step))
        
        for j in range(1, num_steps + 1):
            new_point = p1 + (p2 - p1) * (j * step / distance)
            interpolated_points.append(new_point)
    
    return np.array(interpolated_points)

# 軌跡上の最も近い点を求める関数
def func_calc_st(road_points, target_point):
    target_point = np.array(target_point)
    min_dist = float('inf')
    nearest_point = None
    distance_from_start = 0
    nearest_distance_from_start = 0
    signed_distance = 0
    
    for i in range(len(road_points) - 1):
        p1, p2 = np.array(road_points[i]), np.array(road_points[i + 1])
        v = p2 - p1
        u = target_point - p1
        t = np.dot(u, v) / np.dot(v, v)
        t = np.clip(t, 0, 1)  # 0 <= t <= 1 に制限
        projection = p1 + t * v
        dist = np.linalg.norm(target_point - projection)
        
        # 外積を用いて左右を判定
        cross_product = np.cross(v, target_point - projection)
        sign = np.sign(cross_product)
        
        if dist < min_dist:
            min_dist = dist
            nearest_point = projection
            nearest_distance_from_start = distance_from_start + np.linalg.norm(projection - p1)
            signed_distance = sign * dist
        
        distance_from_start += np.linalg.norm(p2 - p1)
    
    return nearest_point, nearest_distance_from_start, signed_distance

"""
#signals_exist_check.pyで呼び出して使う
# CSVファイルからデータを読み込む
points_df = pd.read_csv('points.csv')
target_point_df = pd.read_csv('target_point.csv')

# データをnumpy配列に変換
points = points_df[['x', 'y']].values
target_point = target_point_df[['x', 'y']].values[0]

# 下記２つの関数を実行
recreate_points = interpolate_points(points, step=1.0) #1m間隔で生成される道路点群
nearest_point, s, t = func_calc_st(recreate_points, target_point)

print(s)
print(t)
"""

"""
# 図に表示
plt.plot(points[:, 0], points[:, 1], 'ro-', label='Original Points')
plt.plot(recreate_points[:, 0], recreate_points[:, 1], 'bo-', markersize=3, label='Interpolated Points')
plt.plot(target_point[0], target_point[1], 'gx', markersize=10, label='Point target_point')
plt.plot(nearest_point[0], nearest_point[1], 'ms', markersize=10, label='Nearest Point')
plt.legend()
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Linear Interpolation and Nearest Point on Path')
plt.grid()
plt.axis('equal')  # XY軸のスケールを等倍にする
plt.show()
"""