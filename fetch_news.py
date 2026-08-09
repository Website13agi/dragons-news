import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape

OUTPUT = "articles.json"

SOURCE_URL = "https://dragons.jp/"

JST = timezone(timedelta(hours=9))


def fetch_page(url):

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

        return response.read().decode(
            "utf-8",
            errors="ignore"
        )


def clean_text(text):

    if not text:
        return ""

    text = unescape(text)

    text = re.sub(
        r"<[^>]*>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def main():

    now = datetime.now(JST)

    one_week_ago = (
        now - timedelta(days=7)
    )

    html = fetch_page(
        SOURCE_URL
    )

    articles = {}

    pattern = re.compile(
        r"<a\b([^>]*)>(.*?)</a>",
        re.S | re.I
    )

    matches = pattern.findall(
        html
    )

    for attributes, inner_html in matches:

        href_match = re.search(
            r'href\s*=\s*["\']([^"\']+)["\']',
            attributes,
            re.I
        )

        if not href_match:
            continue

        url = href_match.group(1)

        text = clean_text(
            inner_html
        )

        if not text:
            continue


        # ==========================================
        # 中日スポーツの記事だけ
        # ==========================================

        if "sp.chunichi.co.jp/dra/news/" not in url:
            continue


        # ==========================================
        # 動画・映画系を除外
        # ==========================================

        if "/movie/" in url:
            continue


        # ==========================================
        # ドラゴンズ関連
        # ==========================================

        keywords = [
            "中日",
            "ドラゴンズ",
            "井上",
            "柳",
            "石伊",
            "斎藤",
            "田中幹也",
            "福永",
            "岡林",
            "細川",
            "石川",
            "村松",
            "松山",
            "金丸",
            "マラー",
            "今中",
        ]

        if not any(
            keyword in text
            for keyword in keywords
        ):
            continue


        # ==========================================
        # 日付
        # ==========================================

        date_match = re.search(
            r"2026/(\d{1,2})/(\d{1,2})",
            text
        )

        if not date_match:
            continue

        month = int(
            date_match.group(1)
        )

        day = int(
            date_match.group(2)
        )

        try:

            article_date = datetime(
                2026,
                month,
                day,
                12,
                0,
                0,
                tzinfo=JST
            )

        except ValueError:

            continue


        # ==========================================
        # 7日以内
        # ==========================================

        if article_date < one_week_ago:
            continue

        if article_date > now:
            continue


        # ==========================================
        # タイトル
        # ==========================================

        title = re.sub(
            r"2026/\d{1,2}/\d{1,2}",
            "",
            text
        )

        title = clean_text(
            title
        )

        if not title:
            continue


        # ==========================================
        # URL
        # ==========================================

        if url.startswith("/"):
            url = (
                "https://sp.chunichi.co.jp"
                + url
            )


        # ==========================================
        # 重複除去
        # ==========================================

        articles[url] = {

            "id": url,

            "title": title,

            "date":
                article_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "url": url,

            "source": "中日スポーツ"

        }


    # ==========================================
    # 最新順
    # ==========================================

    result = list(
        articles.values()
    )

    result.sort(
        key=lambda x: x["date"],
        reverse=True
    )


    # ==========================================
    # 最大100記事
    # ==========================================

    result = result[:100]


    # ==========================================
    # 保存
    # ==========================================

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
        "取得記事数:",
        len(result)
    )

    for article in result:

        print(
            article["date"],
            "|",
            article["title"],
            "|",
            article["url"]
        )


if __name__ == "__main__":
    main()
