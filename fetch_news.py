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
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/131.0 Safari/537.36"
            )
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


def absolute_url(url):

    if url.startswith("//"):
        return "https:" + url

    if url.startswith("/"):
        return "https://dragons.jp" + url

    return url


def main():

    now = datetime.now(JST)

    one_week_ago = (
        now - timedelta(days=7)
    )

    print(
        "中日ドラゴンズ公式サイト取得開始"
    )

    print(
        "現在:",
        now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    try:

        html = fetch_page(
            SOURCE_URL
        )

    except Exception as error:

        print(
            "取得エラー:",
            error
        )

        return


    print(
        "HTML取得:",
        len(html),
        "bytes"
    )


    articles = {}

    # ==================================================
    # aタグをすべて取得
    # ==================================================

    pattern = re.compile(
        r"<a\b([^>]*)>(.*?)</a>",
        re.S | re.I
    )


    matches = pattern.findall(
        html
    )


    print(
        "リンク数:",
        len(matches)
    )


    # ==================================================
    # 「中スポ」周辺から記事を取得
    # ==================================================

    for attributes, inner_html in matches:

        # ----------------------------------------------
        # href
        # ----------------------------------------------

        href_match = re.search(
            r'href\s*=\s*["\']([^"\']+)["\']',
            attributes,
            re.I
        )

        if not href_match:
            continue


        url = href_match.group(1)

        url = absolute_url(
            url
        )


        # ----------------------------------------------
        # sp.chunichi.co.jp の記事だけ
        # ----------------------------------------------

        if "sp.chunichi.co.jp" not in url:
            continue


        # ----------------------------------------------
        # リンク本文
        # ----------------------------------------------

        text = clean_text(
            inner_html
        )


        if not text:
            continue


        # ==================================================
        # 中スポ記事の日付
        #
        # 例:
        # 2026/08/09
        # ==================================================

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
                23,
                59,
                59,
                tzinfo=JST
            )

        except ValueError:

            continue


        # ==================================================
        # 7日以内
        # ==================================================

        if article_date < one_week_ago:
            continue


        if article_date > now + timedelta(days=1):
            continue


        # ==================================================
        # タイトル
        # ==================================================

        title = re.sub(
            r"2026/\d{1,2}/\d{1,2}",
            "",
            text
        )


        title = re.sub(
            r"中日ドラゴンズニュース",
            "",
            title
        )


        title = re.sub(
            r"井上監督ポジ語録",
            "",
            title
        )


        title = clean_text(
            title
        )


        if not title:
            continue


        # ==================================================
        # 取得
        # ==================================================

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


        print(
            "取得:",
            title
        )

        print(
            "URL:",
            url
        )


    # ==================================================
    # 最新順
    # ==================================================

    result = list(
        articles.values()
    )


    result.sort(
        key=lambda x: x["date"],
        reverse=True
    )


    # ==================================================
    # 最大100件
    # ==================================================

    result = result[:100]


    # ==================================================
    # JSON保存
    # ==================================================

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


    print("")
    print(
        "=============================="
    )

    print(
        "取得記事数:",
        len(result)
    )

    print(
        "=============================="
    )


if __name__ == "__main__":
    main()
