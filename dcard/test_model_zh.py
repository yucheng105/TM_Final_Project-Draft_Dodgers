from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

def test_model():
    model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    print(f"Testing model: {model_name}", flush=True)
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        
        test_sentences = [
            "這部電影真的很好看！", # Positive
            "我覺得很普通，沒什麼特別的。", # Neutral
            "真是太糟糕了，浪費我的時間。", # Negative
            "今天天氣不錯", # Positive/Neutral
            "我好難過" # Negative
        ]
        
        print("\nTest Results:", flush=True)
        for sentence in test_sentences:
            result = sentiment_pipeline(sentence)[0]
            print(f"Text: {sentence}", flush=True)
            print(f"Label: {result['label']}, Score: {result['score']:.4f}", flush=True)
            print("-" * 30, flush=True)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_model()
