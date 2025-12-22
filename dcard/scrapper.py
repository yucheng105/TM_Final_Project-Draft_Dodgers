import json
import time
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# ================= 設定區 =================
# 關鍵字設定：每個關鍵字可指定時間範圍
# 格式: {"keyword": "關鍵字", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
KEYWORDS_CONFIG = [
    # {"keyword": "王大陸", "start_date": "2025-02-18", "end_date": "2025-02-25"},
    # {"keyword": "坤達", "start_date": "2025-10-21", "end_date": "2025-10-28"},
    # {"keyword": "修杰楷", "start_date": "2025-10-21", "end_date": "2025-10-28"},
    # {"keyword": "阿達", "start_date": "2025-11-05", "end_date": "2025-11-12"},
    {"keyword": "陳零九", "start_date": "2025-05-14", "end_date": "2025-05-21"},
    # {"keyword": "陳柏霖", "start_date": "2025-10-21", "end_date": "2025-10-28"},
    {"keyword": "書偉", "start_date": "2025-10-21", "end_date": "2025-10-28"},
    # {"keyword": "小杰", "start_date": "2025-10-21", "end_date": "2025-10-28"}
]

MAX_SCROLL_TIMES = 50  # 每篇文章要在留言區捲動幾次 (載入更多留言)
# =========================================

def setup_driver():
    options = Options()
    # 改為使用乾淨的瀏覽器環境，不再讀取本機 User Data
    # 這樣執行時不需要關閉您平常使用的瀏覽器
    
    # 避免一些自動化檢測的 flag
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # driver = webdriver.Edge(options=options)
    driver = uc.Chrome()
    return driver


def parse_date_from_element(date_text=None, datetime_attr=None):
    """
    解析日期，優先使用 <time> 標籤的 datetime 屬性
    datetime_attr: ISO 8601 格式，例如 "2025-11-29T10:13:36.863Z"
    date_text: 顯示文字，例如 "2024年1月15日", "1月15日", "2小時前" 等
    """
    try:
        # 優先使用 datetime 屬性 (精確的 ISO 8601 格式)
        if datetime_attr:
            # 處理 ISO 8601 格式: 2025-11-29T10:13:36.863Z
            # 移除毫秒和 Z 時區標記，轉換為 datetime 物件
            if 'T' in datetime_attr:
                # 移除 'Z' 並處理毫秒
                datetime_str = datetime_attr.replace('Z', '').split('.')[0]
                return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        
        # 備用方案：解析顯示文字
        if date_text:
            date_text = date_text.strip()
            
            # 處理相對時間 (今天、昨天、X小時前等) - 這些都視為最近的文章
            if any(keyword in date_text for keyword in ["小時前", "分鐘前", "剛剛", "今天", "昨天"]):
                return datetime.now()
            
            # 處理完整日期格式: "2024年1月15日"
            if "年" in date_text and "月" in date_text:
                date_text = date_text.replace("年", "-").replace("月", "-").replace("日", "")
                return datetime.strptime(date_text, "%Y-%m-%d")
            
            # 處理只有月日的格式: "1月15日" (假設為今年)
            if "月" in date_text and "日" in date_text:
                current_year = datetime.now().year
                date_text = date_text.replace("月", "-").replace("日", "")
                return datetime.strptime(f"{current_year}-{date_text}", "%Y-%m-%d")
        
        # 如果無法解析，返回 None
        return None
    except:
        return None


def is_date_in_range(article_date, start_date_str, end_date_str):
    """
    檢查文章日期是否在指定範圍內
    """
    if article_date is None:
        return True  # 無法解析日期時，保留該文章
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        return start_date <= article_date <= end_date
    except:
        return True  # 日期格式錯誤時，保留該文章


def scrape_keyword(driver, keyword, start_date, end_date):
    """
    爬取單一關鍵字的所有符合時間範圍的文章
    """
    print(f"\n{'='*60}")
    print(f"🚀 開始搜尋關鍵字: {keyword}")
    print(f"📅 時間範圍: {start_date} ~ {end_date}")
    print(f"{'='*60}\n")
    
    search_url = f"https://www.dcard.tw/search?query={keyword}&sort=latest"
    driver.get(search_url)
    
    # 等待搜尋結果載入
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/f/")]'))
        )
    except:
        print(f"⚠️  搜尋 '{keyword}' 無結果或載入失敗")
        return []
    
    time.sleep(2)

    # 收集文章連結與日期
    article_data_list = []
    max_scroll_attempts = 100  # 增加捲動次數以確保找到所有符合日期的文章
    scroll_count = 0
    no_new_links_count = 0
    out_of_range_count = 0  # 連續超出範圍的文章數
    
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    collected_urls = set()
    
    while scroll_count < max_scroll_attempts:
        # 收集當前頁面上的文章
        # 找尋文章卡片，通常包含連結和日期
        article_cards = driver.find_elements(By.XPATH, '//a[contains(@href, "/f/") and contains(@href, "/p/")]/..')
        
        previous_count = len(article_data_list)
        
        for card in article_cards:
            try:
                # 取得文章連結
                link_elem = card.find_element(By.XPATH, './/a[contains(@href, "/f/") and contains(@href, "/p/")]')
                href = link_elem.get_attribute('href')
                
                if not href or href in collected_urls:
                    continue
                
                # 嘗試取得日期 - 優先從 <time> 標籤獲取 datetime 屬性
                date_text = None
                datetime_attr = None
                
                try:
                    # 優先嘗試找尋 <time> 標籤並取得 datetime 屬性
                    time_elem = card.find_element(By.XPATH, './/time')
                    datetime_attr = time_elem.get_attribute('datetime')
                    date_text = time_elem.text  # 同時也取得顯示文字作為備用
                except:
                    # 如果找不到 <time> 標籤，嘗試其他選擇器
                    try:
                        date_elem = card.find_element(By.XPATH, './/span[contains(@class, "date")] | .//span[contains(text(), "月") or contains(text(), "小時")]')
                        date_text = date_elem.text
                    except:
                        # 如果找不到明確的日期元素，嘗試從整個卡片文字中尋找
                        card_text = card.text
                        # 簡單的日期關鍵字匹配
                        for line in card_text.split('\n'):
                            if any(keyword in line for keyword in ["月", "小時前", "分鐘前", "昨天", "今天"]):
                                date_text = line
                                break
                
                # 解析日期 (優先使用 datetime 屬性)
                article_date = parse_date_from_element(date_text=date_text, datetime_attr=datetime_attr)
                
                # 檢查日期是否在範圍內
                if article_date:
                    if article_date < start_date_obj:
                        # 文章太舊，因為按最新排序，後面的文章也會更舊
                        out_of_range_count += 1
                        if out_of_range_count >= 10:
                            print(f"⚠️  已連續遇到 10 篇超出時間範圍的文章，停止搜尋")
                            scroll_count = max_scroll_attempts  # 強制結束
                            break
                        continue
                    elif article_date > end_date_obj:
                        # 文章太新，繼續找
                        continue
                    else:
                        # 文章在範圍內
                        out_of_range_count = 0
                else:
                    # 無法解析日期，保留該文章
                    pass
                
                collected_urls.add(href)
                article_data_list.append({
                    "url": href,
                    "date": date_text,
                    "datetime": datetime_attr,  # 保存原始 ISO 8601 時間
                    "parsed_date": article_date.strftime("%Y-%m-%d %H:%M:%S") if article_date else "未知"
                })
                print(f"📊 已收集 {len(article_data_list)} 篇文章 (日期: {article_date.strftime('%Y-%m-%d %H:%M:%S') if article_date else date_text if date_text else '未知'})")
                
            except Exception as e:
                continue
        
        # 檢查是否有新增文章
        if len(article_data_list) == previous_count:
            no_new_links_count += 1
            if no_new_links_count >= 100:
                print(f"⚠️  已連續100次捲動無新文章，停止搜尋")
                break
        else:
            no_new_links_count = 0
        
        # 如果已經遇到太多超出範圍的文章，停止
        if out_of_range_count >= 10:
            break
        
        # 往下捲動以載入更多文章
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.5, 2.5))
        scroll_count += 1
    
    print(f"\n📋 關鍵字 '{keyword}' 找到 {len(article_data_list)} 篇符合時間範圍的文章\n")
    
    # 爬取每篇文章的詳細內容
    results = []
    for index, article_info in enumerate(article_data_list):
        url = article_info["url"]
        print(f"[{index+1}/{len(article_data_list)}] 正在爬取: {url}")
        driver.get(url)
        time.sleep(random.uniform(2, 4))

        article_data = {
            "keyword": keyword,
            "url": url,
            "date": article_info["parsed_date"],
            "title": "N/A",
            "content": "N/A",
            "comments": []
        }

        try:
            # --- 抓取標題 ---
            title_elem = driver.find_element(By.TAG_NAME, "h1")
            article_data["title"] = title_elem.text

            # --- 抓取文章內容 ---
            try:
                content_elem = driver.find_element(By.XPATH, '//div[contains(@class, "c04j7q-0")] | //article//div[contains(@class, "phqjxq-0")]')
                if not content_elem:
                    content_elem = driver.find_element(By.CSS_SELECTOR, "article div")
                article_data["content"] = content_elem.text
            except:
                try:
                    full_article = driver.find_element(By.TAG_NAME, "article").text
                    article_data["content"] = full_article
                except:
                    article_data["content"] = "無法提取內容"

            # --- 抓取留言 ---
            print("   └── 正在載入留言...")
            
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            
            while scroll_attempts < MAX_SCROLL_TIMES:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1.5, 2.5))
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    print("   └── 已到達頁面底部，開始抓取留言")
                    break
                
                last_height = new_height
                scroll_attempts += 1
                print(f"   └── 捲動中... ({scroll_attempts}/{MAX_SCROLL_TIMES})")
            
            comment_blocks = driver.find_elements(By.XPATH, '//div[contains(@id, "comment-")]')
            
            for comment in comment_blocks:
                try:
                    text_div = comment.find_element(By.XPATH, './/div[@class="d_xa_34 d_xj_2v c1ehvwc9"]/span')
                    comment_content = text_div.text
                    
                    if comment_content == "":
                        continue
                    article_data["comments"].append(comment_content)
                except:
                    continue

            print(f"   └── 成功抓取 {len(article_data['comments'])} 則留言")

        except Exception as e:
            print(f"   ❌ 爬取文章時發生錯誤: {e}")
        
        results.append(article_data)
    
    return results


def scrape_dcard():
    """
    主函數：依序爬取所有關鍵字
    """
    driver = setup_driver()
    all_results = []
    
    try:
        for index, config in enumerate(KEYWORDS_CONFIG):
            keyword = config["keyword"]
            start_date = config["start_date"]
            end_date = config["end_date"]
            
            print(f"\n{'#'*70}")
            print(f"# 處理第 {index+1}/{len(KEYWORDS_CONFIG)} 個關鍵字")
            print(f"{'#'*70}")
            
            # 爬取該關鍵字的文章
            results = scrape_keyword(driver, keyword, start_date, end_date)
            all_results.extend(results)
            
            # 每個關鍵字之間休息一下
            if index < len(KEYWORDS_CONFIG) - 1:
                print(f"\n⏸️  休息 3 秒後繼續下一個關鍵字...\n")
                time.sleep(3)
        
        # 儲存所有結果
        output_file = f'dcard_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        
        print(f"\n{'='*70}")
        print(f"✅ 所有爬取完成！")
        print(f"📊 總共爬取 {len(all_results)} 篇文章")
        print(f"💾 資料已儲存為 {output_file}")
        print(f"{'='*70}\n")
        
        # 輸出各關鍵字統計
        keyword_stats = {}
        for article in all_results:
            kw = article["keyword"]
            keyword_stats[kw] = keyword_stats.get(kw, 0) + 1
        
        print("\n📈 各關鍵字爬取統計：")
        for kw, count in keyword_stats.items():
            print(f"   - {kw}: {count} 篇文章")

    except Exception as e:
        print(f"發生嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_dcard()
