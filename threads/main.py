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
# 初始化瀏覽器
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
# 滾動頁面到底部（強化版）
# =====================================================
def scroll_to_bottom(driver, max_pause=3):
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

        if stable_rounds >= max_pause:
            break

        last_height = new_height


# =====================================================
# 自動展開留言按鈕
# =====================================================
def auto_expand(driver):

    expand_keywords = [
        "View replies", "查看回覆",
        "View all", "查看全部",
        "Show more", "顯示更多",
        "See more", "查看更多",
        "See translation", "查看翻譯"
    ]

    buttons = driver.find_elements(By.TAG_NAME, "button")
    for b in buttons:
        try:
            if any(k in b.text for k in expand_keywords):
                b.click()
                time.sleep(1)
        except:
            pass


# =====================================================
# 多 selector：抓貼文內文
# =====================================================
def get_post_text(driver):

    selectors = [
        "article div[dir='auto']",
        "article span[dir='auto']",
        "div[role='article'] div[dir='auto']",
        "div.x1lliihq",
        "div.x1fc57z9",
        "div.x16md31u",
    ]

    texts = []

    for sel in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        for e in elements:
            try:
                t = e.text.strip()
                if len(t) > 6:  # 避免抓到 icon、空元素
                    texts.append(t)
            except:
                pass

    if not texts:
        return ""

    # 去重複並合併段落
    full = "\n".join(list(dict.fromkeys(texts)))
    return full


# =====================================================
# 多 selector：抓留言區塊
# =====================================================
def get_comment_blocks(driver):

    selectors = [
        "div[role='article']",
        "div[data-pressable-container='true']",
        "ul li",
        "div.x1lliihq",
        "div.x1fc57z9",
        "div[dir='ltr']",
        "div[dir='auto']"
    ]

    blocks = []
    for sel in selectors:
        found = driver.find_elements(By.CSS_SELECTOR, sel)
        for e in found:
            if e not in blocks:
                blocks.append(e)

    return blocks


# =====================================================
# 解析單篇貼文：回傳 → 貼文全文 + 全部留言
# =====================================================
def scrape_post(driver, url):
    print(f"\n開始爬取：{url}")
    driver.get(url)

    time.sleep(4)
    auto_expand(driver)
    scroll_to_bottom(driver)
    auto_expand(driver)

    # -------- 抓貼文本體 --------
    post_text = get_post_text(driver)

    # -------- 抓留言 --------
    blocks = get_comment_blocks(driver)
    comments = []

    for blk in blocks:
        raw = blk.text.strip()
        if not raw:
            continue
        
        # --- 嘗試抓作者 ---
        try:
            author = blk.find_element(By.CSS_SELECTOR, "span strong").text
        except:
            author = ""

        # --- 時間（YYYY-MM-DD） ---
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
        comment_time = date_match.group(0) if date_match else ""

        # --- 清理 message ---
        cleaned = raw
        if author:
            cleaned = cleaned.replace(author, "")
        if comment_time:
            cleaned = cleaned.replace(comment_time, "")

        comment_text = cleaned.strip()
        if len(comment_text) == 0:
            continue

        comments.append({
            "post_url": url,
            "post_text": post_text,
            "comment_author": author,
            "comment_time": comment_time,
            "comment_text": comment_text
        })

    print(f"抓到 {len(comments)} 則留言")

    return {
        "post_url": url,
        "post_text": post_text,
        "comments": comments
    }


# =====================================================
# 貼文分類邏輯：依「貼文內文」決定歸屬藝人
# =====================================================
def classify_post_by_artist(posts, artist_keywords):

    result = { artist: [] for artist in artist_keywords.keys() }

    for post in posts:
        text = post["post_text"]

        for artist, keywords in artist_keywords.items():
            # 貼文內文有提到該藝人？
            if any(k in text for k in keywords):
                # 整篇加入該藝人（包含全部留言）
                result[artist].extend(post["comments"])

    return result


# =====================================================
# 主程式
# =====================================================
def main():

    # --- 載入 URLs ---
    with open("urls.txt", "r", encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]

    # --- 載入藝人關鍵字 ---
    with open("artists.json", "r", encoding="utf-8") as f:
        artist_keywords = json.load(f)

    os.makedirs("output", exist_ok=True)

    driver = init_driver()
    driver.get("https://www.threads.net/login")
    input("\n請登入 Threads 後按 Enter 開始爬蟲...\n")

    all_posts = []

    for url in urls:
        data = scrape_post(driver, url)
        all_posts.append(data)

    driver.quit()

    # =====================================================
    # 輸出全部留言（不分類）
    # =====================================================
    all_comments = []
    for post in all_posts:
        all_comments.extend(post["comments"])

    df_all = pd.DataFrame(all_comments)
    df_all.to_csv("output/all_comments.csv", encoding="utf-8-sig", index=False)
    print(f"\n已輸出：output/all_comments.csv（共 {len(df_all)} 則留言）")


    # =====================================================
    # 依「貼文全文」分類至藝人 CSV
    # =====================================================
    classified = classify_post_by_artist(all_posts, artist_keywords)

    for artist, rows in classified.items():
        outpath = f"output/{artist}.csv"
        pd.DataFrame(rows).to_csv(outpath, encoding="utf-8-sig", index=False)
        print(f"已輸出：{outpath}（{len(rows)} 則留言）")

    print("\n=== 爬蟲全部完成 ===")


if __name__ == "__main__":
    main()
