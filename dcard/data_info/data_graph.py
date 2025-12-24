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
    # Fallback to a default if the specific path doesn't exist (though we checked)
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'WenQuanYi Zen Hei', 'SimHei', 'Arial Unicode MS']

def main():
    # Path to the JSON file
    json_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dcard_comments_by_keyword.json')
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_file_path}")
        return

    # Calculate statistics
    artist_stats = {}
    total_comments = 0
    
    for artist, comments in data.items():
        count = len(comments)
        artist_stats[artist] = count
        total_comments += count
        
    print(f"Dcard 平台總留言數量: {total_comments}")
    print("各藝人相關留言量:")
    for artist, count in artist_stats.items():
        print(f"{artist}: {count}")

    # Prepare data for plotting
    artists = list(artist_stats.keys())
    counts = list(artist_stats.values())
    
    # Create bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(artists, counts, color='skyblue')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}',
                 ha='center', va='bottom', fontsize=14)

    plt.title('Dcard 各藝人相關留言數量統計', fontproperties=font_prop, fontsize=24)
    plt.xlabel('藝人', fontproperties=font_prop, fontsize=20)
    plt.ylabel('留言數量', fontproperties=font_prop, fontsize=20)
    plt.xticks(rotation=45, fontproperties=font_prop, fontsize=16)
    plt.yticks(fontsize=16)
    
    # Adjust layout to prevent clipping of labels
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(os.path.dirname(__file__), 'dcard_comments_stats.png')
    plt.savefig(output_path)
    print(f"圖表已儲存至: {output_path}")

if __name__ == "__main__":
    main()
