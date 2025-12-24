#!/usr/bin/env python
# coding: utf-8

# In[6]:


import json
import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from umap import UMAP
import os
import torch
import re
from sklearn.feature_extraction.text import CountVectorizer


# In[7]:


# check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"目前使用的設備是: {device}")


# In[8]:


#######################
# 用來把留言中的url清除
#######################

def clean_text(text):
    # 1. 移除網址 (http, https, ftp, www)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # 2. 移除一些社群常見的雜訊 (可選)
    # 例如：移除重複的換行或多餘空格
    text = text.replace('\n', ' ').strip()
    return text


# In[9]:


##############
# Read data
##############

input_file_name = "../../all_artists_comments.json"
platform_name = "threads"

with open(input_file_name, "r", encoding="utf-8") as f:
    comments_dict = json.load(f)
print(f"成功從{input_file_name}讀取檔案至comments_dict\n")


# In[23]:


############
# Settings
############

# 1. 向量化模型 (使用多語言支援)
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 2. 降維模型 (UMAP): 影響分群的精細度
umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)

'''
# 3. 聚類模型 (HDBSCAN): 自動偵測分群
# min_cluster_size: 一個主題最少要有幾則留言 (可根據資料量調整)
hdbscan_model = HDBSCAN(min_cluster_size=len(comments_cleaned) * 0.05, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
'''

# 4. 關鍵字提取 (Vectorizer): 排除停用詞
vectorizer_model = CountVectorizer(stop_words=["的", "了", "在", "是", "我", "https", "com"])



print("設定元件完畢")


# In[39]:


for artist in comments_dict:
    # 把留言中的url刪掉
    comments_cleaned = [clean_text(str(c)) for c in comments_dict[artist] if len(clean_text(str(c))) > 2]
    print(f"成功提取出{artist}的留言至comment_cleaned")

    min_size = int(len(comments_cleaned) * 0.0005)
    if min_size < 2:
        min_size = 5

    # min_cluster_size: 一個主題最少要有幾則留言 (可根據資料量調整)
    hdbscan_model = HDBSCAN(min_cluster_size=min_size, metric='euclidean', cluster_selection_method='eom', prediction_data=True)


    #############
    # Training
    #############
    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        verbose=True
    )
    
    topics, probs = topic_model.fit_transform(comments_cleaned)
    '''
    #########################################################################
    # 如果Topic=-1的文本太多了，執行以下程式，把一些outliers分到最靠近的群體裏面
    #########################################################################
    
    # 將離群值分配給最相似的主題
    new_topics = topic_model.reduce_outliers(comments_cleaned, topics)
    
    # 更新模型中的主題標籤
    topic_model.update_topics(comments_cleaned, topics=new_topics)
    '''
    ###################
    # 結果（文字）　
    ###################
    
    # 取得主題清單 (-1 代表雜訊/不屬於任何主題)
    topic_info = topic_model.get_topic_info()
    print(topic_info.head(10))
    
    # 儲存結果
    folder_path = "hbdscan_topics_result_idividual_csv"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    topic_info.to_csv(f"hbdscan_topics_result_idividual_csv/hdbscan_topics_{platform_name}_{artist}.csv", index=False, encoding="utf-8-sig")
    print(f"儲存{artist}的結果到",f"hdbscan_topics_{platform_name}_{artist}.csv")

    ###############
    # 圖形化顯示
    ###############
    folder_path = f"hbdscan_topics_result_idividual_graphs_/{artist}/{platform_name}"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # top_n_topics: 顯示前幾個主題
    # n_words: 每個主題顯示幾個關鍵字
    fig1 = topic_model.visualize_barchart(top_n_topics=15, n_words=10, height=600)
    # fig1.show()
    
    # 儲存為 HTML 檔（可以用瀏覽器開啟，保留互動功能）
    fig1.write_html(f"hbdscan_topics_result_idividual_graphs_/{artist}/{platform_name}/topic_barchart_{platform_name}_{artist}.html")
    
    # intertopic distance map
    try:
        fig2 = topic_model.visualize_topics()
        # fig2.show()
        fig2.write_html(f"hbdscan_topics_result_idividual_graphs_/{artist}/{platform_name}/topic_distance_map_{platform_name}_{artist}.html")
    except Exception as e:
        print(f"無法繪製 Intertopic Distance Map (可能是主題太少): {e}")
    
    # Hierarchy
    fig3 = topic_model.visualize_hierarchy()
    # fig3.show()
    fig3.write_html(f"hbdscan_topics_result_idividual_graphs_/{artist}/{platform_name}/topic_hierarchy_{platform_name}_{artist}.html")
    
    # Heat Map
    fig4 = topic_model.visualize_heatmap()
    # fig4.show()
    fig4.write_html(f"hbdscan_topics_result_idividual_graphs_/{artist}/{platform_name}/topic_heatmap_{platform_name}_{artist}.html")

print()
print("All Done!")


# In[ ]:




