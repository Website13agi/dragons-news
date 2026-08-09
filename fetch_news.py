import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import html
import re

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


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

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

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

    # --------------------------------------
    # ドラゴンズ固有語
    # --------------------------------------

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


    # --------------------------------------
    # 選手名
    # --------------------------------------

    for name in players:

        if name and name in text:
            return True


    # --------------------------------------
    # 監督・コーチ名
    # --------------------------------------

    for name in coaches:

        if name and name in text:
            return True


    # --------------------------------------
    # 「中日」＋野球関連語
    # --------------------------------------

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

    if "中日スポーツ" in source:
        return True

    if "Chunichi Sports" in source:
        return True

    if "chunichi.co.jp/chuspo" in source_url:
        return True

    if "中日スポーツ" in text:
        return True

    return False


# ==========================================
# RSSの日付をdatetimeに変換
# ==========================================

def parse_article_date(date_text):

    try:

        article_date = parsedate_to_datetime(
            date_text
        )

        if article_date.tzinfo is None:

            article_date = article_date.replace(
                tzinfo=timezone.utc
            )

        return article_date.astimezone(
            timezone.utc
        )

    except Exception:

        return None


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


    # ======================================
    # 1週間前の時刻
    # ======================================

    now = datetime.now(
        timezone.utc
    )

    one_week_ago = (
        now
        - timedelta(days=7)
    )


    total_rss = 0
    total_source = 0
    total_dragons = 0
    total_recent = 0


    # ======================================
    # Google News RSSを検索
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

            data = fetch_rss(
                query
            )

            root = ET.fromstring(
                data
            )

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


        for item in items:

            # ==================================
            # 基本情報
            # ==================================

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


            # ==================================
            # 日付
            # ==================================

            article_date = parse_article_date(
                date
            )


            # 日付が取得できない記事は除外
            if article_date is None:

                continue


            # ==================================
            # 1週間より古い記事を除外
            # ==================================

            if article_date < one_week_ago:

                continue


            total_recent += 1


            # ==================================
            # source
            # ==================================

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
    # 最新記事順
    # ==========================================

    def sort_key(article):

        date = parse_article_date(
            article.get(
                "date",
                ""
            )
        )

        if date is None:

            return datetime.min.replace(
                tzinfo=timezone.utc
            )

        return date


    articles.sort(
        key=sort_key,
        reverse=True
    )


    # ==========================================
    # 最大100記事
    # ==========================================

    articles = articles[:100]


    # ==========================================
    # JSON保存
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
        "1週間以内の記事:",
        total_recent
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
        "最終保存記事:",
        len(articles)
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()
