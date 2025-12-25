import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

# Set the font path for Chinese characters
font_path = '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'
if os.path.exists(font_path):
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Noto Sans CJK TC', 'WenQuanYi Zen Hei', 'SimHei', 'Arial Unicode MS']
    font_prop = fm.FontProperties(family=plt.rcParams['font.sans-serif'])

def main():
    # Path to the JSON file
    json_file_path = os.path.join(os.path.dirname(__file__), 'dcard_sentiment_by_keyword.json')
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_file_path}")
        return

    # Name mapping
    name_mapping = {
        '王大陸': '王大陸',
        '王大陸資訊分享台灣站': '王大陸',
        '坤達': '謝坤達',
        '謝坤達': '謝坤達',
        '修杰楷': '修杰楷',
        '阿達': '阿達',
        '陳柏霖': '陳柏霖',
        '小杰': '廖允杰',
        '廖允杰': '廖允杰',
        '陳零九': '陳零九',
        '書偉': '張書偉',
        '張書偉': '張書偉'
    }

    # Aggregate data by standard name
    aggregated_data = {}
    for artist, comments in data.items():
        standard_name = name_mapping.get(artist, artist)
        if standard_name not in aggregated_data:
            aggregated_data[standard_name] = []
        aggregated_data[standard_name].extend(comments)

    artists = []
    positive = []
    negative = []
    neutral = []

    target_order = ['王大陸', '謝坤達', '修杰楷', '阿達', '廖允杰', '陳零九']

    for artist in target_order:
        if artist in aggregated_data:
            comments = aggregated_data[artist]
            artists.append(artist)
            pos = sum(1 for c in comments if c.get('sentiment') == '正面')
            neg = sum(1 for c in comments if c.get('sentiment') == '負面')
            neu = sum(1 for c in comments if c.get('sentiment') == '中性')
            positive.append(pos)
            negative.append(neg)
            neutral.append(neu)

    # Calculate proportions
    total_counts = np.array(positive) + np.array(neutral) + np.array(negative)
    # Avoid division by zero
    total_counts = np.where(total_counts == 0, 1, total_counts)
    
    pos_prop = np.array(positive) / total_counts * 100
    neu_prop = np.array(neutral) / total_counts * 100
    neg_prop = np.array(negative) / total_counts * 100

    # Plotting
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Horizontal Stacked bar chart (100%)
    # Colors: Positive (Green), Neutral (Yellow/Amber), Negative (Red)
    p1 = ax.barh(artists, pos_prop, label='正面', color='#66BB6A') 
    p2 = ax.barh(artists, neu_prop, left=pos_prop, label='中性', color='#FFCA28') 
    p3 = ax.barh(artists, neg_prop, left=pos_prop+neu_prop, label='負面', color='#EF5350') 

    ax.set_title('Dcard 各藝人情感分析比例', fontproperties=font_prop, fontsize=24)
    ax.set_ylabel('藝人', fontproperties=font_prop, fontsize=20)
    ax.set_xlabel('情感比例 (%)', fontproperties=font_prop, fontsize=20)
    ax.legend(prop=font_prop, fontsize=16, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)
    
    plt.xticks(fontproperties=font_prop, fontsize=16)
    plt.yticks(fontproperties=font_prop, fontsize=16)
    
    # Invert y-axis to have the first artist at the top
    ax.invert_yaxis()

    # Add percentage labels on the bars
    for i in range(len(artists)):
        # Positive label
        if pos_prop[i] > 5: # Only show if segment is large enough
            ax.text(pos_prop[i]/2, i, f'{pos_prop[i]:.1f}%', ha='center', va='center', fontsize=12, color='white', fontweight='bold')
        
        # Neutral label
        if neu_prop[i] > 5:
            ax.text(pos_prop[i] + neu_prop[i]/2, i, f'{neu_prop[i]:.1f}%', ha='center', va='center', fontsize=12, color='black', fontweight='bold')
            
        # Negative label
        if neg_prop[i] > 5:
            ax.text(pos_prop[i] + neu_prop[i] + neg_prop[i]/2, i, f'{neg_prop[i]:.1f}%', ha='center', va='center', fontsize=12, color='white', fontweight='bold')

    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(os.path.dirname(__file__), 'dcard_sentiment_stats.png')
    plt.savefig(output_path)
    print(f"圖表已儲存至: {output_path}")

if __name__ == "__main__":
    main()
