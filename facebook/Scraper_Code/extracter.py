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

        ############
        # username
        ############

        # 頭號粉絲
        if lines[0] == "頭號粉絲":
            user_name = lines[1]
            comment_index = 2
        
        # 一般粉絲
        else:
            user_name = lines[0]
            comment_index = 1


        comment_start_index = comment_index
        comment_end_index = 0
        time_index = 0

        '''i = -1
        while (True):
            if lines[i] == "讚":
                time_index = i - 1
                comment_end_index = i - 1
                break'''
        
        comment_time = lines[time_index]
        comment_content = lines[comment_start_index:comment_end_index]

        # 已編輯留言
        if lines[-1] == "已編輯":
            comment_time = lines[-4]
            comment_content = lines[comment_index:-4]

        # 正常留言
        else:
            comment_time = lines[-3]
            comment_content = lines[comment_index:-3]
            
        processed_data.append({
            'comment_id': index + 1,
            '用戶名稱': user_name,
            '留言內容': "\n".join(comment_content),
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
process_multiple_files("C:\\大學\\大三上\\文字探勘初論\\期末報告Git\\TM_Final_Project-Draft_Dodgers\\raw_data\\facebook\\scraper_code\\scraped_unprocessed_raw_data", "C:\\大學\\大三上\\文字探勘初論\\期末報告Git\\TM_Final_Project-Draft_Dodgers\\raw_data\\facebook\\scraped_cleansed_raw_data")



