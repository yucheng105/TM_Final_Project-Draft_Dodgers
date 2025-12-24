import os

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import json
import torch
from tqdm import tqdm

def main():
    # Check for GPU
    device = 0 if torch.cuda.is_available() else -1
    print(f"Using device: {device}")

    # Input and Output files
    input_file = 'all_artists_comments.json'
    output_file = 'sentiment_analysis/sentiment_by_keyword.json'

    # Load data
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Model name
    model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

    print(f"Loading model: {model_name}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Move model to device
        if device >= 0:
            model = model.to(f'cuda:{device}')
        
        sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)
    except Exception as e:
        print(f"Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return

    # Label mapping
    label_map = {
        "negative": "負面",
        "neutral": "中性",
        "positive": "正面",
        "LABEL_0": "負面",
        "LABEL_1": "中性",
        "LABEL_2": "正面"
    }

    print("Starting sentiment analysis...")
    results = {} # {keyword: [ {comment, sentiment, score}, ... ]}

    # Process each keyword
    for keyword, comments in tqdm(data.items()):
        comment_sentiments = []
        
        if comments:
            try:
                # Process comments in batch
                predictions = sentiment_pipeline(comments, truncation=True, max_length=512, batch_size=8)
                
                for comment, pred in zip(comments, predictions):
                    sentiment_label = pred['label'].lower() if isinstance(pred['label'], str) else pred['label']
                    if sentiment_label in label_map:
                        sentiment_zh = label_map[sentiment_label]
                    else:
                        sentiment_zh = sentiment_label

                    comment_sentiments.append({
                        "comment": comment,
                        "sentiment": sentiment_zh,
                        "score": pred['score']
                    })
            except Exception as e:
                print(f"Error processing comments for keyword {keyword}: {e}")
                # Fallback: process one by one
                for comment in comments:
                    try:
                        pred = sentiment_pipeline(comment, truncation=True, max_length=512)[0]
                        sentiment_label = pred['label']
                        sentiment_zh = label_map.get(sentiment_label, sentiment_label)
                        if sentiment_zh not in ["正面", "中性", "負面"]:
                             sentiment_zh = label_map.get(str(sentiment_label).lower(), sentiment_label)

                        comment_sentiments.append({
                            "comment": comment,
                            "sentiment": sentiment_zh,
                            "score": pred['score']
                        })
                    except Exception as inner_e:
                        comment_sentiments.append({
                            "comment": comment,
                            "sentiment": "Error",
                            "score": 0.0
                        })

        results[keyword] = comment_sentiments

    # Save
    print(f"Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    # Print summary and save to file
    summary_file = 'sentiment_analysis/sentiment_summary.txt'
    print(f"Saving summary to {summary_file}...")
    
    with open(summary_file, 'w', encoding='utf-8') as f_summary:
        sentiment_counts = {"正面": 0, "中性": 0, "負面": 0}
        keyword_stats = {} # {keyword: {"正面": 0, "中性": 0, "負面": 0, "total": 0}}

        total_comments = 0
        for keyword, comments_data in results.items():
            if keyword not in keyword_stats:
                keyword_stats[keyword] = {"正面": 0, "中性": 0, "負面": 0, "total": 0}

            for item in comments_data:
                s = item.get('sentiment')
                
                # Global stats
                if s in sentiment_counts:
                    sentiment_counts[s] += 1
                total_comments += 1
                
                # Keyword stats
                if s in keyword_stats[keyword]:
                    keyword_stats[keyword][s] += 1
                keyword_stats[keyword]["total"] += 1
                
        # Helper to print to both console and file
        def print_both(text):
            print(text)
            f_summary.write(text + "\n")

        print_both("\nSentiment Analysis Summary:")
        print_both(f"Total comments processed: {total_comments}")
        for k, v in sentiment_counts.items():
            print_both(f"{k}: {v}")

        print_both("\nSentiment Distribution by Keyword:")
        print_both(f"{'Keyword':<15} | {'Positive':<10} | {'Neutral':<10} | {'Negative':<10} | {'Total':<8}")
        print_both("-" * 65)
        
        for keyword, stats in keyword_stats.items():
            total = stats["total"]
            if total > 0:
                pos_pct = (stats["正面"] / total) * 100
                neu_pct = (stats["中性"] / total) * 100
                neg_pct = (stats["負面"] / total) * 100
                print_both(f"{keyword:<15} | {pos_pct:>6.1f}%   | {neu_pct:>6.1f}%   | {neg_pct:>6.1f}%   | {total:>8}")
            else:
                print_both(f"{keyword:<15} | {'N/A':>8} | {'N/A':>8} | {'N/A':>8} | {total:>8}")

    print("Done.")

if __name__ == "__main__":
    main()
