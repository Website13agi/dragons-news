import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


RSS_URL = (
    "https://news.google.com/rss/search?"
    + urllib.parse.urlencode({
        "q": 'site:chunichi.co.jp/chuspo "ドラゴンズ"',
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja"
    })
)

OUTPUT = "articles.json"


def fetch_rss():
    request = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:
        return response.read()


def main():

    data = fetch_rss()

    root = ET.fromstring(data)

    articles = []

    for item in root.findall(".//item"):

        title = item.findtext(
            "title",
            ""
        )

        url = item.findtext(
            "link",
            ""
        )

        date = item.findtext(
            "pubDate",
            ""
        )

        source_element = item.find(
            "source"
        )

        source = ""

        if source_element is not None:
            source = (
                source_element.text or ""
            )

        # タイトルにドラゴンズ関連語があるもの
        keywords = [
            "中日",
            "ドラゴンズ",
            "竜",
            "バンテリンドーム",
            "ナゴヤ球場"
        ]

        if not any(
            keyword in title
            for keyword in keywords
        ):
            continue

        articles.append({
            "id": url,
            "title": title,
            "date": date,
            "url": url,
            "source": source
        })

    # 重複除去
    unique = {}

    for article in articles:
        unique[
            article["id"]
        ] = article

    articles = list(
        unique.values()
    )

    # 新しい順
    articles.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    # 最大100件
    articles = articles[:100]

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            articles,
            f,
            ensure_ascii=False,
            indent=2
        )


if __name__ == "__main__":
    main()
