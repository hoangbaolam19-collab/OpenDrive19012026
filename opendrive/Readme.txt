使用方法:

[getRoadData.py]または[getMultipointRoadData.py]でいつもナビAPI3.0の周辺道路リンク検索(自動車)を道路リンク情報を取得します。

周辺道路検索を行うための緯度経度および距離範囲を指定するファイルを作成し、[search_point]フォルダにおいてください。
座標の測地系はWGS84です。
このファイルは列名をlatitude,longitude,rangeとするcsv形式で作成してください。
また、ファイル名称は[search_point.csv]もしくは[search_point_xxx.csv]としてください。
search_point.csv、search_point_xxx.csvを複数行作成することで複数地点に対する周辺道路リンク検索が実施されます。


参照されるファイルは
[python getRoadData.py]または[getMultipointRoadData.py]で実行すると[search_point.csv]、
[python getRoadData.py xxx]または[getMultipointRoadData.py xxx]で実行すると[search_point_xxx.csv]
となります。
[getRoadData.py]を実行すると、search_point_xxx.csvに記述された行数分、いつもナビAPI3.0の周辺道路リンク検索が実施されます。
[getMultipointRoadData.py]を実行すると、search_point_xxx.csvに記述された地点に対して、一度だけいつもナビAPI3.0の周辺道路リンク検索が実施されます。
[getMultipointRoadData.py]を実行した場合、周辺道路リンク検索の「マッチング距離範囲」はsearch_point_xxx.csvの最初の行で指定されたrangeの値が適用されます。


いつもナビAPI3.0によって取得された周辺道路リンク情報は[road_data]フォルダに出力されます。
このとき、出力されるファイル名は、
[python getRoadData.py]または[getMultipointRoadData.py]では[roda_data.csv]、
[python getRoadData.py xxx]または[getMultipointRoadData.py xxx]では[road_data_xxx.csv]
となります。

[getOpenDRIVE.py]で[road_data]フォルダ内のファイルからOpenDRIVE形式への変換を行います。

変換に使用されるファイルは、
[python getOpenDRIVE.py]で実行すると[road_data.csv]、
[python getOpenDRIVE.py -f xxx]で実行すると[road_data_xxx.csv]
です。

OpenDRIVE形式に変換されたファイルは[open_drive_format]フォルダにxml形式で出力されます。

出力ファイル名は
[python getOpenDRIVE.py]では[open_drive_format.xodr]、
[python getOpenDRIVE.py -f xxx]では[open_drive_format_xxx.xodr]となります。


search_point_test1.csvを使用する場合の使用例：

>python getRoadData.py test1
>python getOpenDRIVE.py -f test1


OpenDRIVE形式への変換処理での主な制限事項:

１．高速道路の接続
	OpenDRIVE形式への変換はすべての道路を対象としますが、接続先・接続元の道路が高速道路である場合、
	ジャンクションでの接続は暫定的な処理になります。
	そのため、接続する道路のレーン数や接続するレーン位置等が実際とは異なるといった状況が発生します。

補足：

変換したデータを使用する際にインポートするシミュレーション環境等によっては道路形状が正しく変換されない
ことがあります。
特にクロソイド曲線の変換で問題が生じる場合には、Parametric Cubic Curveを用いることで正しく変換できる場合が
あります。
コマンドライン引数を下記のように指定することで、全てのSpiralに該当するGeometryをParametric Cubic Curve
として出力します。
[python getOpenDRIVE.py -p 1]
