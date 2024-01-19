from googleapiclient.discovery import build
from datetime import datetime, timedelta
from pymongo import MongoClient
import os,sys
import pytz

class Youtube_API_settings:
    youtube_api_key = os.getenv("GOOGLE_API_KEY")
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)

def get_cost():
    client = MongoClient()
    db = client["Youtube_DB"]
    collection = db["info"]
    static_cost = collection.find_one({"name":"youtubeAPI_info"})
    static_cost = static_cost['cost']
    return static_cost

def add_cost(cost):
    client = MongoClient()
    db = client["Youtube_DB"]
    collection = db["info"]

    API_info = collection.find_one({"name":"youtubeAPI_info"})
    static_cost = API_info['cost']
    date_str = API_info['date']
    date_object = datetime.strptime(date_str, "%Y-%m-%d").date()
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_datetime = datetime.now(pacific_tz)
    today_date = current_datetime.date()

    #日付が変わっていない場合は、加算
    if date_object == today_date:
        cost = static_cost + cost

    today_date_str = today_date.isoformat()

    new_values = {"$set": {"cost": cost,"date":today_date_str}}

    result = collection.update_one({"name":"youtubeAPI_info"}, new_values)
    return result

def search_youtube_playlist(part='snippet',id=None,playlistId=None):
    """
    id: id パラメータには、1 つ以上の一意の再生リスト アイテム ID をカンマ区切りのリストで指定します。
    playlistId: playlistId パラメータは、プレイリスト アイテムを取得するプレイリストの一意の ID を指定します。これはオプションのパラメータですが、プレイリスト アイテムを取得するすべてのリクエストで、id パラメータまたは playlistId パラメータの値を指定する必要があります。
    """
    parameters = {
        "part": part
        }
    if id != None:
        parameters.update({"id": id})
    if playlistId != None:
        parameters.update({"playlistId": playlistId})
    try:
        response = Youtube_API_settings.youtube.playlistItems().list(**parameters).execute()
    except Exception as e:
        print(f"An error occurred: {e}\nParameters: {parameters}")
        sys.exit(1)
    # Add cost
    add_cost(2)
    return response

def search_youtube(q=None,part='snippet',order='relevance',type=None,eventType=None,channelId=None,maxResults=50,region=None,relevanceLanguage=None,publishedAfter=None):
    """
    q: qパラメータは検索クエリを指定し、NOT（-）とOR（|）演算子を用いて動画を絞り込むことができます（例：boating|sailing、boating|sailing -fishing）。パイプ文字はURLエスケープが必要（%7C）

    type: 検索結果のタイプを指定します。video、channel、playlistのいずれか、またはこれらの組み合わせを指定できます。
    
    eventType: これをliveに設定すると、ライブストリームの検索結果のみを取得できます。他のオプションにはcompleted（終了したライブストリーム）やupcoming（今後のライブストリーム）があります。
    
    channelId: 特定のチャンネルに属するコンテンツを検索するために使用されます。
    
    regionCode: 特定の地域に基づいて検索結果を絞り込むために使用します。このコードはISO 3166-1 alpha-2形式の2文字の国コードです。('JP')
    
    publishedAfter: 検索日数範囲を設定します。未設定可能です
    
    regionCode: パラメータは、指定した国で視聴可能な動画の検索結果を返すように API に指示します。パラメータ値は ISO 3166-1 alpha-2 国コードです。
    
    relevanceLanguage: relevanceLanguage パラメータは、指定した言語に最も関連性の高い検索結果を返すように API に指示します。通常、パラメータ値は ISO 639-1 の 2 文字の言語コードです。ただし、簡体字中国語の場合は zh-Hans、繁体字中国語の場合は zh-Hant を使用する必要があります。なお、検索クエリとの関連性が高い場合、他の言語の結果が返されます。
    
    order: string order `order`はAPIの並べ替え方法を指定するパラメータで、デフォルトは関連性(`relevance`)です。利用可能な値には`date`（新しい順）、`rating`（評価順）、`title`（タイトル順）、`videoCount`（動画数順）、`viewCount`（視聴数順）があります。
    """
    parameters = {
        "part": part,
        "maxResults": maxResults,
        "order": order
        }
    if q != None:
        parameters.update({"q": q})
    if type != None:
        parameters.update({"type": type})
    if region != None:
        parameters.update({"regionCode": region})
    if relevanceLanguage != None:
        parameters.update({"relevanceLanguage": relevanceLanguage})
    if eventType != None:
        parameters.update({"eventType": eventType})
    if channelId != None:
        parameters.update({"channelId": channelId})
    if publishedAfter is not None:
        # UTCの現在時刻から指定された日数を引く
        date_in_the_past = datetime.utcnow() - timedelta(days=publishedAfter)
        # RFC 3339形式に変換（秒までの精度で、ミリ秒を除去）
        date_in_the_past_iso = date_in_the_past.strftime('%Y-%m-%dT%H:%M:%SZ')
        parameters.update({"publishedAfter": date_in_the_past_iso})
    try:
        response = Youtube_API_settings.youtube.search().list(**parameters).execute()
    except Exception as e:
        print(f"An error occurred: {e}\nParameters: {parameters}")
        sys.exit(1)
    # Add cost
    add_cost(100)
    return response

