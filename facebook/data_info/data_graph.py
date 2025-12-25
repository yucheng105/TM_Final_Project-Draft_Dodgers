import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

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
    json_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'facebook_comments_by_keyword.json')
    
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

    # Calculate statistics
    artist_stats = {}
    total_comments = 0
    
    for artist, comments in data.items():
        standard_name = name_mapping.get(artist, artist)
        count = len(comments)
        artist_stats[standard_name] = artist_stats.get(standard_name, 0) + count
        total_comments += count
        
    print(f"Facebook 平台總留言數量: {total_comments}")
    print("各藝人相關留言量:")
    for artist, count in artist_stats.items():
        print(f"{artist}: {count}")

    # Prepare data for plotting
    target_order = ['王大陸', '謝坤達', '修杰楷', '阿達', '廖允杰', '陳零九']
    artists = [artist for artist in target_order if artist in artist_stats]
    counts = [artist_stats[artist] for artist in artists]
    
    # Create bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(artists, counts, color='skyblue')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}',
                 ha='center', va='bottom', fontsize=14)

    plt.title('Facebook 各藝人相關留言數量統計', fontproperties=font_prop, fontsize=24)
    plt.xlabel('藝人', fontproperties=font_prop, fontsize=20)
    plt.ylabel('留言數量', fontproperties=font_prop, fontsize=20)
    plt.xticks(rotation=45, fontproperties=font_prop, fontsize=16)
    plt.yticks(fontsize=16)
    
    # Adjust layout to prevent clipping of labels
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(os.path.dirname(__file__), 'fb_comments_stats.png')
    plt.savefig(output_path)
    print(f"圖表已儲存至: {output_path}")

if __name__ == "__main__":
    main()
