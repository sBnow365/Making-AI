import os
import numpy as np
import pandas as pd
import seaborn as sns
from backend import extract_text, preprocess_image
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib
import matplotlib.pyplot as plt

# Set matplotlib backend (try different options if this doesn't work)
matplotlib.use('TkAgg')  # Alternatives: 'Qt5Agg', 'GTK3Agg', 'WebAgg'

# Dataset paths
img_dir = 'dataset/img'
gt_dir = 'dataset/text'

# File list
image_files = sorted([f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
total = len(image_files)
print(f"Total images: {total}")

# Evaluation stats
correct_words = 0
total_chars = 0
correct_chars = 0
lev_dist_sum = 0
y_true_chars = []
y_pred_chars = []

# Additional metrics collections
lev_distances = []
word_lengths = []
is_correct = []

for img_file in tqdm(image_files, total=total):
    img_path = os.path.join(img_dir, img_file)
    file_id = os.path.splitext(img_file)[0]
    gt_path = os.path.join(gt_dir, f"{file_id}.txt")

    if not os.path.exists(gt_path):
        print(f"Missing ground truth for: {img_file}")
        continue

    with open(gt_path, 'r', encoding='utf-8') as f:
        gt = f.read().strip().lower()

    _, processed, _ = preprocess_image(img_path)
    if processed is None:
        print(f"Failed to process image: {img_file}")
        continue

    pred = extract_text(processed).strip().lower()
    
    # Word-level accuracy
    word_correct = pred == gt
    if word_correct:
        correct_words += 1
    
    # Character-level stats
    min_len = min(len(pred), len(gt))
    correct_chars += sum(p == g for p, g in zip(pred, gt))
    total_chars += len(gt)

    # Levenshtein distance
    def levenshtein_distance(s1, s2):
        len_s1, len_s2 = len(s1), len(s2)
        dp = np.zeros((len_s1 + 1, len_s2 + 1), dtype=int)
        for i in range(len_s1 + 1):
            dp[i][0] = i
        for j in range(len_s2 + 1):
            dp[0][j] = j
        for i in range(1, len_s1 + 1):
            for j in range(1, len_s2 + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1,
                               dp[i][j - 1] + 1,
                               dp[i - 1][j - 1] + cost)
        return dp[len_s1][len_s2]
    
    lev_dist = levenshtein_distance(pred, gt)
    lev_dist_sum += lev_dist
    lev_distances.append(lev_dist)

    # For precision/recall/F1: character-wise comparison
    y_true_chars.extend(list(gt))
    y_pred_chars.extend(list(pred[:len(gt)]))  # match length

    # For word length analysis
    word_lengths.append(len(gt))
    is_correct.append(1 if word_correct else 0)

# Final calculations
word_accuracy = (correct_words / total) * 100
char_accuracy = (correct_chars / total_chars) * 100 if total_chars > 0 else 0
avg_lev_distance = lev_dist_sum / total if total > 0 else 0

# Precision, Recall, F1 (char-wise)
precision = precision_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)
recall = recall_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)
f1 = f1_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)

# Print metrics
print("\n📊 OCR Evaluation Metrics:")
print(f"✅ Word-Level Accuracy:     {word_accuracy:.2f}%")
print(f"🔠 Character-Level Accuracy: {char_accuracy:.2f}%")
print(f"✏️ Avg Levenshtein Distance: {avg_lev_distance:.2f}")
print(f"🎯 Precision:                {precision:.4f}")
print(f"📈 Recall:                   {recall:.4f}")
print(f"🏆 F1 Score:                 {f1:.4f}")



# Character Error Heatmap (if character set is small)
if len(set(y_true_chars)) <= 30:
    chars = sorted(set(y_true_chars))
    cm = confusion_matrix(y_true_chars, y_pred_chars, labels=chars)
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=chars, yticklabels=chars,
                cbar_kws={'label': 'Number of Errors'})
    plt.title('Character Confusion Matrix', fontweight='bold')
    plt.xlabel('Predicted Characters')
    plt.ylabel('True Characters')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()

