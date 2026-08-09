import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


OUTPUT = "articles.json"

BASE_URL = "https://www.chunichi.co.jp"
NEWS_URL = "https://www.chunichi.co.jp/chuspo"

JST = timezone(timedelta(hours=9))


def parse_date(text):
    """
    ページ内の日付表記を解析
    """

    if not text:
        return None

    patterns = [
        r"2026[年/-]\s*(\d{1,2})[月/-]\s*(\d{1,2})日?\s+(\d{1,2}):(\d{2})",
        r"(\d{4})[年/-]\s*(\d{1,2})[月/-]\s*(\d{1,2})日?\s+(\d{1,2}):(\d{2})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text
        )

        if match:

            groups = match.groups()

            if len(groups) == 4:

                year = 2026
                month, day, hour, minute = map(
                    int,
                    groups
                )

            else:

                year, month, day, hour, minute = map(
                    int,
                    groups
                )

            try:

                return datetime(
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    tzinfo=JST
                )

            except ValueError:

                return None

    return None


def clean_title(title):

    if not title:
        return ""

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


def main():

    now = datetime.now(JST)

    one_week_ago = (
        now
        - timedelta(days=7)
    )


    print(
        "現在時刻:",
        now.isoformat()
    )

    print(
        "取得対象:",
        one_week_ago.isoformat(),
        "以降"
    )


    articles = []

    seen_urls = set()


    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            locale="ja-JP"
        )


        print(
            "中日スポーツを取得中..."
        )


        page.goto(
            NEWS_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )


        page.wait_for_timeout(
            5000
        )


        # ==================================
        # ページ内の全リンクを取得
        # ==================================

        links = page.locator(
            "a"
        ).all()


        print(
            "リンク数:",
            len(links)
        )


        # ==================================
        # 個別記事URLを探す
        # ==================================

        for link in links:

            try:

                href = link.get_attribute(
                    "href"
                )

                title = link.inner_text()

            except Exception:

                continue


            if not href:
                continue


            href = urljoin(
                BASE_URL,
                href
            )


            # --------------------------------
            # 中日新聞社の個別記事だけ
            # --------------------------------

            if not re.search(
                r"https://www\.chunichi\.co\.jp/article/\d+",
                href
            ):

                continue


            title = clean_title(
                title
            )


            if not title:
                continue


            if href in seen_urls:
                continue


            seen_urls.add(
                href
            )


            # ==================================
            # 個別記事ページを開く
            # ==================================

            try:

                article_page = (
                    browser.new_page(
                        locale="ja-JP"
                    )
                )


                article_page.goto(
                    href,
                    wait_until="domcontentloaded",
                    timeout=30000
                )


                article_page.wait_for_timeout(
                    1000
                )


                # ------------------------------
                # ページテキスト
                # ------------------------------

                body_text = (
                    article_page
                    .locator("body")
                    .inner_text()
                )


                # ------------------------------
                # タイトル
                # ------------------------------

                page_title = (
                    article_page
                    .title()
                )


                if page_title:

                    page_title = clean_title(
                        page_title
                    )

                    if page_title:
                        title = page_title


                # ------------------------------
                # 日付
                # ------------------------------

                article_date = parse_date(
                    body_text
                )


                article_page.close()


            except Exception as error:

                print(
                    "記事取得エラー:",
                    href,
                    error
                )

                continue


            # ==================================
            # 日付が取得できなければ除外
            # ==================================

            if article_date is None:

                continue


            # ==================================
            # 7日より古ければ除外
            # ==================================

            if article_date < one_week_ago:

                continue


            # ==================================
            # 将来の日付も除外
            # ==================================

            if article_date > now:

                continue


            # ==================================
            # ドラゴンズ記事判定
            # ==================================

            dragons_keywords = [

                "中日",
                "ドラゴンズ",
                "井上",
                "バンテリンドーム",
                "ナゴヤ球場",
                "柳裕也",
                "細川成也",
                "石川昂弥",
                "福永裕基",
                "岡林勇希",
                "上林誠知",

            ]


            if not any(
                keyword in (
                    title
                    + " "
                    + body_text
                )
                for keyword in dragons_keywords
            ):

                continue


            # ==================================
            # 記事保存
            # ==================================

            articles.append({

                "id": href,

                "title": title,

                "date":
                    article_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                "url": href,

                "source": "中日スポーツ"

            })


            print(
                "取得:",
                article_date.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                title
            )


        browser.close()


    # ==========================================
    # 新しい順
    # ==========================================

    articles.sort(
        key=lambda article:
            article["date"],
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


    print("")
    print(
        "=============================="
    )

    print(
        "保存記事数:",
        len(articles)
    )

    print(
        "=============================="
    )


if __name__ == "__main__":

    main()
