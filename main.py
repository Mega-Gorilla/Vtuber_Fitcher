from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError,BulkWriteError
from vtuber_post import *
import time

client = MongoClient()
db = client["Youtube_DB"]
collection = db["Vtubers"]

def Add_mongo_list(list_data):
    result_data = []
    for dict_data in list_data:
        try:
            insert_result = collection.insert_one(dict_data)
            result_dict = {
                "inserted_id": str(insert_result.inserted_id),  # ObjectIDを文字列に変換
                "acknowledged": insert_result.acknowledged
                }
            result_data.append(result_dict)
        except DuplicateKeyError as e:
            # 重複キーエラーが発生した場合の処理
            print(f"IDが重複したため代入されませんでした。 / {dict_data['name']} - {dict_data['id']}")
            result_dict = {"acknowledged":False,"Data":dict_data,"error":e.details}
            result_data.append(result_dict)
    return result_dict

if __name__ == '__main__':
    #男性+デビューが早い順
    man_vtuber_list = search_channels(gender=1,order=2,limit=1000)
    Add_mongo_list(man_vtuber_list)
    time.sleep(3)
    woman_vtuber_list = search_channels(gender=2,order=2,limit=1000)
    Add_mongo_list(woman_vtuber_list)