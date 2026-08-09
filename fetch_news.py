import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape


OUTPUT = "articles.json"
PEOPLE_FILE = "dragons_people.json"

JST = timezone(timedelta(hours=9))


# ============================================================
# ニュース検索
# ============================================================

SEARCH_QUERIES = [

    "中日ドラゴンズ",

    "中日ドラゴンズ 一軍",

    "中日ドラゴンズ 二軍",

    "中日ドラゴンズ ファーム",

    "中日ドラゴンズ 投手",

    "中日ドラゴンズ 打者",

    "中日ドラゴンズ 若手",

]


# ============================================================
# HTTP取得
# ============================================================

def fetch(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return response.read()


# ============================================================
# 人名読み込み
# ============================================================

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


    def extract_names(items):

        names = []


        for item in items:

            if isinstance(
                item,
                str
            ):

                names.append(
                    item
                )

                continue


            if isinstance(
                item,
                dict
            ):

                # よくある形式
                for key in [
                    "name",
                    "player",
                    "coach",
                    "person"
                ]:

                    if key in item:

                        value = item[key]

                        if value:

                            names.append(
                                str(value)
                            )

                        break


        return names


    players = extract_names(
        players
    )

    coaches = extract_names(
        coaches
    )


    return (
        players,
        coaches
    )


# ============================================================
# HTML文字列をきれいにする
# ============================================================

def clean_text(text):

    if not text:

        return ""


    text = unescape(
        text
    )


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


# ============================================================
# ドラゴンズ度
# ============================================================

def dragons_score(
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


    score = 0


    # ========================================================
    # 最重要
    # ========================================================

    if "中日ドラゴンズ" in text:

        score += 100


    if "ドラゴンズ" in text:

        score += 90


    # ========================================================
    # 選手
    # ========================================================

    for name in players:

        if (
            name
            and name in text
        ):

            score += 80


    # ========================================================
    # 監督・コーチ
    # ========================================================

    for name in coaches:

        if (
            name
            and name in text
        ):

            score += 80


    # ========================================================
    # 球団固有語
    # ========================================================

    strong_words = [

        "バンテリンドーム",

        "ナゴヤ球場",

        "若竜",

        "竜戦士",

        "竜党",

        "中日・",

        "中日が",

        "中日を",

        "中日は",

        "中日、",

    ]


    for word in strong_words:

        if word in text:

            score += 40


    # ========================================================
    # 野球関連語
    #
    # 一軍・二軍は「条件」ではなく
    # 単なる補助情報
    # ========================================================

    baseball_words = [

        "野球",

        "プロ野球",

        "セ・リーグ",

        "セリーグ",

        "NPB",

        "投手",

        "打者",

        "先発",

        "中継ぎ",

        "抑え",

        "登板",

        "打席",

        "本塁打",

        "ホームラン",

        "安打",

        "三振",

        "一軍",

        "二軍",

        "1軍",

        "2軍",

        "ファーム",

        "育成",

        "登録",

        "抹消",

        "昇格",

        "降格",

        "キャンプ",

        "ドラフト",

        "オープン戦",

        "交流戦",

        "クライマックスシリーズ",

    ]


    baseball_count = 0


    for word in baseball_words:

        if word in text:

            baseball_count += 1


    score += (
        baseball_count * 5
    )


    # ========================================================
    # 「中日」だけの記事を除外しやすくする
    # ========================================================

    if (
        "中日" in text
        and score < 40
    ):

        score -= 100


    return score


# ============================================================
# RSS取得
# ============================================================

def fetch_rss(query):

    encoded = urllib.parse.quote(
        query
    )


    url = (
        "https://news.google.com/rss/search?"
        "q="
        + encoded
        + "&hl=ja&gl=JP&ceid=JP:ja"
    )


    data = fetch(
        url
    )


    root = ET.fromstring(
        data
    )


    return root.findall(
        ".//item"
    )


# ============================================================
# 日付
# ============================================================

def parse_date(value):

    if not value:

        return None


    formats = [

        "%a, %d %b %Y %H:%M:%S %z",

        "%a, %d %b %Y %H:%M %z",

        "%Y-%m-%dT%H:%M:%S%z",

        "%Y-%m-%dT%H:%M:%S",

    ]


    for fmt in formats:

        try:

            date = datetime.strptime(
                value.strip(),
                fmt
            )


            if date.tzinfo is None:

                date = date.replace(
                    tzinfo=JST
                )


            return date.astimezone(
                JST
            )


        except ValueError:

            continue


    return None


# ============================================================
# メイン
# ============================================================

def main():

    now = datetime.now(
        JST
    )


    one_week_ago = (
        now
        - timedelta(days=7)
    )


    players, coaches = load_people()


    print(
        "================================"
    )

    print(
        "Dragons News Fetcher"
    )

    print(
        "選手:",
        len(players)
    )

    print(
        "監督・コーチ:",
        len(coaches)
    )

    print(
        "================================"
    )


    articles = {}


    total = 0


    # ========================================================
    # 複数検索
    # ========================================================

    for query in SEARCH_QUERIES:

        print(
            "検索:",
            query
        )


        try:

            items = fetch_rss(
                query
            )


        except Exception as error:

            print(
                "RSS取得エラー:",
                error
            )

            continue


        total += len(
            items
        )


        # ====================================================
        # 各記事
        # ====================================================

        for item in items:

            title = clean_text(
                item.findtext(
                    "title",
                    ""
                )
            )


            description = clean_text(
                item.findtext(
                    "description",
                    ""
                )
            )


            url = item.findtext(
                "link",
                ""
            )


            date_text = item.findtext(
                "pubDate",
                ""
            )


            if not title:

                continue


            if not url:

                continue


            article_date = parse_date(
                date_text
            )


            if article_date is None:

                continue


            # =================================================
            # 7日以内
            # =================================================

            if article_date < one_week_ago:

                continue


            if article_date > now:

                continue


            # =================================================
            # ドラゴンズ度
            # =================================================

            score = dragons_score(

                title,

                description,

                players,

                coaches

            )


            print(
                "判定:",
                score,
                "|",
                title
            )


            # =================================================
            # 採用
            # =================================================
            #
            # 選手・監督・コーチ名
            # ドラゴンズ
            # 中日ドラゴンズ
            #
            # などを中心に採用
            # =================================================

            if score < 50:

                continue


            # =================================================
            # 重複除去
            # =================================================

            articles[url] = {

                "id": url,

                "title": title,

                "date":
                    article_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "url": url,

                "source": "ニュース",

                "score": score

            }


    # ========================================================
    # 新しい順
    # ========================================================

    result = list(
        articles.values()
    )


    result.sort(

        key=lambda article: (

            article["date"],

            article["score"]

        ),

        reverse=True

    )


    # ========================================================
    # 最大100件
    # ========================================================

    result = result[:100]


    # ========================================================
    # 保存
    # ========================================================

    with open(

        OUTPUT,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            result,

            file,

            ensure_ascii=False,

            indent=2

        )


    # ========================================================
    # 結果
    # ========================================================

    print("")

    print(
        "================================"
    )

    print(
        "RSS総記事数:",
        total
    )

    print(
        "採用記事数:",
        len(result)
    )

    print(
        "================================"
    )


    for article in result:

        print(
            article["date"],
            "|",
            article["score"],
            "|",
            article["title"]
        )

        print(
            article["url"]
        )


    print(
        "================================"
    )


if __name__ == "__main__":

    main()
