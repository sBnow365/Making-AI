import os
import numpy as np
import pandas as pd
import seaborn as sns
from backend import extract_text, preprocess_image
from tqdm import tqdm
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib
import matplotlib.pyplot as plt

# Set matplotlib backend
matplotlib.use('TkAgg')

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

# Additional metrics
lev_distances = []
word_lengths = []
is_correct = []
wrong_predictions = []  # To store details of incorrect predictions

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

    print("Predicted: ", pred)
    print("Actual: ", gt)

    # Word-level accuracy
    word_correct = pred == gt
    if word_correct:
        correct_words += 1
    else:
        wrong_predictions.append({
            'filename': img_file,
            'predicted': pred,
            'ground_truth': gt
        })

    # Character-level stats
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

    # Pad strings
    max_len = max(len(gt), len(pred))
    gt_padded = gt.ljust(max_len)
    pred_padded = pred.ljust(max_len)

    y_true_chars.extend(list(gt_padded))
    y_pred_chars.extend(list(pred_padded))

    # Word length stats
    word_lengths.append(len(gt))
    is_correct.append(1 if word_correct else 0)

# Clean padding-only characters
filtered = [(t, p) for t, p in zip(y_true_chars, y_pred_chars) if t.strip() != '' or p.strip() != '']
y_true_chars, y_pred_chars = zip(*filtered) if filtered else ([], [])

# Final calculations
word_accuracy = (correct_words / total) * 100
char_accuracy = (correct_chars / total_chars) * 100 if total_chars > 0 else 0
avg_lev_distance = lev_dist_sum / total if total > 0 else 0

# Precision, Recall, F1
precision = precision_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)
recall = recall_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)
f1 = f1_score(y_true_chars, y_pred_chars, average='micro', zero_division=0)

# Print metrics
print("\n📊 OCR Evaluation Metrics:")
print(f"✅ Word-Level Accuracy:     {word_accuracy:.2f}%")
print(f"🔠 Character-Level Accuracy: {char_accuracy:.2f}%")
print(f"✏ Avg Levenshtein Distance: {avg_lev_distance:.2f}")
print(f"🎯 Precision:                {precision:.4f}")
print(f"📈 Recall:                   {recall:.4f}")
print(f"🏆 F1 Score:                 {f1:.4f}")

# Print detailed wrong predictions
if wrong_predictions:
    print("\n❌ Incorrect Predictions:")
    for item in wrong_predictions:
        print(f"\n🖼 Image: {item['filename']}")
        print(f"🔮 Predicted:     {item['predicted']}")
        print(f"📌 Ground Truth:  {item['ground_truth']}")
else:
    print("\n✅ All predictions were correct!")

# Character Confusion Matrix
if len(set(y_true_chars)) <= 100:
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