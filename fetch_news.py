import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import html


OUTPUT = "articles.json"
PEOPLE_FILE = "dragons_people.json"


# 中日スポーツからドラゴンズ記事を探すための検索
SEARCH_QUERIES = [
    'site:chunichi.co.jp/chuspo ドラゴンズ',
    'site:chunichi.co.jp/chuspo "中日ドラゴンズ"',
    'site:chunichi.co.jp/chuspo "中日" 野球',
    'site:chunichi.co.jp/chuspo "2軍" 中日',
    'site:chunichi.co.jp/chuspo "ファーム" 中日',
    'site:chunichi.co.jp/chuspo "一軍" 中日',
]


def fetch_rss(query):

    params = urllib.parse.urlencode({
        "q": query,
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja"
    })

    url = (
        "https://news.google.com/rss/search?"
        + params
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return response.read()


def clean_text(text):

    if not text:
        return ""

    return html.unescape(text)


def load_people():

    with open(
        PEOPLE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    players = data.get(
        "players",
        []
    )

    coaches = data.get(
        "coaches",
        []
    )

    return players, coaches


def is_dragons_article(
    title,
    description,
    players,
    coaches
):

    text = (
        title
        + " "
        + description
    )

    # ==================================
    # ① ドラゴンズ固有語
    # ==================================

    strong_keywords = [
        "中日ドラゴンズ",
        "ドラゴンズ",
        "バンテリンドーム",
        "ナゴヤ球場",
        "若竜",
        "竜戦士",
        "竜党",
    ]

    for keyword in strong_keywords:

        if keyword in text:

            return True


    # ==================================
    # ② 選手名
    # ==================================

    for name in players:

        if name in text:

            return True


    # ==================================
    # ③ 監督・コーチ名
    # ==================================

    for name in coaches:

        if name in text:

            return True


    # ==================================
    # ④ 中日＋野球関連語
    # ==================================

    baseball_keywords = [

        "プロ野球",
        "セ・リーグ",
        "セリーグ",
        "野球",
        "投手",
        "打者",
        "先発",
        "中継ぎ",
        "抑え",
        "本塁打",
        "ホームラン",
        "安打",
        "三振",
        "登板",
        "打席",
        "出場選手登録",
        "登録抹消",
        "一軍",
        "1軍",
        "二軍",
        "2軍",
        "ファーム",
        "キャンプ",
        "オープン戦",
        "ドラフト",
        "練習試合",
        "交流戦",
        "クライマックスシリーズ",
        "CS",
    ]

    has_baseball = any(
        keyword in text
        for keyword in baseball_keywords
    )

    if (
        "中日" in text
        and has_baseball
    ):

        return True


    return False


def main():

    players, coaches = load_people()

    articles = []


    # ==================================
    # Google News RSSを複数検索
    # ==================================

    for query in SEARCH_QUERIES:

        try:

            data = fetch_rss(query)

            root = ET.fromstring(data)

        except Exception as error:

            print(
                "RSS取得エラー:",
                error
            )

            continue


        # ==================================
        # RSSの記事を処理
        # ==================================

        for item in root.findall(
            ".//item"
        ):

            title = clean_text(
                item.findtext(
                    "title",
                    ""
                )
            )

            url = item.findtext(
                "link",
                ""
            )

            date = item.findtext(
                "pubDate",
                ""
            )

            description = clean_text(
                item.findtext(
                    "description",
                    ""
                )
            )

            source_element = item.find(
                "source"
            )

            source = ""

            if source_element is not None:

                source = (
                    source_element.text
                    or ""
                )


            # ==================================
            # 中日スポーツだけを取得
            # ==================================

            if (
                "中日スポーツ"
                not in source
            ):

                continue


            # ==================================
            # ドラゴンズ関連か判定
            # ==================================

            if not is_dragons_article(
                title,
                description,
                players,
                coaches
            ):

                continue


            # ==================================
            # 記事を追加
            # ==================================

            articles.append({

                "id": url,

                "title": title,

                "date": date,

                "url": url,

                "source": "中日スポーツ"

            })


    # ==================================
    # URLで重複除去
    # ==================================

    unique_articles = {}

    for article in articles:

        unique_articles[
            article["id"]
        ] = article


    articles = list(
        unique_articles.values()
    )


    # ==================================
    # 新しい記事を上にする
    # ==================================

    articles.sort(
        key=lambda article:
            article["date"],
        reverse=True
    )


    # ==================================
    # 最大100記事
    # ==================================

    articles = articles[:100]


    # ==================================
    # articles.jsonに保存
    # ==================================

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            articles,
            file,
            ensure_ascii=False,
            indent=2
        )


    print(
        "取得したドラゴンズ記事:",
        len(articles)
    )


if __name__ == "__main__":
    main()
