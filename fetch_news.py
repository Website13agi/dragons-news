import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape


OUTPUT = "articles.json"

JST = timezone(timedelta(hours=9))

SEARCH_QUERIES = [
    "site:chunichi.co.jp/article/ ドラゴンズ",
    "site:chunichi.co.jp/article/ 中日ドラゴンズ",
    "site:chunichi.co.jp/article/ 中日 野球",
]


def fetch_rss(query):

    params = urllib.parse.urlencode({
        "q": query,
        "format": "rss"
    })

    url = (
        "https://www.bing.com/news/search?"
        + params
    )

    print("")
    print("RSS URL:")
    print(url)

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

        data = response.read()

    print(
        "RSS取得:",
        len(data),
        "bytes"
    )

    return data


def clean_text(text):

    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def parse_date(text):

    if not text:
        return None

    try:

        date = parsedate_to_datetime(
            text
        )

        if date.tzinfo is None:

            date = date.replace(
                tzinfo=timezone.utc
            )

        return date.astimezone(JST)

    except Exception:

        return None


def extract_chunichi_url(text):

    if not text:
        return None

    # 通常のURL
    match = re.search(
        r"https?://www\.chunichi\.co\.jp/article/\d+",
        text
    )

    if match:
        return match.group(0)

    # HTML内にある場合
    match = re.search(
        r"https?://www\.chunichi\.co\.jp/article/\d+",
        unescape(text)
    )

    if match:
        return match.group(0)

    return None


def main():

    now = datetime.now(JST)

    one_week_ago = (
        now
        - timedelta(days=7)
    )

    print("================================")
    print("ドラゴンズニュース取得開始")
    print("現在時刻:", now)
    print("7日前:", one_week_ago)
    print("================================")


    articles = {}

    total_items = 0
    chunichi_urls = 0


    for query in SEARCH_QUERIES:

        print("")
        print("--------------------------------")
        print("検索:", query)
        print("--------------------------------")


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
                repr(error)
            )

            continue


        items = root.findall(
            ".//item"
        )

        print(
            "RSS記事数:",
            len(items)
        )

        total_items += len(items)


        for item in items:

            title = clean_text(
                item.findtext(
                    "title",
                    ""
                )
            )

            link = clean_text(
                item.findtext(
                    "link",
                    ""
                )
            )

            description = clean_text(
                item.findtext(
                    "description",
                    ""
                )
            )

            date_text = clean_text(
                item.findtext(
                    "pubDate",
                    ""
                )
            )

            source = clean_text(
                item.findtext(
                    "source",
                    ""
                )
            )


            print("")
            print("記事:")
            print(
                "タイトル:",
                title
            )
            print(
                "URL:",
                link
            )
            print(
                "日時:",
                date_text
            )
            print(
                "媒体:",
                source
            )


            # ==================================
            # 個別記事URLを探す
            # ==================================

            combined_text = (
                link
                + " "
                + description
            )

            article_url = extract_chunichi_url(
                combined_text
            )


            if article_url:

                chunichi_urls += 1

                print(
                    "★ 中日新聞URL発見:",
                    article_url
                )

            else:

                print(
                    "× 中日新聞URLなし"
                )

                continue


            # ==================================
            # 日付
            # ==================================

            article_date = parse_date(
                date_text
            )


            if article_date is None:

                print(
                    "× 日付を解析できません"
                )

                continue


            print(
                "解析日時:",
                article_date
            )


            # ==================================
            # 7日以内
            # ==================================

            if article_date < one_week_ago:

                print(
                    "× 7日より古い"
                )

                continue


            if article_date > now:

                print(
                    "× 未来の日付"
                )

                continue


            # ==================================
            # ドラゴンズ判定
            # ==================================

            text = (
                title
                + " "
                + description
            )


            keywords = [

                "中日ドラゴンズ",
                "ドラゴンズ",
                "中日",
                "竜",
                "バンテリンドーム",
                "ナゴヤ球場",

            ]


            is_dragons = any(
                keyword in text
                for keyword in keywords
            )


            if not is_dragons:

                print(
                    "× ドラゴンズ関連ではない"
                )

                continue


            # ==================================
            # 保存
            # ==================================

            articles[article_url] = {

                "id": article_url,

                "title": title,

                "date":
                    article_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "url": article_url,

                "source": "中日スポーツ"

            }


            print(
                "◎ 採用:"
                ,
                article_url
            )


    # ======================================
    # 新しい順
    # ======================================

    result = list(
        articles.values()
    )


    result.sort(
        key=lambda article:
            article["date"],
        reverse=True
    )


    # ======================================
    # 最大100件
    # ======================================

    result = result[:100]


    # ======================================
    # JSON保存
    # ======================================

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


    # ======================================
    # 結果
    # ======================================

    print("")
    print("================================")
    print("取得結果")
    print("================================")

    print(
        "RSS総記事数:",
        total_items
    )

    print(
        "中日新聞URL:",
        chunichi_urls
    )

    print(
        "採用記事数:",
        len(result)
    )


    print("")
    print("採用された記事:")

    for article in result:

        print(
            article["date"],
            "|",
            article["title"],
            "|",
            article["url"]
        )


    print("================================")


if __name__ == "__main__":
    main()
