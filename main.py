from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError,BulkWriteError
from vtuber_post import *
from youtube_api import *
import time

client = MongoClient()
db = client["Youtube_DB"]
collection = db["Vtubers"]

class config:
    sample_data_num = 1000
    youtube_API_limit = 10000

def Add_mongo_list(list_data):
    result_data = []
    data_count = 0
    for dict_data in list_data:
        try:
            insert_result = collection.insert_one(dict_data)
            result_dict = {
                "inserted_id": str(insert_result.inserted_id),  # ObjectIDを文字列に変換
                "acknowledged": insert_result.acknowledged
                }
            result_data.append(result_dict)
            data_count+=1
        except DuplicateKeyError as e:
            # 重複キーエラーが発生した場合の処理
            print(f"IDが重複したため代入されませんでした。 / {dict_data['name']} - {dict_data['id']}")
            result_dict = {"acknowledged":False,"Data":dict_data,"error":e.details}
            result_data.append(result_dict)
    print(f"{data_count} data added.")
    return result_dict

def get_new_channel_data(genders=[],limit=10):
    """
    新しいチャンネルデータを取得し、MongoDBに追加します
    男性・女性・バ美肉 のデータを取得します

    genders: 1-men/2-women/3-unknown/4-Babiniku/5-Femboy(男の娘)/6-bisexual(両性)
    例[1,2,4]

    limit: 取得データ数を設定します。取得データ数は性別ごとの取得数になります。
    """

    keys_to_remove = ["subscriber", "total_viewers", "total_videos"]
    results = []
    if genders == []:
        genders = [1,2,3,4,5,6]

    for gender in genders:  # 1: 男性, 2: 女性, 4: バ美肉
        # デビューが早い順でVTuberリストを検索
        vtuber_list = search_channels(gender=gender, order=2, limit=limit)
        # 不要なキーを削除してMongoDBに追加
        modi_vtuber_list = []
        for vtuber_dict in vtuber_list:
            modi_vtuber_list.append(dict_keys_to_remove(vtuber_dict, keys_to_remove))
        result = Add_mongo_list(modi_vtuber_list)
        results+= result
        # サーバーに負担をかけないように待機
        time.sleep(3)
    return results

def channel_gender_count(genders=[]):
    """
    DBにあるデータを性別別で取得し、各個数を返します。

    genders: 1-men/2-women/3-unknown/4-Babiniku/5-Femboy(男の娘)/6-bisexual(両性)
    例[1,2,4]

    返り値例:{'men': 844, 'women': 957, 'unknown': 0, 'Babiniku': 285, 'Femboy': 0, 'bisexual': 0}
    """
    if genders == []:
        genders = [1,2,3,4,5,6]
    gender_dict = {1: 'men', 2: 'women', 3: 'unknown', 4: 'Babiniku', 5: 'Femboy', 6: 'bisexual'}
    results = {}
    for gender in genders:
        gender_str = gender_dict.get(gender, "unknown")
        query = {
            "$and": [
                {"active": True},
                {"gender":gender_str}
            ]
        }
        count = collection.count_documents(query)
        results.update({gender_str:count})
    return results

def get_channel_info(channel_id):
    """
    YouTube APIを利用して、channel info を取得します。
    """
    if get_cost() >= 10000:
        print('Youtube API Cost Limit.')
        exit()
        
    channel_info = channel_info_youtube("snippet",channel_id=channel_id)
    name = channel_info["items"][0]["snippet"]["title"]
    description = channel_info["items"][0]["snippet"]["description"]
    publishedAt = channel_info["items"][0]["snippet"]["publishedAt"]
    channel_image_url = channel_info["items"][0]["snippet"]["thumbnails"]["high"]["url"]
    country = channel_info["items"][0]["snippet"].get("country", "none")
    return {"name":name,"description":description,"publishedAt":publishedAt,"channel_image_url":channel_image_url,"country":country}

def get_upload_info(channel_id):
    """
    チャンネルのアップロードされている動画一覧(50件)を取得します。取得されるのは動画作成日、タイトル、説明、サムネ等であり、統計データは取得されません。
    """
    if get_cost() >= 9900:
        print('Youtube API Cost Limit.')
        exit()

    #動画データを取得
    upload_data = search_youtube(channelId=channel_id,order='date',type='video')

    results = []
    for item in upload_data['items']:
        result = item["snippet"]
        result.update(item['id']) #kind videoIdの追加
        #更新日時の追加
        #current_datetime = datetime.utcnow()
        #result.update({'last_updated':current_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'})
        results.append(result)
    return {"upload_info":results}

def dict_keys_to_remove(dict_data,keys_to_remove):
    """
    辞書配列より指定された配列を消去します
    """
    for key in keys_to_remove:
        if key in dict_data:
            del dict_data[key]
    return dict_data

def update_channel_info(query,func):
    """
    query: DBをソートする条件を設定
    func: チャンネルidを代入して、DBに代入する配列を返す関数名を設定
    """
    results = collection.find(query)
    for result in results:
        id = result['id']
        info_data = func(id)
        collection.update_one({"id":result['id']},{"$set": info_data})
        print(f"updated: {id} - {result['name']}")

def days_between(d1, d2):
    """2つの日付文字列の間の日数を計算する"""
    d1 = datetime.strptime(d1, "%Y-%m-%dT%H:%M:%SZ")
    d2 = datetime.strptime(d2, "%Y-%m-%dT%H:%M:%SZ")
    return abs((d2 - d1).days)

if __name__ == '__main__':
    #result = collection.delete_many({})
    gender_dict = {
        'men': 1,
        'women': 2,
        'unknown': 3,
        'Babiniku': 4,
        'Femboy': 5,
        'bisexual': 6
    }

    # 各性別ごとにVtuberPostをソートして不足してサンプルデータが不足ている場合はチャンネルを探す
    gender_counts = channel_gender_count([1,2,4])
    for gender_str, count in gender_counts.items():
        if count < config.sample_data_num:
            gender_num = gender_dict.get(gender_str, 3)
            get_new_channel_data(genders=[gender_num],limit=500)
    
    #チャンネルデータでチャンネル情報を取得していないチャンネルについてはYoutubeAPIより詳細を取得する
    query = {
        "$and": [
            {"publishedAt": {"$exists": False}},  # publishedAt フィールドが存在しない
            {"$or": [
                {"gender": "men"},  # gender フィールドが "men" である
                {"gender": "women"},  # gender フィールドが "women" である
                {"gender": "Babiniku"}
            ]}
        ]
    }
    update_channel_info(query,get_channel_info)
    
    #upload_infoが存在しないDBデータにupload_infoを追記する
    query = {
        "$and": [
            {"upload_info": {"$exists": False}},
            {"$or": [
                {"gender": "men"},  # gender フィールドが "men" である
                {"gender": "women"},  # gender フィールドが "women" である
                {"gender": "Babiniku"}
            ]}
        ]
    }
    update_channel_info(query,get_upload_info)
    
    #更新頻度が週1以上かどうかをソートする
    query = {
        "$and": [
            {"upload_info": {"$exists": True}},
            {"active": {"$exists": False}},
            {"$or": [
                {"gender": "men"},
                {"gender": "women"},
                {"gender": "Babiniku"}
            ]}
        ]
    }
    searchs = collection.find(query)
    for search in searchs:
        upload_info = search["upload_info"]
        publish_times = [item["publishTime"] for item in upload_info]
        # 各ビデオ間の日数を計算し、7日以下かどうかを判定する
        result = True
        for i in range(len(publish_times) - 1):
            days_diff = days_between(publish_times[i], publish_times[i + 1])
            if (days_diff <= 7)==False:
                #更新頻度が7日以下であるとき
                result = False
                break
        collection.update_one({"id":search['id']},{"$set": {"active":result}})
        if result:
            print(f"{search['name']}は、週１にて更新されていることを確認しました。")