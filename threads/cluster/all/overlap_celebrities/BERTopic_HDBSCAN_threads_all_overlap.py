#!/usr/bin/env python
# coding: utf-8

# In[1]:


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


# In[2]:


# check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"目前使用的設備是: {device}")


# In[3]:


def clean_text(text):
    # 1. 移除網址 (http, https, ftp, www)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    # 2. 移除一些社群常見的雜訊 (可選)
    # 例如：移除重複的換行或多餘空格
    text = text.replace('\n', ' ').strip()
    return text


# In[15]:


##############
# Read data
##############

platform_name = "threads"
input_file_name = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "threads_comments_by_keyword.json")

with open(input_file_name, "r", encoding="utf-8") as f:
    fb_comments_dict = json.load(f)
print(f"成功從{input_file_name}讀取檔案至fb_comments_dict\n")


print()

# 將全部留言存到all_comments
all_comments = []
for artist in fb_comments_dict:
    if artist == '張書偉' or artist == '陳柏霖' or artist == '書偉':
        continue
    all_comments += fb_comments_dict[artist]
    print(artist)

print()

# 刪掉url
all_comments_cleaned = [clean_text(str(c)) for c in all_comments if len(clean_text(str(c))) > 2]
print("成功將所有留言存入all_comments_cleaned，並去除留言內的url\n")
print(f"all_comments_cleaned共有{len(all_comments_cleaned)}篇貼文")


# In[24]:


############
# Settings
############

# 1. 向量化模型 (使用多語言支援)
embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 2. 降維模型 (UMAP): 影響分群的精細度
umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)

# 3. 聚類模型 (HDBSCAN): 自動偵測分群
# min_cluster_size: 一個主題最少要有幾則留言 (可根據資料量調整)
min_size = 15
hdbscan_model = HDBSCAN(min_cluster_size=min_size, metric='euclidean', cluster_selection_method='eom', prediction_data=True)

# 4. 關鍵字提取 (Vectorizer): 排除停用詞
vectorizer_model = CountVectorizer(stop_words=["的", "了", "在", "是", "我", "https", "com"])

print(f"設定元件完畢{min_size}")


# In[25]:


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

topics, probs = topic_model.fit_transform(all_comments_cleaned)


# In[26]:


# 將離群值分配給最相似的主題
new_topics = topic_model.reduce_outliers(all_comments_cleaned, topics)

# 更新模型中的主題標籤
topic_model.update_topics(all_comments_cleaned, topics=new_topics)


# In[27]:


###################
# Display Results
###################

# 取得主題清單 (-1 代表雜訊/不屬於任何主題)
topic_info = topic_model.get_topic_info()
print(topic_info.head(10))

# 儲存結果
topic_info.to_csv(f"hdbscan_topics_{platform_name}_overlap.csv", index=False, encoding="utf-8-sig")


# In[29]:


###############
# 圖形化顯示
###############

# top_n_topics: 顯示前幾個主題
# n_words: 每個主題顯示幾個關鍵字
fig1 = topic_model.visualize_barchart(top_n_topics=15, n_words=10, height=600)
fig1.show()

# 儲存為 HTML 檔（可以用瀏覽器開啟，保留互動功能）
fig1.write_html(f"topic_barchart_{platform_name}_overlap.html")

# intertopic distance map
fig2 = topic_model.visualize_topics()
fig2.show()
fig2.write_html(f"topic_distance_map_{platform_name}_overlap.html")

# Hierarchy
fig3 = topic_model.visualize_hierarchy()
fig3.show()
fig3.write_html(f"topic_hierarchy_{platform_name}_overlap.html")

# Heat Map
fig4 = topic_model.visualize_heatmap()
fig4.show()
fig4.write_html(f"topic_heatmap_{platform_name}_overlap.html")


# In[ ]:




