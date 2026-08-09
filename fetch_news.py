import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re


OUTPUT = "articles.json"

JST = timezone(timedelta(hours=9))

SEARCH_QUERIES = [
    'site:chunichi.co.jp/article/ ドラゴンズ',
    'site:chunichi.co.jp/article/ 中日ドラゴンズ',
    'site:chunichi.co.jp/article/ 中日 野球',
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


def main():

    now = datetime.now(JST)

    one_week_ago = (
        now
        - timedelta(days=7)
    )

    articles = {}

    for query in SEARCH_QUERIES:

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


        for item in root.findall(
            ".//item"
        ):

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

            date_text = clean_text(
                item.findtext(
                    "pubDate",
                    ""
                )
            )

            article_date = parse_date(
                date_text
            )


            if not article_date:

                continue


            # 7日以内
            if article_date < one_week_ago:

                continue


            # 未来の記事を除外
            if article_date > now:

                continue


            # 中日新聞社の個別記事URL
            match = re.search(
                r"https?://www\.chunichi\.co\.jp/article/\d+",
                url
            )

            if not match:

                continue


            article_url = match.group(0)


            # ドラゴンズ関連
            keywords = [
                "中日",
                "ドラゴンズ",
                "竜",
                "井上",
                "バンテリン",
                "ナゴヤ球場"
            ]


            if not any(
                word in title
                for word in keywords
            ):

                continue


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


    # 新しい順
    result = sorted(
        articles.values(),
        key=lambda x: x["date"],
        reverse=True
    )


    # 最大100記事
    result = result[:100]


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


    print(
        "保存記事数:",
        len(result)
    )


if __name__ == "__main__":
    main()
