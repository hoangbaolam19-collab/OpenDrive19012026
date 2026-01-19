#必要なライブラリをインポート
import time
import urllib.parse
import urllib
import urllib.request
import hmac
import hashlib
import base64
import random, string

#Oauthの企業
clientid = 'JSZ04a4c17e7e79|2TN9y'     #クライアントキー
secret_key = '92-rZ_7X04pE5RZV_Lou1Wg2Xyc' # キーに紐づく秘密鍵



#nounceに入力する任意の変数を作成する関数
def randomname(n): 
   randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
   return ''.join(randlst)

#OauthのURLを作成する関数
def make_signature_hmac(http_method, parameter, uri, secret):
    #HTTPメソッドを決定
    http_method = http_method.upper()
    #parameterを作成する式
    if 'oauth_signature' in parameter:
        del parameter['oauth_signature']
    params = urllib.parse.urlencode(sorted(parameter.items(),key=lambda x:x[0]))
    #URIを作成
    parts = urllib.parse.urlparse(uri)
    scheme = parts.scheme if parts.scheme else 'http'
    port = '443' if scheme == 'https' else '80'
    host = parts.netloc
    path = parts.path
    uri = scheme + '://' + host + path
    # secret
    secret += '&'
    # base_string
    base_string = http_method + '&' + urllib.parse.quote(uri,'') + '&' + urllib.parse.quote(params,'')
    # oauth_signature
    signature = (hmac.new(secret.encode(), base_string.encode(), hashlib.sha1).digest())
    # base64エンコードを行う
    signature1 = base64.b64encode(signature)
    parameter['oauth_signature'] = signature1.decode()


#周辺道路リンク検索の関数(マルチポイント対応)
def drive_route_multi(latlon, range):
    #Oauthのパラメータを設定
    http_method = 'get'
    parameter = {
        'if_clientid'           : clientid,
        'if_auth_type'          : 'oauth',
        'oauth_consumer_key'    : clientid,
        'latlon'                : str(latlon), #緯度経度の羅列、複数ポイントでの出力が可能
        'range'                 : str(range),
        'datum'                 : 'WGS84',
        'adasinfo'              : 'T',
        'road_elevation_info'   : 'T',
        'multipoint'            : 'T',
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp'       : int(time.time()),
        'oauth_nonce'           : randomname(7), #任意の文字列
        'oauth_version'         : '1.0',
        'oauth_signature'       : ''
    }
    uri = 'https://test.core.its-mo.com/zmaps/api/apicore/core/v1_0/road/latlon/drive' #使用するAPI
    secret = secret_key                  # キーに紐づく秘密鍵
    make_signature_hmac(http_method, parameter, uri, secret)
    url = uri + '?' + urllib.parse.urlencode(parameter)
    req = urllib.request.Request(url)
    req.set_proxy("136.131.63.121:8082", "http")
    req.set_proxy("136.131.63.121:8082", "https")
    #結果の取得
    result = None
    try :
        result = urllib.request.urlopen( req ).read().decode('UTF-8')
    except ValueError :
        print('miss access')
    except IOError :
        print('miss acception')
        error_msg = f"Error 3: Unable to retrieve data from \"Itsumo NAVI API\""
        raise ValueError(error_msg)
    return result

#マップマッチングの関数※一度の入力点数は100点まで
def route_match(latlon):
    #Oauthのパラメータを設定
    http_method = 'get'
    parameter = {
        'if_clientid'           : clientid,
        'if_auth_type'          : 'oauth',
        'oauth_consumer_key'    : clientid,
        'latlon'                : str(latlon), #緯度経度の羅列、複数ポイントでの出力が可能
        'datum'                 : 'WGS84',
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp'       : int(time.time()),
        'oauth_nonce'           : randomname(7), #任意の文字列
        'oauth_version'         : '1.0',
        'oauth_signature'       : ''
    }
    uri = 'https://test.core.its-mo.com/zmaps/api/apicore/core/v1_0/road_path_drive' #使用するAPI
    secret = secret_key                  # キーに紐づく秘密鍵
    make_signature_hmac(http_method, parameter, uri, secret)
    url = uri + '?' + urllib.parse.urlencode(parameter)
    #結果の取得
    result = None
    try :
        result = urllib.request.urlopen( url ).read().decode('UTF-8')
    except ValueError :
        print('miss access')
    except IOError :
        print('miss acception')
        error_msg = f"Error 3: Unable to retrieve data from \"Itsumo NAVI API\""
        raise ValueError(error_msg)
    return result


#ルート検索の関数
def route_search(from_latlon,to_latlon,*mpoints):
    #経由地点をリスト化
    mpoints_d     = mpoints[0]
    for i in range(1,len(mpoints)):
        mpoints_d = mpoints_d + "," + mpoints[i]
    #経由地点の引き込みタイプ
    mpointstype_d = ["all"] if len(mpoints) >0 else []
    for i in range(len(mpoints)-1):
        mpointstype_d.append(",all")
    mpointstype_d = "".join(mpointstype_d)
    #Oauthのパラメータを設定
    http_method = 'get'
    parameter = {
        'if_clientid'           : clientid,
        'if_auth_type'          : 'oauth',
        'oauth_consumer_key'    : clientid,
        'searchType'            : '0',
        'mpointstype'           : mpointstype_d,
        'from'                  : str(from_latlon), #開始地点の緯度経度、"緯度,経度"で表現
        'to'                    : str(to_latlon), #終了地点の緯度経度、"緯度,経度"で表現
        'mpoints'               : str(mpoints_d), #終了地点の緯度経度、"緯度,経度"で表現
        'fromtype'              : 'all', #開始地点の緯度経度、"緯度,経度"で表現
        'totype'                : 'all', #終了地点の緯度経度、"緯度,経度"で表現
        'mpointstype'           : 'all', #終了地点の緯度経度、"緯度,経度"で表現
        'datum'                 : 'WGS84',
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp'       : int(time.time()),
        'oauth_nonce'           : randomname(7), #任意の文字列
        'oauth_version'         : '1.0',
        'oauth_signature'       : ''
    }
    uri = 'https://test.core.its-mo.com/zmaps/api/apicore/core/v1_0/route3/drive' #使用するAPI
    secret = secret_key                    # キーに紐づく秘密鍵
    make_signature_hmac(http_method, parameter, uri, secret)
    url = uri + '?' + urllib.parse.urlencode(parameter)
    #結果の取得
    result = None
    try :
        result = urllib.request.urlopen( url ).read().decode('UTF-8')
    except ValueError :
        print('miss access')
    except IOError :
        print('miss acception')
        error_msg = f"Error 3: Unable to retrieve data from \"Itsumo NAVI API\""
        raise ValueError(error_msg)
    return result