#!/usr/bin/env python
# coding: utf-8

# In[3]:


import json
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os


# In[7]:


# Load data
input_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'facebook_comments_by_keyword.json')
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = {}


# In[8]:


def preprocess(text):
    # Simple preprocessing: cut words
    return " ".join(jieba.cut(text))


# In[9]:


print(f"Analyzing {len(data)} keywords...")

for keyword, comments in data.items():
    # Filter out system messages
    comments = [c for c in comments if not c.startswith("通報 📢")]

    if len(comments) < 2:
        continue

    # Preprocess comments
    corpus = [preprocess(c) for c in comments]

    # TF-IDF Vectorization
    # Use character n-grams as well to capture exact phrasing better? 
    # For now, let's stick to word level, maybe add ngram_range=(1,2)
    try:
        vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Handle cases with empty vocabulary or stop words issues
        continue

    # Calculate Cosine Similarity
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Get upper triangle indices
    upper_tri_indices = np.triu_indices_from(sim_matrix, k=1)
    similarities = sim_matrix[upper_tri_indices]

    if len(similarities) == 0:
        continue

    # Statistics
    mean_sim = float(np.mean(similarities))
    max_sim = float(np.max(similarities))
    median_sim = float(np.median(similarities))

    # Count high similarity pairs
    high_sim_count_80 = int(np.sum(similarities > 0.8))
    high_sim_count_90 = int(np.sum(similarities > 0.9))

    # Find groups of identical or near-identical comments
    # We can use a simple approach: find connected components where edge weight > threshold
    # But for summary, just listing the top most similar pairs is good.

    # Find all similar pairs above threshold
    THRESHOLD = 0.8
    high_sim_indices = np.where(similarities > THRESHOLD)[0]

    # Sort by score descending
    sorted_indices = high_sim_indices[np.argsort(similarities[high_sim_indices])[::-1]]

    top_pairs = []
    for idx in sorted_indices:
        i = upper_tri_indices[0][idx]
        j = upper_tri_indices[1][idx]
        score = similarities[idx]
        top_pairs.append({
            "score": float(score),
            "comment_1": comments[i],
            "comment_2": comments[j]
        })

    results[keyword] = {
        "num_comments": len(comments),
        "mean_similarity": mean_sim,
        "median_similarity": median_sim,
        "max_similarity": max_sim,
        "pairs_gt_0.8": high_sim_count_80,
        "pairs_gt_0.9": high_sim_count_90,
        "top_similar_pairs": top_pairs
    }

# Sort results by mean similarity or max similarity to find suspicious ones
sorted_keywords = sorted(results.items(), key=lambda x: x[1]['mean_similarity'], reverse=True)

# Save results
output_file = 'similarity_analysis_results_ig.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"Analysis complete. Results saved to {output_file}")

# Print top 5 suspicious keywords based on mean similarity
print("\nTop 5 keywords with highest MEAN similarity:")
for k, v in sorted_keywords[:5]:
    print(f"Keyword: {k}, Mean Sim: {v['mean_similarity']:.4f}, Num Comments: {v['num_comments']}")

# Print top 5 suspicious keywords based on MAX similarity (potential copy-paste)
sorted_by_max = sorted(results.items(), key=lambda x: x[1]['max_similarity'], reverse=True)
print("\nTop 5 keywords with highest MAX similarity:")
for k, v in sorted_by_max[:5]:
    print(f"Keyword: {k}, Max Sim: {v['max_similarity']:.4f}, Num Comments: {v['num_comments']}")
    if v['top_similar_pairs']:
        print(f"  Top Pair ({v['top_similar_pairs'][0]['score']:.4f}):")
        print(f"    1: {v['top_similar_pairs'][0]['comment_1'][:50]}...")
        print(f"    2: {v['top_similar_pairs'][0]['comment_2'][:50]}...")


# In[ ]:




