import time
import csv
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, ElementClickInterceptedException

# ----------------------------
# 參數（修改成你的 IG 帖文）
# ----------------------------
POST_URL = "https://www.instagram.com/hsieh_kunda/p/DPk1EhDgZc1/"   # ← 改成目標 IG 帖文

# ----------------------------
# 啟動 Selenium
# ----------------------------
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--lang=en")  # 設定語言為英文，避免按鈕文字不同
driver = webdriver.Chrome(options=options)
driver.get(POST_URL)

# 等待頁面加載
time.sleep(5)

# 先檢查是否在登入頁面
try:
    # 檢查是否有登入表單
    driver.find_element(By.XPATH, "//input[@name='username']")
    print("請先手動登入 Instagram...")
    input("登入完成後按 Enter 繼續： ")
except:
    print("已登入或非登入頁面，繼續執行...")
    time.sleep(2)

# ----------------------------
# CSV 初始化
# ----------------------------
csv_file = open("ig_comments.csv", "w", newline="", encoding="utf-8-sig")  # 改為 "w" 模式
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["comment_id", "author", "content"])
csv_file.flush()

def make_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ----------------------------
# 簡化的留言擷取函數
# ----------------------------
def extract_comments(seen):
    """
    擷取目前頁面上所有留言
    """
    try:
        # 方法1：嘗試找留言容器（Instagram 常見的留言結構）
        comments = []
        
        # 嘗試多種定位留言的方式
        selectors = [
            "div[class*='x9f619'][class*='xjbqb8w'] span",
            "ul[class*='x78zum5'] li span",
            "div[role='dialog'] span",  # 留言可能在全螢幕模式中
            "article span",  # 文章內的留言
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text and len(text) > 3:  # 過濾太短的文字
                        # 嘗試找作者（通常是父元素中的連結或粗體文字）
                        author = ""
                        try:
                            # 向上找可能包含作者的元素
                            parent = elem.find_element(By.XPATH, "./ancestor::div[contains(@class, 'x9f619') or contains(@class, 'x1lliihq')]")
                            author_elements = parent.find_elements(By.CSS_SELECTOR, "a, span[class*='_ap3a'], span[style*='font-weight']")
                            for auth_elem in author_elements:
                                auth_text = auth_elem.text.strip()
                                if auth_text and auth_text != text and len(auth_text) > 1:
                                    author = auth_text
                                    break
                        except:
                            pass
                        
                        # 生成唯一ID
                        cid = make_hash(f"{author}:{text}")
                        
                        if cid not in seen and text:
                            seen.add(cid)
                            csv_writer.writerow([cid, author, text])
                            csv_file.flush()
                            print(f"✔ 找到留言: [{author}] {text[:50]}...")
                if elements:
                    print(f"使用選擇器 '{selector}' 找到 {len(elements)} 個元素")
            except Exception as e:
                continue
        
        # 方法2：直接抓取所有可見留言（更直接的方法）
        try:
            # 找到留言區域（通常有一個特定的容器）
            comment_areas = driver.find_elements(By.XPATH, 
                "//div[contains(@class, 'x9f619') and contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')] | "
                "//ul[contains(@class, '_abpo')] | "
                "//div[@role='dialog']//ul"
            )
            
            for area in comment_areas:
                try:
                    # 在留言區域中找留言項目
                    comment_items = area.find_elements(By.XPATH, 
                        ".//div[contains(@class, 'x9f619')] | "
                        ".//li[contains(@class, 'x1lliihq')] | "
                        ".//div[@data-comment-id]"
                    )
                    
                    for item in comment_items:
                        try:
                            text = item.text.strip()
                            if not text or len(text) < 3:
                                continue
                            
                            # 分離作者和內容
                            lines = text.split('\n')
                            if len(lines) >= 2:
                                author = lines[0].strip()
                                content = ' '.join(lines[1:]).strip()
                            else:
                                author = ""
                                content = text
                            
                            # 過濾掉按讚數、時間等非留言文字
                            if any(word in content.lower() for word in ['like', 'reply', 'h', 'd', 'w', 'min', 'sec']):
                                continue
                            
                            cid = make_hash(f"{author}:{content}")
                            
                            if cid not in seen and content:
                                seen.add(cid)
                                csv_writer.writerow([cid, author, content])
                                csv_file.flush()
                                print(f"✔ 擷取留言: [{author}] {content[:50]}...")
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"方法2錯誤: {e}")
            
        return len(seen)
        
    except Exception as e:
        print(f"擷取留言時發生錯誤: {e}")
        return 0

# ----------------------------
# 滾動載入更多留言
# ----------------------------
def scroll_for_comments():
    """
    滾動頁面以載入更多留言
    """
    seen = set()
    last_count = 0
    no_new_count = 0
    
    print("開始擷取留言...")
    
    # 先擷取一次
    extract_comments(seen)
    last_count = len(seen)
    
    # 持續滾動直到沒有新留言
    for i in range(50):  # 最多嘗試50次滾動
        print(f"\n--- 第 {i+1} 次滾動 ---")
        print(f"目前已收集 {len(seen)} 則留言")
        
        # 滾動到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # 等待新留言載入
        
        # 嘗試點擊「查看更多留言」按鈕
        try:
            more_buttons = driver.find_elements(By.XPATH,
                "//button[contains(., 'more') or contains(., 'More') or "
                "contains(., 'load') or contains(., 'Load') or "
                "contains(., '查看') or contains(., '顯示')]"
            )
            
            for btn in more_buttons:
                try:
                    if btn.is_displayed():
                        btn.click()
                        print("點擊了「更多」按鈕")
                        time.sleep(2)
                except:
                    continue
        except:
            pass
        
        # 擷取新留言
        extract_comments(seen)
        
        # 檢查是否有新留言
        if len(seen) == last_count:
            no_new_count += 1
            print(f"無新留言 ({no_new_count}/5)")
        else:
            no_new_count = 0
            last_count = len(seen)
            
        # 如果連續5次沒有新留言，結束
        if no_new_count >= 5:
            print("連續多次無新留言，結束擷取")
            break
            
        # 隨機等待一下
        time.sleep(2)
    
    return seen

# ----------------------------
# 主程式
# ----------------------------
try:
    # 等待頁面完全加載
    print("等待頁面載入...")
    time.sleep(5)
    
    # 嘗試點開留言區（如果有需要）
    try:
        # 點擊留言/評論按鈕
        comment_buttons = driver.find_elements(By.XPATH,
            "//span[contains(., 'comment') or contains(., 'Comment') or "
            "contains(., '評論') or contains(., '留言')]/ancestor::button | "
            "//button[contains(@aria-label, 'comment') or contains(@aria-label, 'Comment')]"
        )
        
        for btn in comment_buttons:
            try:
                btn.click()
                print("點擊了留言按鈕")
                time.sleep(3)
                break
            except:
                continue
    except:
        print("無法點擊留言按鈕，繼續執行...")
    
    # 開始滾動和擷取
    all_comments = scroll_for_comments()
    
    print(f"\n🎉 完成！總共收集到 {len(all_comments)} 則留言")
    
except KeyboardInterrupt:
    print("\n使用者中斷程式")
except Exception as e:
    print(f"程式執行錯誤: {e}")
    import traceback
    traceback.print_exc()
finally:
    csv_file.close()
    driver.quit()
    print("程式結束，留言已儲存至 ig_comments.csv")