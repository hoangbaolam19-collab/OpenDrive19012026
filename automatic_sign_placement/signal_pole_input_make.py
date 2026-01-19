import pandas as pd
import os
import shutil

# Base directories resolved from this file location
BASE_DIR = os.path.dirname(__file__)
OPENDRIVE_DIR = os.path.join(BASE_DIR, 'opendrive_format')

# Paths for templates and outputs
SIGNAL_TEMPLATE_PATH = os.path.join(OPENDRIVE_DIR, 'signal_input.csv')
POLE_TEMPLATE_PATH = os.path.join(OPENDRIVE_DIR, 'pole_input.csv')
SIGNAL_INPUT_NEW_PATH = os.path.join(BASE_DIR, 'signal_input_new.csv')
POLE_INPUT_NEW_PATH = os.path.join(BASE_DIR, 'pole_input_new.csv')

# Module-level guard to initialize outputs exactly once per Python run
_outputs_initialized = False

def _initialize_outputs_once():
    global _outputs_initialized
    if _outputs_initialized:
        return
    # Reinitialize from templates at the start of each run
    if os.path.exists(SIGNAL_TEMPLATE_PATH):
        shutil.copyfile(SIGNAL_TEMPLATE_PATH, SIGNAL_INPUT_NEW_PATH)
    if os.path.exists(POLE_TEMPLATE_PATH):
        shutil.copyfile(POLE_TEMPLATE_PATH, POLE_INPUT_NEW_PATH)
    _outputs_initialized = True


def make_format(s1, t1, id1, maxspeed1, orflg1):
    # Initialize outputs from templates once per run
    _initialize_outputs_once()

    # Load current working CSVs (already reinitialized above)
    signal_input = pd.read_csv(SIGNAL_INPUT_NEW_PATH)

    #orientation(標識の向き)を決定
    
    # 欠損行を削除
    signal_input = signal_input.dropna().reset_index(drop=True)

    # 値の設定
    s = s1
    t = t1
    linkno = id1
    id_value = id1
    maxspeed = maxspeed1
    orflg = orflg1
    #print(orflg)

    for i in range(len(orflg)):
        if orflg[i] == 1:
            orientation = '-'
        else:
            orientation = '+'

    # linkno を signal_input の行数に設定
    id_value = 2*(len(signal_input) + 1)

    # 新しく追加する行
    new_row_signal = {
        'linkno': linkno,
        'name': f"Sign_323({maxspeed})",
        'id': id_value,
        's': s,
        't': t,
        'zOffset': 3.3,
        'hOffset': -2.79,
        'roll': 0.0,
        'pitch': 0.0,
        'orientation': orientation,
        'dynamic': 'no',
        'type': 323,
        'subtype': -1,
        'height': 0.4,
        'width': 0.4,
    }

    # 既存重複チェック（signal）
    existing_signal = signal_input[
        (signal_input['linkno'] == linkno) &
        (signal_input['s'] == s) &
        (signal_input['t'] == t) &
        (signal_input['name'] == new_row_signal['name'])
    ]
    if existing_signal.empty:
        # 行を追加
        signal_input = pd.concat([signal_input, pd.DataFrame([new_row_signal])], ignore_index=True)

    # 重複除去（signal）
    signal_input = signal_input.drop_duplicates(subset=['linkno','s','t','name'], keep='first')
    # 上書き保存（追記ではなく毎回更新された全体を保存）
    signal_input.to_csv(SIGNAL_INPUT_NEW_PATH, index=False)

    # Load pole input (already reinitialized above)
    pole_input = pd.read_csv(POLE_INPUT_NEW_PATH)
    
    # 欠損行を削除
    pole_input = pole_input.dropna().reset_index(drop=True)

    # signal_input_newから最大IDを取得して+1
    max_id = signal_input['id'].max()
    new_id = max_id + 1 if pd.notnull(max_id) else 1

    # 新しく追加する行
    new_row_pole = {
        'linkno': linkno,
        'name': 'Sign_Post01_3m',
        'id': new_id,
        's': s,
        't': t,
        'zOffset': 0.0,
        'hOffset': -2.79,
        'roll': 0.0,
        'pitch': 0.0,
        'orientation': orientation,
        'dynamic': 'no',
        'type': 'pole',
        'subtype': -1,
        'height': 3.5,
        'width': 0.04,
    }

    # 既存重複チェック（pole）
    existing_pole = pole_input[
        (pole_input['linkno'] == linkno) &
        (pole_input['s'] == s) &
        (pole_input['t'] == t) &
        (pole_input['name'] == new_row_pole['name'])
    ]
    if existing_pole.empty:
        # 行を追加
        pole_input = pd.concat([pole_input, pd.DataFrame([new_row_pole])], ignore_index=True)

    # 重複除去（pole）
    pole_input = pole_input.drop_duplicates(subset=['linkno','s','t','name'], keep='first')
    # 保存
    pole_input.to_csv(POLE_INPUT_NEW_PATH, index=False)

    print("結果が signal_input_new.csv と pole_input_new.csv に保存されました。")



"""
# CSVファイルを読み込みます
signal_input = pd.read_csv('signal_input.csv')
updated_data = pd.read_csv('updated_Z533936_MAXSPEED_SIGN_processed_updated_with_st_and_length.csv')
pole_input = pd.read_csv('pole_input.csv')

# idの値を+2ずつ大きくするための初期値を設定します
max_id = signal_input['id'].max() + 2

# updated_dataの各行に対して処理を行います
for index, row in updated_data.iterrows():
    linkno = row['linkno']
    maxspeed = row['maxspeed']
    s = row['s']
    t = row['t']
    length = row['length']
    
    # signal_inputに対応する行があるか確認します
    signal_row = signal_input[signal_input['id'] == linkno]
    
    if not signal_row.empty:
        # 既存の行を更新します
        signal_input.loc[signal_input['id'] == linkno, 'name'] = maxspeed
        signal_input.loc[signal_input['id'] == linkno, 's'] = s
        signal_input.loc[signal_input['id'] == linkno, 't'] = t
        signal_input.loc[signal_input['id'] == linkno, 'length'] = length
    else:
        # 新しい行を作成します
        new_row = signal_input.iloc[0].copy()  # 既存のデータの列をコピー
        new_row['id'] = max_id
        new_row['linkno'] = linkno
        new_row['name'] = maxspeed
        new_row['s'] = s
        new_row['t'] = t
        new_row['length'] = length
        
        # 新しい行をデータフレームに追加
        signal_input = pd.concat([signal_input, pd.DataFrame([new_row])], ignore_index=True)
        
        # idの値を+2する
        max_id += 2

# 新しいCSVファイルとして保存します
signal_input.to_csv('signal_input_new.csv', index=False)

# signal_input_new.csvを再度読み込みます
signal_input_new = pd.read_csv('signal_input_new.csv')

# pole_inputの各行に対して処理を行います
for index, row in signal_input_new.iterrows():
    linkno = row['linkno']
    s = row['s']
    t = row['t']
    new_id = row['id'] + 1
    length = row['length']
    
    # 新しい行を作成します
    new_row = pole_input.iloc[0].copy()  # 既存のデータの列をコピー
    new_row['linkno'] = linkno
    new_row['s'] = s
    new_row['t'] = t
    new_row['id'] = new_id
    new_row['length'] = length
    
    # 新しい行をデータフレームに追加
    pole_input = pd.concat([pole_input, pd.DataFrame([new_row])], ignore_index=True)

# 新しいCSVファイルとして保存します
pole_input.to_csv('pole_input_new.csv', index=False)

print("結果が signal_input_new.csv と pole_input_new.csv に保存されました。")
"""