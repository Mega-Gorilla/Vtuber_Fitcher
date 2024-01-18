import requests
from bs4 import BeautifulSoup

def search_channels(keyword='',gender=1,office=0,order=2,limit=500,non_movie=1,country=1):
    """
    Vtuberデータベースより、チャンネルを検索します。

    keyword: 検索ワード

    gender: 1-men/2-women/3-unknown/4-Babiniku/5-Femboy(男の娘)/6-bisexual(両性)/None-全選択

    office: 0-所属なし

    order: 1-Vtuber Post登録順 / 2-デビュー日新しい順 / 3-デビュー日古い順 / 4-総再生数多い順 / 5-総再生数少ない順 / 6-動画登録数の多い順 / 7-動画登録数の多い順 / 8-チャンネル登録者数多い順/ 9-チャンネル登録者数少ない順/ 10-投稿動画が新しい順/ 11-生放送が新しい順/ 12-活動頻度(1か月)
    
    limit: 検索件数

    non_movie: 1-動画ゼロ件を除外/0-動画ゼロ件を含める

    country: 1-日本/2-海外
    """

    # POSTリクエストのURL
    url = 'https://vtuber-post.com/database/index.php'

    gender_dict = {1: 'men', 2: 'women', 3: 'unknown', 4: 'Babiniku', 6: 'Femboy', 7: 'bisexual'}
    gender_str = gender_dict.get(gender, "unknown")

    # 送信するデータ (フォームデータ)
    data = {
        'keyword': keyword,
        'gender': gender,
        'office': office,
        'order': order, #1:Vtuber Post登録順 / 2:デビュー日新しい順 / 3:デビュー日古い順 / 4:総再生数多い順 / 5:総再生数少ない順 / 6:動画登録数の多い順 / 7:動画登録数の多い順 / 8:チャンネル登録者数多い順/ 9:チャンネル登録者数少ない順/ 10:投稿動画が新しい順/ 11:生放送が新しい順/ 12:活動頻度(1か月)
        'limit': limit,
        'non_movie': non_movie,
        'country': country,
        'prefectures[]': '',
        'genre[]': '',
        'model[]': '',
        'attribute[]': '',
        'creature[]': '',
        'job[]': '',
        'appearance[]': '',
        'collabo': '',
        'colabo_genre[]': '',
        'projects': '',
        'customer[]': '',
        'submit': '上記の条件で絞り込む',
        'searchFlg': '1',
        # 必要なフォームデータをここに追加...
    }

    # POSTリクエストを送信
    response = requests.post(url,data=data)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 各Vtuberの情報を含むdivタグを取得
    clipdata = soup.find('div', class_="vtuber_list heightLineParent clearfix")
    vtuber_divs = clipdata.find_all('div', class_='clearfix')


    # 結果を格納するためのリスト
    vtuber_list = []

    # 各Vtuberの情報を抽出
    for div in vtuber_divs:
        # 'name'クラスを持つpタグがある場合のみ処理を行う
        if div.find('p', class_='name') and div.find('p', class_='thumb'):
            #print("---"*50)
            #print(div)  # デバッグのためdivを出力
            name = div.find('p', class_='name').get_text(strip=True)
            id = div.find('p', class_='channel').find('a')['href'].replace('https://www.youtube.com/channel/','')
            channel_image_url = div.find('p', class_='thumb').find('img')['src']
            subscriber = div.find('p', class_='regist').get_text(strip=True)
            total_viewers = div.find('p', class_='play').get_text(strip=True)
            total_videos = div.find('p', class_='upload').get_text(strip=True)
            group = div.find('p', class_='group').get_text(strip=True)

            # 数値を整数に変換（「,」を除去してから変換）
            subscriber_num = int(subscriber.replace(',', '').replace('人', ''))
            total_viewers_num = int(total_viewers.replace(',', '').replace('回', ''))
            total_videos_num = int(total_videos.replace(',', '').replace('本', ''))

            # Vtuberの情報を辞書にしてリストに追加
            add_data={
                "id":id,
                "name": name,
                "gender":gender_str,
                "channel_image_url": channel_image_url,
                "subscriber": subscriber_num,
                "total_viewers": total_viewers_num,
                "total_videos": total_videos_num,
                "group": group
            }
            vtuber_list.append(add_data)
            print(add_data)

    print(f"{len(vtuber_list)} channels fetched.")
    return vtuber_list

if __name__ == '__main__':
    results = search_channels(limit=10)
    for result in results:
        print(result)