def channel_info_youtube(part= 'statistics',channel_id=None,forUsername=None):
    """
    parts:
        auditDetails: チャンネルのコミュニティガイドラインや著作権違反の監査情報。
        brandingSettings: チャンネルのブランディング設定（タイトル、説明、アイコン、バナーなど）。
        contentDetails: アップロードされた動画リストやプレイリストなど、チャンネルのコンテンツ詳細。
        contentOwnerDetails: YouTubeコンテンツパートナーに関連するチャンネルオーナー情報。
        id: チャンネルのID。
        localizations: 異なる言語でのチャンネル情報のローカライズ版。
        snippet: チャンネルの基本情報（名前、説明、作成日、サムネイル）。
        statistics: 登録者数、総視聴回数、動画数などのチャンネル統計。
        status: チャンネルの公開状態やコンテンツID状況。
        topicDetails: チャンネルが関連するトピック情報（FreebaseトピックIDなど）。

    Other Info: https://developers.google.com/youtube/v3/docs/channels/list?hl=ja&apix_params=%7B%22part%22%3A%5B%22statistics%22%5D%2C%22id%22%3A%5B%22UCxyEJ2PblLJDPxOkN_6ALLw%22%5D%7D
    """

    parameters = {
        "part":part
    }
    if channel_id != None:
        parameters.update({"id":channel_id})
    if forUsername != None:
        parameters.update({"forUsername":forUsername})
    try:
        response = Youtube_API_settings.youtube.channels().list(**parameters).execute()
    except Exception as e:
        print(f"An error occurred: {e}\nParameters: {parameters}")
        sys.exit(1)
    add_cost(1)
    return response


if __name__ == '__main__':
    live_channels = []
    #response = search_youtube(q="Vtuber",type="channel",maxResults=50,relevanceLanguage="ja",order='date')
    print(channel_info_youtube(part='statistics',channel_id="UCxyEJ2PblLJDPxOkN_6ALLw"))
    print(channel_info_youtube(part='statistics',channel_id="UCxyEJ2PblLJDPxOkN_6ALLw"))
    exit()
    for item in response['items']:
        print(item)
        channel_id = item['snippet']['channelId']
        print(f"search ChannelID:{channel_id}")
        # チャンネルIDを使って過去1か月のライブ配信を検索
        live_response = search_youtube(channelId=channel_id,type="video",eventType="completed",publishedAfter=30,maxResults=1,order='date')

        # ライブ配信があればチャンネルIDをリストに追加
        if live_response['items']:
            live_channels.append(channel_id)

    # ライブ配信を行ったチャンネルのIDを表示
    for channel in live_channels:
        print(channel)