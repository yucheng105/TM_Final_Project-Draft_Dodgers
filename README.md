# TM_Final_Project-Draft_Dodgers

文字探勘初論期末報告 - 社交媒體輿情分析

本專案旨在分析 Dcard、Facebook、Instagram 和 Threads 四大社交媒體平台上關於逃兵議題的討論。專案包含資料爬取、情感分析、主題分群與相似度分析等模組。

## 目錄結構

專案依照平台分為四個主要資料夾，結構統一如下：

- **dcard/**
- **facebook/**
- **instagram/**
- **threads/**

每個平台資料夾內包含以下子模組：

- **scrapper/**: 負責爬取該平台的留言資料。
- **sentiment_analysis/**: 使用 RoBERTa 模型進行情感分析。
- **cluster/**: 使用 BERTopic 與 HDBSCAN 進行主題分群（包含整體與個別藝人）。
- **similarity/**: 分析留言之間的相似度。
- **data_info/**: 資料統計與視覺化圖表繪製。

## 安裝需求

請確保已安裝 Python 3.8+，並執行以下指令安裝所需套件：

```bash
pip install -r requirement.txt
```

主要依賴套件包括：
- torch, transformers (深度學習與模型)
- bertopic, hdbscan, umap-learn (主題分群)
- selenium, undetected-chromedriver (爬蟲)
- jieba (中文斷詞)
- pandas, numpy, matplotlib (資料處理與繪圖)

## 使用說明

### 1. 資料爬取 (Scrapper)
進入各平台的 `scrapper` 資料夾，執行爬蟲程式以獲取留言資料。
例如：
```bash
python facebook/scrapper/scrapper.py
```
產出的 JSON 檔案將會儲存於各平台的主目錄下（如 `facebook/facebook_comments_by_keyword.json`）。

### 2. 情感分析 (Sentiment Analysis)
進入 `sentiment_analysis` 資料夾，執行分析腳本或 Jupyter Notebook。
```bash
python facebook/sentiment_analysis/sentiment_analysis.py
# 或執行對應的 .ipynb 檔案
```

### 3. 主題分群 (Cluster)
進入 `cluster/all` 或 `cluster/individual` 進行全體或個別對象的主題分析。
```bash
python facebook/cluster/all/cluster_all.py
```

### 4. 相似度分析 (Similarity)
執行相似度分析腳本：
```bash
python facebook/similarity/analyze_similarity.py
```

### 5. 資料視覺化 (Data Info)
生成統計圖表：
```bash
python facebook/data_info/data_graph.py
```

## 注意事項
- 爬蟲程式可能需要對應的瀏覽器驅動程式 (如 ChromeDriver)。
- 部分模型 (如 BERT) 執行時需要較多記憶體與 GPU 資源。
- 請確保執行程式時的工作目錄位於專案根目錄，以確保路徑引用正確。
