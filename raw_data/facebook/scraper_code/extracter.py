'''從scraped_unprocessed_raw_data抽出回覆本身'''
import pandas as pd
import re
import os
import glob

def process_single_facebook_csv(input_file, output_file):
    """
    處理單個Facebook留言CSV檔案
    """
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"讀取檔案 {input_file} 時發生錯誤: {e}")
        return None
    
    processed_data = []
    
    for index, row in df.iterrows():
        content = str(row['content'])
        lines = content.split('\n')
        
        # 確保至少有2行資料
        if len(lines) >= 2:
            user_name = lines[0].strip() if lines[0] else ''
            comment_content = lines[1].strip() if len(lines) > 1 else ''
            
            # 處理時間（第三行）
            comment_time = ''
            if len(lines) > 2:
                time_text = lines[2].strip()
                # 更靈活的時間提取
                time_patterns = [
                    r'(\d+\s*[天週小時分鐘秒月年]+)',
                    r'(\d+\s*[dD][天aA]*|[wW][週周])',
                    r'(\d+\s*[hH][小時]*|[mM][分鐘]*)'
                ]
                
                for pattern in time_patterns:
                    time_match = re.search(pattern, time_text)
                    if time_match:
                        comment_time = time_match.group(1)
                        break
                
                if not comment_time:
                    comment_time = time_text
            
            processed_data.append({
                'comment_id': index + 1,
                '用戶名稱': user_name,
                '留言內容': comment_content,
                '留言時間': comment_time
            })
    
    new_df = pd.DataFrame(processed_data)
    new_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return new_df

def process_multiple_files(input_folder, output_folder):
    """
    處理資料夾中的所有CSV檔案
    """
    # 建立輸出資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 尋找所有CSV檔案
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))
    
    print(f"找到 {len(csv_files)} 個CSV檔案")
    
    for csv_file in csv_files:
        file_name = os.path.basename(csv_file)
        output_file = os.path.join(output_folder, f"{file_name}")
        
        print(f"處理檔案: {file_name}")
        
        processed_df = process_single_facebook_csv(csv_file, output_file)
        
        if processed_df is not None:
            print(f"  成功處理 {len(processed_df)} 筆留言")
    
    print("\n所有檔案處理完成！")

'''# 使用範例
if __name__ == "__main__":
    # 單一檔案處理
    # process_single_facebook_csv("facebook_comments.csv", "processed_comments.csv")
    
    # 多檔案處理'''
process_multiple_files("C:\\大學\\大三上\\文字探勘初論\\期末報告Git\\TM_Final_Project-Draft_Dodgers\\raw_data\\facebook\\scraped_unprocessed_raw_data", "C:\\大學\\大三上\\文字探勘初論\\期末報告Git\\TM_Final_Project-Draft_Dodgers\\raw_data\\facebook\\scraped_prettified_raw_data")



