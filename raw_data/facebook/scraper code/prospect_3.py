import time
import csv
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ------------------------------------------------
# 啟動 Selenium
# ------------------------------------------------
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
driver = webdriver.Chrome(options=options)

# ------------------------------------------------
# 進入貼文網址
# ------------------------------------------------
POST_URL = "https://www.facebook.com/lefthere036/posts/pfbid02p6akqs7knutGbe96utxdvV5SYNZ41bTyGjUeBiqTN94KLTHXzEKpQWeFfJ9zaCz4l"
driver.get(POST_URL)

input("登入好請按任意鍵： ")


# ------------------------------------------------
# CSV：初始化
# ------------------------------------------------
csv_file = open("fb_comments.csv", "a", newline="", encoding="utf-8-sig")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["comment_id", "author", "content"])


# ------------------------------------------------
# 工具函式：產生唯一 ID
# ------------------------------------------------
def make_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ------------------------------------------------
# 找到留言區（Facebook 的留言區並沒有固定 selector，需要等待第一則留言出現）
# ------------------------------------------------
def find_comment_section():
    print("尋找評論區域...")

    # ==========================
    # 1️⃣ 優先使用你找到的 scroll container suspect
    # ==========================
    suspect_selector = (
        "//div[contains(@class, 'x14z9mp') and "
        "contains(@class,'xat24cr') and "
        "contains(@class,'x1lziwak') and "
        "contains(@class,'xexx8yu') and "
        "contains(@class,'xyri2b') and "
        "contains(@class,'x18d9i69') and "
        "contains(@class,'x1c1uobl') and "
        "contains(@class,'x1gslohp')]"
    )

    suspect_sections = driver.find_elements(By.XPATH, suspect_selector)
    for i, sec in enumerate(suspect_sections):
        if sec.is_displayed() and sec.size["height"] > 200:
            print(f"找到疑似留言區 scroll container：#{i+1} 高度={sec.size['height']}")
            return sec

    # ==========================
    # 2️⃣ 第二優先：常見的留言 scroll container (x1n2onr6)
    # ==========================
    primary_selector = "//div[contains(@class,'x1n2onr6')]"
    sections = driver.find_elements(By.XPATH, primary_selector)

    for i, sec in enumerate(sections):
        try:
            if sec.is_displayed() and sec.size["height"] > 200:

                print(f"找到主要評論區域: {i+1}, 高度={sec.size['height']}")

                # 測試這個元素是否真的能滾動
                before = driver.execute_script("return arguments[0].scrollTop;", sec)
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", sec)
                time.sleep(0.3)
                after = driver.execute_script("return arguments[0].scrollTop;", sec)

                if after > before:
                    print(" → 確認此元素可滾動 ✔")
                    return sec
                else:
                    print(" → 此元素不可滾動，跳過 ✘")

        except Exception as e:
            continue

    print("主要評論區域未找到，退回次要搜尋...")

    # ==========================
    # 3️⃣ fallback selectors
    # ==========================

    fallback_selectors = [
        # 這兩個 class 幾乎必定出現在真正 scroll container
        "//div[contains(@class,'x78zum5') and contains(@class,'x1n2onr6')]",
        "//div[contains(@class,'x1n2onr6')]",
    ]

    for selector in fallback_selectors:
        sections = driver.find_elements(By.XPATH, selector)
        for sec in sections:
            try:
                if sec.is_displayed() and sec.size["height"] > 150:
                    print(f"fallback 找到區域，高度={sec.size['height']}")
                    return sec
            except:
                continue

    print("最終未找到特定區域，使用全局滾動")
    return None


# ------------------------------------------------
# 展開留言 / 回覆
# ------------------------------------------------
def expand_all_buttons():
    '''changed = False

    # 所有可能的展開按鈕文字（繁中 + 英文）
    keywords = [
        "查看其他", "查看之前", "查看更多", "更多回覆",
        "View more", "View previous", "See more"
    ]

    for text in keywords:
        buttons = driver.find_elements(By.XPATH, f"//span[contains(text(), '{text}')]")

        for btn in buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.3)
                btn.click()
                time.sleep(1)
                changed = True
            except:
                pass

    return changed'''
    changed = False

    # 尋找所有可能的展開按鈕
    button_selectors = [
        # 展開回覆
        "//span[contains(text(), '則回覆')]/ancestor::div[@role='button']",
        "//span[contains(text(), '条回复')]/ancestor::div[@role='button']",

        # 展開更多留言
        "//span[contains(text(), '更多留言')]/ancestor::div[@role='button']",
        "//div[@role='button'][contains(text(), '更多留言')]",

        # 查看之前的留言
        "//div[@role='button'][contains(text(), '查看之前的留言')]",

        # 查看更多留言/回覆
        "//span[contains(text(), '查看更多')]/ancestor::div[@role='button']",
    ]
    
    buttons = driver.find_elements(By.XPATH, " | ".join(button_selectors))
    for btn in buttons:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.5)
            btn.click()
            print("clicked button")
            time.sleep(1.5)
            changed = True
        except:
            pass
    return changed


# ------------------------------------------------
# 滾動頁面直到高度改變
# ------------------------------------------------
def scroll_page():
    old_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    print("scrolled_page_sleep:")
    time.sleep(1.2)
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height > old_height


# ------------------------------------------------
# 提取留言（邊讀邊寫 CSV）
# ------------------------------------------------
def extract_comments(seen):
    comments = driver.find_elements(
        By.XPATH,
        "//div[@role='article' and .//div[@dir='auto']]"
    )

    for c in comments:
        try:
            text_block = c.text.strip()
            if not text_block:
                continue

            # 嘗試取得留言 permalink（唯一 ID）
            links = c.find_elements(By.XPATH, ".//a[contains(@href,'comment_id')]")
            if links:
                permalink = links[0].get_attribute("href")
                cid = permalink
            else:
                cid = make_hash(text_block)

            if cid in seen:
                continue

            seen.add(cid)

            # 抓作者
            author = ""
            try:
                author = c.find_element(By.XPATH, ".//strong//span").text
            except:
                pass

            # 抓內容（移除作者）
            content = text_block.replace(author, "").strip()

            csv_writer.writerow([cid, author, content])
            print("✔ 已寫入留言：", content[:30])

        except Exception as e:
            pass


# ------------------------------------------------
# 控制整體流程
# ------------------------------------------------
def navigate_comment_section():
    seen = set()

    no_change_count = 0

    while True:
        print("➡ 展開更多留言/回覆…")
        expanded = expand_all_buttons()

        print("➡ 提取留言…")
        extract_comments(seen)

        print("➡ 滾動頁面…")
        scrolled = scroll_page()

        print("page_scrolled, sleep now")
        time.sleep(0.5)

        # 若無展開也無滾動，可能到底
        if not expanded and not scrolled:
            no_change_count += 1
            print("no change count: ",no_change_count)
        else:
            no_change_count = 0
            print("no change count refreshed")

        if no_change_count >= 10:
            print("✔ 已到底部，停止")
            break


# ------------------------------------------------
# 主流程
# ------------------------------------------------
comment_section = find_comment_section()
navigate_comment_section()

csv_file.close()
driver.quit()

print("🎉 完成！留言已寫入 fb_comments.csv")
