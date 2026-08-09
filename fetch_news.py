import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import html
import re

OUTPUT = "articles.json"
PEOPLE_FILE = "dragons_people.json"

# ==========================================
# Google News 検索
# ==========================================

SEARCH_QUERIES = [
    'site:chunichi.co.jp/chuspo ドラゴンズ',
    'site:chunichi.co.jp/chuspo "中日ドラゴンズ"',
    'site:chunichi.co.jp/chuspo "中日" 野球',
    'site:chunichi.co.jp/chuspo "2軍" 中日',
    'site:chunichi.co.jp/chuspo "ファーム" 中日',
    'site:chunichi.co.jp/chuspo "一軍" 中日',
]


# ==========================================
# Google News RSS取得
# ==========================================

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


# ==========================================
# HTML文字列をきれいにする
# ==========================================

def clean_text(text):

    if not text:
        return ""

    text = html.unescape(text)

    # HTMLタグを除去
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # 余分な空白を整理
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================
# 選手・首脳陣を読み込む
# ==========================================

def load_people():

    try:

        with open(
            PEOPLE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except Exception as error:

        print(
            "人物ファイル読み込みエラー:",
            error
        )

        return [], []


    players = data.get(
        "players",
        []
    )

    coaches = data.get(
        "coaches",
        []
    )

    return players, coaches


# ==========================================
# ドラゴンズ記事判定
# ==========================================

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

    # ======================================
    # ① ドラゴンズ固有語
    # ======================================

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


    # ======================================
    # ② 選手名
    # ======================================

    for name in players:

        if name and name in text:

            return True


    # ======================================
    # ③ 監督・コーチ名
    # ======================================

    for name in coaches:

        if name and name in text:

            return True


    # ======================================
    # ④ 「中日」＋野球関連語
    # ======================================

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


# ==========================================
# 中日スポーツ判定
# ==========================================

def is_chunichi_sports(
    source,
    source_url,
    title,
    description
):

    text = (
        source
        + " "
        + source_url
        + " "
        + title
        + " "
        + description
    )

    # Google Newsのsource名
    if "中日スポーツ" in source:
        return True

    # 英語表記など
    if "Chunichi Sports" in source:
        return True

    # URLに中日スポーツのパスが含まれる場合
    if "chunichi.co.jp/chuspo" in source_url:
        return True

    # 検索結果のタイトル・説明に
    # 中日スポーツが明記されている場合
    if "中日スポーツ" in text:
        return True

    return False


# ==========================================
# メイン処理
# ==========================================

def main():

    players, coaches = load_people()

    print(
        "選手:",
        len(players),
        "人"
    )

    print(
        "首脳陣:",
        len(coaches),
        "人"
    )


    articles = []


    total_rss = 0
    total_source = 0
    total_dragons = 0


    # ======================================
    # Google News RSSを複数検索
    # ======================================

    for query in SEARCH_QUERIES:

        print("")
        print(
            "======================================"
        )

        print(
            "検索:",
            query
        )

        try:

            data = fetch_rss(query)

            root = ET.fromstring(data)

        except Exception as error:

            print(
                "RSS取得エラー:",
                error
            )

            continue


        items = root.findall(
            ".//item"
        )

        print(
            "RSS取得記事数:",
            len(items)
        )

        total_rss += len(items)


        query_source_count = 0
        query_dragons_count = 0


        # ==================================
        # RSSの記事を処理
        # ==================================

        for item in items:

            title = clean_text(
                item.findtext(
                    "title",
                    ""
                )
            )


            url = clean_text(
                item.findtext(
                    "link",
                    ""
                )
            )


            date = clean_text(
                item.findtext(
                    "pubDate",
                    ""
                )
            )


            description = clean_text(
                item.findtext(
                    "description",
                    ""
                )
            )


            # ------------------------------
            # source
            # ------------------------------

            source_element = item.find(
                "source"
            )

            source = ""
            source_url = ""


            if source_element is not None:

                source = clean_text(
                    source_element.text
                    or ""
                )

                source_url = (
                    source_element.attrib.get(
                        "url",
                        ""
                    )
                )


            # ==================================
            # 中日スポーツ判定
            # ==================================

            if not is_chunichi_sports(
                source,
                source_url,
                title,
                description
            ):

                continue


            total_source += 1
            query_source_count += 1


            # ==================================
            # ドラゴンズ記事判定
            # ==================================

            if not is_dragons_article(
                title,
                description,
                players,
                coaches
            ):

                continue


            total_dragons += 1
            query_dragons_count += 1


            # ==================================
            # 記事追加
            # ==================================

            articles.append({

                "id": url,

                "title": title,

                "date": date,

                "url": url,

                "source": "中日スポーツ"

            })


        print(
            "中日スポーツ:",
            query_source_count
        )

        print(
            "ドラゴンズ記事:",
            query_dragons_count
        )


    # ==========================================
    # URLで重複除去
    # ==========================================

    unique_articles = {}

    for article in articles:

        article_id = article.get(
            "id",
            ""
        )

        if not article_id:
            continue

        unique_articles[
            article_id
        ] = article


    articles = list(
        unique_articles.values()
    )


    # ==========================================
    # 新しい記事を上にする
    # ==========================================

    articles.sort(
        key=lambda article:
            article.get(
                "date",
                ""
            ),
        reverse=True
    )


    # ==========================================
    # 最大100記事
    # ==========================================

    articles = articles[:100]


    # ==========================================
    # articles.jsonに保存
    # ==========================================

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


    # ==========================================
    # 結果表示
    # ==========================================

    print("")
    print(
        "======================================"
    )

    print(
        "Google News取得記事:",
        total_rss
    )

    print(
        "中日スポーツ記事:",
        total_source
    )

    print(
        "ドラゴンズ関連記事:",
        total_dragons
    )

    print(
        "重複除去後:",
        len(articles)
    )

    print(
        "articles.json:",
        len(articles),
        "記事"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()
