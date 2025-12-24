#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import os
print("import OK!")


# In[2]:


import torch
# check device
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"目前使用的設備是: {device}")


# In[3]:


# Load data
input_file = 'fb_comments.json'
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

def preprocess(text):
    return " ".join(jieba.cut(text))

print(f"Clustering comments for {len(data)} keywords...")

cluster_results = {}

for keyword, comments in data.items():
    # Filter system messages
    comments = [c for c in comments if not c.startswith("通報 📢")]

    if len(comments) < 5: # Need a few comments to cluster
        continue

    corpus = [preprocess(c) for c in comments]

    try:
        vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        continue

    # Convert sparse matrix to dense
    X = tfidf_matrix.toarray()

    # Filter out empty vectors
    non_zero_indices = np.where(X.any(axis=1))[0]
    if len(non_zero_indices) < 2:
        continue

    X_filtered = X[non_zero_indices]
    comments_filtered = [comments[i] for i in non_zero_indices]

    clustering = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=0.2, # Similarity > 0.8
        metric='cosine',
        linkage='average'
    )

    try:
        clustering.fit(X_filtered)
    except Exception as e:
        print(f"Clustering failed for {keyword}: {e}")
        continue

    labels = clustering.labels_

    # Group comments by cluster
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(comments_filtered[i])

    # Filter out clusters with only 1 item (unique comments)
    suspicious_clusters = []
    for label, cluster_comments in clusters.items():
        if len(cluster_comments) > 1:
            suspicious_clusters.append({
                "size": len(cluster_comments),
                "comments": list(set(cluster_comments)) # Show unique texts in the cluster to see variations
            })

    if suspicious_clusters:
        cluster_results[keyword] = sorted(suspicious_clusters, key=lambda x: x['size'], reverse=True)

# Save results
output_file = 'jieba_comment_clusters.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(cluster_results, f, ensure_ascii=False, indent=4)

print(f"Clustering complete. Found suspicious clusters in {len(cluster_results)} keywords.")
print(f"Results saved to {output_file}")

# Print summary
for keyword, clusters in cluster_results.items():
    print(f"\nKeyword: {keyword} - Found {len(clusters)} suspicious clusters")
    for i, cluster in enumerate(clusters[:3]): # Show top 3 clusters
        print(f"  Cluster {i+1} (Size: {cluster['size']}):")
        for c in cluster['comments'][:2]: # Show first 2 unique comments
            print(f"    - {c[:50]}...")


# In[ ]:




