import json
import os

def main():
    input_file = 'dcard_data_20251201_221552.json'
    output_file = 'dcard_comments_by_keyword.json'

    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Aggregate comments by keyword
    keyword_comments = {}

    for item in data:
        keyword = item.get('keyword')
        comments = item.get('comments', [])
        
        if keyword and comments:
            if keyword not in keyword_comments:
                keyword_comments[keyword] = []
            
            # Add comments to the list
            keyword_comments[keyword].extend(comments)

    print(f"Converted data. Found {len(keyword_comments)} keywords.")
    
    # Save to new format
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(keyword_comments, f, ensure_ascii=False, indent=4)
    print("Done.")

if __name__ == "__main__":
    main()
