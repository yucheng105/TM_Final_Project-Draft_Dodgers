import time
import json
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
# 讓頁面滾動到底（強化版）
# =====================================================
def scroll_to_bottom(driver, max_pause=3):
    last_height = driver.execute_script("return document.body.scrollHeight")
    stable_rounds = 0

    while True:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(1.5)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            stable_rounds += 1
        else:
            stable_rounds = 0

        if stable_rounds >= max_pause:
            break

        last_height = new_height


# =====================================================
# 自動展開留言、回覆（Threads 常見按鈕）
# =====================================================
def auto_expand(driver):

    expand_texts = [
        "View replies", "查看回覆",
        "Show all", "查看全部",
        "Show more", "顯示更多",
        "See more", "查看更多"
    ]

    for _ in range(3):  # 嘗試三輪展開
        buttons = driver.find_elements(By.TAG_NAME, "button")
        clicked = False
        for b in buttons:
            try:
                if any(t in b.text for t in expand_texts):
                    b.click()
                    time.sleep(1.2)
                    clicked = True
            except:
                pass

        if not clicked:
            break


# =====================================================
# 多重 selector：盡可能抓到留言 DOM
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

    collected = []
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for e in elements:
            if e not in collected:
                collected.append(e)

    return collected


# =====================================================
# 解析貼文
# =====================================================
def scrape_post(driver, url):
    print(f"\n開始爬取：{url}")
    driver.get(url)

    time.sleep(4)
    auto_expand(driver)
    scroll_to_bottom(driver)
    auto_expand(driver)

    # --- 抓貼文本體 ---
    try:
        post_text = driver.find_element(By.CSS_SELECTOR, "article div[dir='auto']").text
    except:
        post_text = ""

    comment_blocks = get_comment_blocks(driver)
    rows = []

    for block in comment_blocks:

        try:
            raw = block.text.strip()
        except:
            raw = ""

        if not raw:
            continue

        # 避開非留言（例如貼文自己）
        if len(raw) < 2:
            continue

        # 嘗試抓作者名稱
        try:
            author = block.find_element(By.CSS_SELECTOR, "span strong").text
        except:
            author = ""

        # 留言內容 = 整塊文本 + 移除作者
        content = raw.replace(author, "").strip()

        if len(content) == 0:
            continue

        rows.append({
            "post_url": url,
            "post_text": post_text,
            "comment_author": author,
            "comment_text": content
        })

    print(f"抓到 {len(rows)} 筆留言")
    return rows


# =====================================================
# 多藝人分類（同一留言可以出現在多 CSV）
# =====================================================
def classify_by_artist(df, artist_keywords):

    result = { artist: [] for artist in artist_keywords.keys() }

    for _, row in df.iterrows():
        text = row["comment_text"]

        for artist, keys in artist_keywords.items():
            if any(k in text for k in keys):
                result[artist].append(row.to_dict())

    return result


# =====================================================
# 主程式
# =====================================================
def main():

    # 讀取 URL 清單
    with open("urls.txt", "r", encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]

    # 讀取藝人關鍵字
    with open("artists.json", "r", encoding="utf-8") as f:
        artist_keywords = json.load(f)

    os.makedirs("output", exist_ok=True)

    driver = init_driver()
    driver.get("https://www.threads.net/login")
    input("請登入 Threads，登入完成後按 Enter 開始爬蟲...")

    all_rows = []

    for url in urls:
        rows = scrape_post(driver, url)
        all_rows.extend(rows)

    driver.quit()

    df = pd.DataFrame(all_rows)

    # --- 分類 ---
    classified = classify_by_artist(df, artist_keywords)

    # --- 輸出 CSV ---
    for artist, rows in classified.items():
        out_path = f"output/{artist}.csv"
        pd.DataFrame(rows).to_csv(out_path, encoding="utf-8-sig", index=False)
        print(f"已輸出：{out_path}（{len(rows)} 筆留言）")

    print("\n=== 爬蟲全部完成 ===")


if __name__ == "__main__":
    main()
