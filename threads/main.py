import time
import json
import os
import re
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


# =====================================================
# Selenium 初始化
# =====================================================
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)


# =====================================================
# 讓畫面向下捲到讀完
# =====================================================
def scroll_to_bottom(driver, max_pause_rounds=3):
    last_height = driver.execute_script("return document.body.scrollHeight")
    stable_rounds = 0

    while True:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(1.2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stable_rounds += 1
        else:
            stable_rounds = 0

        if stable_rounds >= max_pause_rounds:
            break

        last_height = new_height


# =====================================================
# 嘗試把「展開留言 / 更多」按鈕點開
# =====================================================
def auto_expand(driver):
    keywords = [
        "View replies", "查看回覆",
        "View all", "查看全部",
        "Show more", "顯示更多",
        "See more", "查看更多",
    ]
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for b in buttons:
        try:
            if any(k in b.text for k in keywords):
                b.click()
                time.sleep(1)
        except Exception:
            pass


# =====================================================
# 把尾巴那串 2 3 11 14 之類的數字清掉
# =====================================================
def strip_trailing_numbers(text: str) -> str:
    # 例如："... 他是練習曲 2,375 9 11 14" -> 把最後幾組純數字拿掉
    return re.sub(r"(?:\s+[0-9,]+)+\s*$", "", text).strip()


# =====================================================
# 抓「貼文主文」：保留分段
# =====================================================
def get_post_text(driver):
    # 觀察 DOM：貼文主文出現在 span，class 會包含 x1plvlek / x1lliihq 等
    spans = driver.find_elements(
        By.XPATH,
        "//span[contains(@class,'x1plvlek') or contains(@class,'x1lliihq')]"
    )

    chunks = []
    for s in spans:
        try:
            t = s.text.strip()
        except Exception:
            t = ""
        # 過濾掉太短、或只有圖示的文字
        if len(t) >= 4:
            chunks.append(t)

    # 去重複，維持順序
    seen = set()
    unique_chunks = []
    for c in chunks:
        if c not in seen:
            seen.add(c)
            unique_chunks.append(c)

    if not unique_chunks:
        return ""

    # 依照你的要求：保留分段，用換行連接
    return "\n".join(unique_chunks)


# =====================================================
# 取得所有可能含留言文字的大區塊
# =====================================================
def get_comment_blocks(driver):
    selectors = [
        "div[role='article']",
        "div[data-pressable-container='true']",
        "ul li",
        "div.x1lliihq",
        "div[dir='auto']",
    ]
    blocks = []
    for sel in selectors:
        for e in driver.find_elements(By.CSS_SELECTOR, sel):
            if e not in blocks:
                blocks.append(e)
    return blocks


# =====================================================
# 解析單一 Threads 貼文：貼文主文 + 所有留言
# =====================================================
def scrape_post(driver, url: str):
    print(f"\n開始爬取：{url}")
    driver.get(url)

    time.sleep(4)
    auto_expand(driver)
    scroll_to_bottom(driver)
    auto_expand(driver)

    # ---------- 貼文主文 ----------
    post_text = get_post_text(driver)

    # ---------- 抓留言 ----------
    date_pat = re.compile(r"\d{4}-\d{2}-\d{2}")
    blocks = get_comment_blocks(driver)
    comments = []

    # 若之後需要 fallback，用來候補當作貼文主文
    fallback_post_text = ""

    for blk in blocks:
        try:
            raw = blk.text.strip()
        except Exception:
            raw = ""
        if not raw:
            continue

        # 找日期，沒有日期的大多不是留言
        m = date_pat.search(raw)
        if not m:
            continue

        comment_time = m.group(0)
        before = raw[:m.start()].strip()
        after = raw[m.end():].strip()

        # 作者 = 日期前面的第一個 token
        author_tokens = before.split()
        comment_author = author_tokens[0] if author_tokens else ""

        # 留言內容 = 日期後面的文字，把尾巴數字清掉
        comment_text = strip_trailing_numbers(after)

        # 若貼文主文抓不到，第一個比較長的 after 可當作貼文主文 fallback
        if not post_text and not fallback_post_text and len(comment_text) >= 10:
            fallback_post_text = comment_text

        if not comment_text:
            continue

        comments.append(
            {
                "post_url": url,
                "post_text": None,  # 先佔位，稍後填入真正貼文文字
                "comment_author": comment_author,
                "comment_time": comment_time,
                "comment_text": comment_text,
            }
        )

    # 如果前面沒抓到 post_text，就用 fallback
    if not post_text and fallback_post_text:
        post_text = fallback_post_text

    # 把 post_text 寫回每一筆留言
    for c in comments:
        c["post_text"] = post_text

    print(f"抓到 {len(comments)} 則留言")
    return {
        "post_url": url,
        "post_text": post_text,
        "comments": comments,
    }


# =====================================================
# 依「貼文主文」決定這篇貼文要分給哪些藝人
# （一篇可以分給多個藝人）
# =====================================================
def classify_posts_by_artist(posts, artist_keywords):
    result = {artist: [] for artist in artist_keywords.keys()}

    for post in posts:
        post_text = post["post_text"] or ""
        comments = post["comments"]

        for artist, keywords in artist_keywords.items():
            # 貼文主文是否提到該藝人的任何一個關鍵字？
            if any(k in post_text for k in keywords):
                # 這篇貼文的所有留言都放進該藝人
                result[artist].extend(comments)

    return result


# =====================================================
# 主程式
# =====================================================
def main():
    # -------- 讀取 URL 清單 --------
    with open("urls.txt", "r", encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]

    # -------- 讀取藝人關鍵字 --------
    # 例如：
    # {
    #   "王大陸": ["王大陸"],
    #   "坤達": ["坤達", "謝坤達"],
    #   ...
    # }
    with open("artists.json", "r", encoding="utf-8") as f:
        artist_keywords = json.load(f)

    os.makedirs("output", exist_ok=True)

    driver = init_driver()
    driver.get("https://www.threads.net/login")
    input("\n請在彈出的視窗登入 Threads，登入完成後回到這裡按 Enter 繼續...\n")

    all_posts = []

    for url in urls:
        try:
            data = scrape_post(driver, url)
            all_posts.append(data)
        except Exception as e:
            print(f"爬取 {url} 時發生錯誤：{e}")

    driver.quit()

    # -------- 整理全部留言，輸出 all_comments.csv --------
    all_comments = []
    for post in all_posts:
        all_comments.extend(post["comments"])

    df_all = pd.DataFrame(all_comments)
    all_comments_path = os.path.join("output", "all_comments.csv")
    df_all.to_csv(all_comments_path, encoding="utf-8-sig", index=False)
    print(f"\n已輸出：{all_comments_path}（共 {len(df_all)} 則留言）")

    # -------- 依貼文主文分類到各藝人 --------
    classified = classify_posts_by_artist(all_posts, artist_keywords)

    for artist, rows in classified.items():
        out_path = os.path.join("output", f"{artist}.csv")
        pd.DataFrame(rows).to_csv(out_path, encoding="utf-8-sig", index=False)
        print(f"已輸出：{out_path}（{len(rows)} 則留言）")

    print("\n=== 全部完成 ===")


if __name__ == "__main__":
    main()
