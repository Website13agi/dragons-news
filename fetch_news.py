import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape

OUTPUT = "articles.json"

NEWS_URL = "https://www.chunichi.co.jp/chuspo"

JST = timezone(timedelta(hours=9))


def fetch_page(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=30
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="ignore"
        )


def clean_text(text):
    text = unescape(text)
    text = re.sub(
        r"<[^>]*>",
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
    patterns = [
        r"2026年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})",
        r"2026/(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})",
        r"2026-(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{2})",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text
        )

        if match:
            month, day, hour, minute = map(
                int,
                match.groups()
            )

            try:
                return datetime(
                    2026,
                    month,
                    day,
                    hour,
                    minute,
                    tzinfo=JST
                )
            except ValueError:
                pass

    return None


def extract_articles(html):

    articles = []

    # /article/数字 のリンクをすべて取得
    pattern = re.compile(
        r'href=["\']([^"\']*/article/\d+)["\']'
        r'[^>]*>(.*?)</a>',
        re.S | re.I
    )

    for match in pattern.finditer(html):

        url = match.group(1)
        inner = match.group(2)

        if url.startswith("/"):
            url = "https://www.chunichi.co.jp" + url

        title = clean_text(inner)

        if not title:
            continue

        articles.append({
            "url": url,
            "title": title
        })

    return articles


def main():

    print("中日スポーツ取得開始")

    try:
        html = fetch_page(
            NEWS_URL
        )
    except Exception as error:
        print(
            "ページ取得失敗:",
            error
        )

        return

    print(
        "HTML取得:",
        len(html),
        "bytes"
    )

    candidates = extract_articles(
        html
    )

    print(
        "記事候補:",
        len(candidates)
    )

    now = datetime.now(JST)

    one_week_ago = (
        now
        - timedelta(days=7)
    )

    articles = []
    seen = set()

    for article in candidates:

        url = article["url"]

        if url in seen:
            continue

        seen.add(url)

        title = article["title"]

        # ----------------------------------
        # ドラゴンズ関連判定
        # ----------------------------------

        keywords = [
            "中日",
            "ドラゴンズ",
            "竜",
            "バンテリンドーム",
            "ナゴヤ球場",
        ]

        if not any(
            keyword in title
            for keyword in keywords
        ):
            continue

        # ----------------------------------
        # 周辺HTMLから日付を探す
        # ----------------------------------

        position = html.find(url)

        if position == -1:
            continue

        surrounding = html[
            max(0, position - 1500):
            position + 1500
        ]

        article_date = parse_date(
            surrounding
        )

        if article_date is None:
            continue

        # ----------------------------------
        # 7日以内
        # ----------------------------------

        if article_date < one_week_ago:
            continue

        if article_date > now:
            continue

        articles.append({
            "id": url,
            "title": title,
            "date": article_date.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "url": url,
            "source": "中日スポーツ"
        })

    # --------------------------------------
    # 最新順
    # --------------------------------------

    articles.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    # --------------------------------------
    # 最大100件
    # --------------------------------------

    articles = articles[:100]

    # --------------------------------------
    # 保存
    # --------------------------------------

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
        "保存記事数:",
        len(articles)
    )


if __name__ == "__main__":
    main()
