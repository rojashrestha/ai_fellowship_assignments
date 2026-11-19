# Customer Segmentation Project — Final Technical Documentation

## What This Project Does

This project takes raw sales records from an online retail store (the UCI "Online Retail II" dataset, about 540,000 transactions) and groups the store's customers into segments based on how they shop. The store had never grouped its customers before — there were no existing labels saying "this customer is high-value" or "this customer is at risk of leaving." The job was to find these groups using unsupervised machine learning (clustering), then explain each group in plain business language so a marketing team can act on it.

Three different clustering methods were used and compared: **K-Means**, **Hierarchical (Agglomerative) Clustering**, and **DBSCAN**.

---

## 1. Environment Setup

The project runs in **Google Colab**. The dataset is downloaded fresh inside the notebook each session (since Colab's storage resets between sessions) using `urllib` and `zipfile`. The Excel file is read with the `python-calamine` engine instead of the default `openpyxl`, since the file has 540,000+ rows and the default engine was far too slow.

---

## 2. Loading and First Look at the Data

The raw dataset has **541,910 rows and 8 columns**. Key observations before cleaning:

- Only **25,900 unique invoice numbers** exist, meaning each row is one product line within an order, not one full transaction.
- **About 25% of rows (135,080) are missing a Customer ID** — likely guest purchases.
- `Quantity` and `Price` both contain **negative values**, signaling returns, cancellations, or data errors.
- Both fields are heavily skewed, with a small number of very large values suggesting bulk/wholesale buyers.

---

## 3. Data Cleaning

Five cleaning steps removed **144,025 rows total** (541,910 → 397,885 remaining): rows with missing Customer ID (135,080), cancelled invoices (8,905), non-positive Quantity/Price (40), plus a datetime conversion and a new `TotalPrice` column (Quantity × Price).

---

## 4. Building Customer Features (RFM)

The cleaned, line-item-level data was reshaped into **one row per customer** using three core features:

- **Recency** — days since last purchase, measured from one day after the latest date in the dataset.
- **Frequency** — number of unique invoices per customer.
- **Monetary** — total spend (sum of `TotalPrice`) per customer.

---

## 5. Handling Outliers and Scaling

`Frequency` and `Monetary` were both extremely right-skewed, so both were **log-transformed** (`log(x+1)`) to compress the gap between typical and extreme customers without deleting potentially genuine high-value buyers. `Recency` was left unchanged, since its skew was moderate.

All three features (`Recency`, `Frequency_log`, `Monetary_log`) were then scaled with **StandardScaler** so no single feature would dominate distance calculations.

---

## 6. K-Means Clustering

Testing k from 2–10, both the **Elbow Method** and **Silhouette Score** pointed to **k=3**. Comparing `random` vs. `k-means++` initialization across 5 runs each showed k-means++ was more consistent (std=0.02 vs. 0.06), though both were stable overall — a sign the data has a genuinely strong 3-cluster structure.

The final model produced three clear, business-meaningful segments:

| Segment | Recency (days) | Frequency (orders) | Monetary ($) |
|---|---|---|---|
| High-Value Champions | 30.1 | 9.83 | 5,494 |
| Mid-Tier Growth Seekers | 54.9 | 2.05 | 615 |
| Lapsed Dormants | 255.3 | 1.39 | 398 |

---

## 7. Hierarchical Clustering

A dendrogram built on a 300-customer sample showed the largest merge gap at **3 clusters**, matching K-Means. Ward linkage produced balanced cluster sizes (1,937 / 1,528 / 873); Complete linkage produced one dominant cluster and two small ones (2,970 / 797 / 571). Ward was preferred for being more actionable.

---

## 8. DBSCAN

A k-distance plot suggested an epsilon around 0.4. Testing eps=0.32, 0.40, and 0.48 (min_samples=5) gave 7, 4, and 2 clusters respectively, with noise percentages of 3.30%, 1.96%, and 1.22%. **Eps=0.40 was chosen**, balancing cluster count against fragmentation.

Noise points (85 customers, ~2%) were investigated rather than discarded — they include high-spending outliers (likely VIP/wholesale accounts), high-frequency "power users," and long-lapsed one-time buyers. The recommendation was to treat them as a separate "Anomaly" segment with tailored marketing, rather than forcing them into a standard cluster.

---

## 9. Cluster Validation

| Method | Clusters | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Index |
|---|---|---|---|---|
| K-Means | 3 | 0.4156 | 0.8247 | 4,394.52 |
| Hierarchical (Ward) | 3 | 0.3959 | 0.8455 | 4,031.98 |
| DBSCAN | 4 | 0.1553 | 1.3904 | 1,447.29 |

(Higher Silhouette = better, lower Davies-Bouldin = better, higher Calinski-Harabasz = better. DBSCAN's score excludes noise points, so it isn't directly comparable to the other two.)

**K-Means with k=3 was chosen as the final segmentation** — it had the best Davies-Bouldin score, a strong Silhouette and Calinski-Harabasz score, is reproducible (deterministic given a seed), and its 3 segments map cleanly to actionable business personas. Hierarchical (Ward) independently converging on the same k=3 structure served as cross-validation that this is a real pattern in the data, not an artifact of one algorithm.

---

## 10. Business Narrative

**High-Value Champions** — the most engaged, highest-spending tier (avg. ~10 orders, ~$5,494 spent, purchased within the last month). *Action:* exclusive VIP loyalty program with dedicated support and early access to new products.

**Mid-Tier Growth Seekers** — moderate, occasional spenders (avg. ~2 orders, ~$615 spent, last purchase ~2 months ago) who trust the brand but haven't reached full potential. *Action:* targeted cross-selling and low-threshold incentives (e.g. free shipping over $50).

**Lapsed Dormants** — inactive, low-value customers who haven't purchased in over 8 months on average, with the lowest spend and frequency. *Action:* a "win-back" email campaign with a steep limited-time discount, paired with a short survey to learn why they stopped buying.

**Executive summary:** The RFM-based clustering gives the marketing team a data-driven way to replace generic campaigns with three targeted strategies — retaining Champions, growing Mid-Tier customers, and winning back Lapsed Dormants — improving both marketing efficiency and customer retention.

---

## 11. Failure Log (3 documented hypotheses that didn't go as expected)

1. **Expected** random K-Means initialization to be highly unstable vs. k-means++. **Found** both were nearly equally stable on this dataset (std 0.06 vs 0.02, tiny relative to inertia ~4,298) — because the underlying cluster structure is unusually well-separated.
2. **Expected** a small DBSCAN epsilon to cleanly isolate tight sub-groups and a large epsilon to capture broad segments with minimal noise. **Found** small epsilon over-fragmented the data (7 clusters) and large epsilon over-merged it (2 clusters) — epsilon needed careful tuning around business-relevant cluster counts.
3. **Expected** StandardScaler alone (without log transform) to be sufficient preprocessing. **Found** extreme outliers in Monetary still dominated distance calculations even after scaling — log transform was a necessary step before scaling, not optional.

---

*This documentation reflects the completed Week 7 clustering assignment as of June 21, 2026.*
