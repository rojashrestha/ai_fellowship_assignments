# Week 4: Linear Models for Telco Customer Churn

**AIF 2026 · Phase 2 · Statistical Machine Learning**

This project predicts which telecom customers are likely to leave (churn), so the retention team can call them before they go. It also predicts how long a customer will stay (tenure) and uses that to estimate customer lifetime value (CLV).

Only linear models are used, so every prediction can be explained.

---

## Dataset

- **Source:** [Telco Customer Churn (Kaggle)](https://www.kaggle.com/datasets/blastchar/telco-customer-churn), loaded with `kagglehub`
- **Size:** 7,043 customers × 21 columns (7,032 after cleaning)
- **Target:** `Churn` (Yes = 1, No = 0)
- **Class balance:** 73.4% stay, 26.6% leave. Because the classes are uneven, accuracy alone is misleading.

**Data fix:** `TotalCharges` had blank strings for 11 customers with tenure 0 (new customers who had not been billed yet). These were converted to `NaN` and dropped.

---

## Project structure (notebook blocks)

| Block | What it does |
|---|---|
| 1. Problem formulation | Defines X, y, model family, loss, and metric. Builds a naive "nobody churns" baseline |
| 2. Preprocessing | One-hot encoding (30 features), stratified 70/15/15 split, `StandardScaler` fit on train only |
| 3. Classification | Logistic Regression vs Ridge Classifier vs SGD Classifier, ROC/PR curves, top-200 threshold, coefficients, batch GD vs SGD |
| 4. Regression | Predicts tenure with Linear/Ridge/Lasso/ElasticNet, residual plots, Lasso path, CLV |
| 5. Evaluation checks | 5-fold stratified cross-validation, learning curves, leakage demo |
| 6. Production decision | Final test-set evaluation, model card, reflection |

---

## Results

### Naive baseline (always predicts "no churn")

| Accuracy | Recall | F1 |
|---|---|---|
| 0.734 | 0.000 | 0.000 |

73% accuracy, but it catches zero churners. This is why we use precision, recall, F1, and PR-AUC instead.

### Classifier comparison (validation set, threshold 0.5)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | Log Loss |
|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **0.825** | **0.697** | 0.605 | 0.648 | **0.853** | **0.654** | **0.411** |
| Ridge Classifier | 0.814 | 0.689 | 0.552 | 0.613 | 0.851 | 0.648 | 0.518 |
| SGD Classifier | 0.810 | 0.641 | **0.655** | **0.648** | 0.841 | 0.643 | 0.431 |

**Chosen model: Logistic Regression.** It has the best PR-AUC (the main metric for uneven classes) and the best log loss, so its probabilities are the most trustworthy for ranking customers.

### Business threshold: 200 calls per week

The retention team can only call 200 customers a week. The default 0.5 threshold would flag 244, so instead we call the top 200 by churn probability.

| Threshold | Precision | Recall |
|---|---|---|
| 0.554 (200th customer) | 0.72 | 0.51 |

72% of calls reach customers who were really about to leave, and we reach about half of all churners.

### Main churn drivers (logistic regression coefficients)

| Increases churn risk | Decreases churn risk |
|---|---|
| Month-to-month contract | Longer tenure |
| Fiber optic internet | One-year or two-year contract |
| Electronic check payment | |
| Paperless billing | |

### Batch GD vs SGD

| | Logistic Regression (L-BFGS) | SGD Classifier |
|---|---|---|
| ROC-AUC | 0.853 | 0.841 |
| Training time | 0.19 s | 0.18 s |

The predicted probabilities are highly correlated (0.95), but the coefficients differ by up to 0.54. SGD's noisy updates bounce around the best solution instead of settling exactly on it. At this data size, speed makes no real difference.

### Regression: predicting tenure

| MAE | RMSE | R² |
|---|---|---|
| 6.82 months | 8.73 months | 0.873 |

- **Residual plot:** slight fan shape. Errors grow for customers with longer tenure.
- **Lasso path:** contract type, fiber internet, and monthly charges survive the longest. Gender and phone service drop to zero early.
- **Predicted CLV** (`MonthlyCharges × predicted tenure`): mean $2,293, median $1,156. The median is lower because a few high-value customers pull the mean up.

> ⚠️ **Caution:** R² = 0.87 is too good for predicting human behaviour. `TotalCharges ≈ MonthlyCharges × tenure`, so the model can almost calculate tenure directly. For a brand-new customer, TotalCharges would not be known yet, so this feature should be removed for a real tenure model.

### Cross-validation (5-fold, stratified)

| Metric | CV mean ± std | Holdout validation |
|---|---|---|
| ROC-AUC | 0.848 ± 0.012 | 0.853 |
| PR-AUC | 0.671 ± 0.029 | 0.654 |

The spread is small and holdout matches CV, so the model is stable.

**Learning curves:** training and validation scores are close and flatten out. The model fits well. More data would help only a little, so bigger gains need better features or non-linear models.

### Leakage demo

A fake feature `leak = tenure × Churn + noise` was added on purpose.

| Model | ROC-AUC | PR-AUC |
|---|---|---|
| Baseline | 0.853 | 0.654 |
| With leakage | **0.998** | **0.996** |
| Leak removed | 0.853 | 0.654 |

The leak feature got the largest coefficient by far (13.1 vs 5.9 for the next one). **Cross-validation cannot catch this**, because the leaky feature is present in every fold. Only asking "would I know this value at prediction time?" catches it.

### Final test set (threshold 0.5)

| Precision | Recall | F1 | PR-AUC |
|---|---|---|---|
| 0.626 | 0.525 | 0.571 | 0.583 |

Test PR-AUC (0.58) is lower than CV PR-AUC (0.67). Part of this is likely because the test set is small (1,055 customers), but the drop should be watched after deployment.

---

## Model card

| Field | Answer |
|---|---|
| **Classification model** | Logistic Regression (`max_iter=1000`), retrained on train + validation |
| **Regression model** | Ridge (`alpha=1.0`) for tenure |
| **Test results** | Precision 0.63, Recall 0.53, F1 0.57, PR-AUC 0.58 |
| **Threshold** | Top 200 customers by churn probability each week |
| **Why** | Retention team capacity is 200 calls per week |
| **Limitations** | Uneven classes (27% churn). One snapshot in time, not tracked over months. Tenure model relies on TotalCharges, which leaks tenure |
| **Failure risks** | Customer behaviour changes (new competitor, price changes). Live data formatted differently from training data |
| **Monitoring** | Monthly: precision of the 200 calls, PR-AUC, and input feature averages. Retrain if PR-AUC drops below ~0.50 |

---

## Key takeaways

1. **Accuracy lies on uneven data.** A useless model gets 73%. Use PR-AUC, precision, and recall.
2. **Thresholds are business decisions.** We picked the cut-off from team capacity, not from 0.5.
3. **Fit preprocessing on train only.** Otherwise test data leaks into training.
4. **Lasso removes features, Ridge only shrinks them.**
5. **Too-good scores are a warning sign.** Check for leakage before celebrating.
6. **Linear models are a strong baseline.** They're fast, explainable, and hard to beat by much. Week 5 tests tree-based models against them.

---

## Known issues to fix in the notebook

- **3.1:** Ridge Classifier is labelled "squared hinge loss". It actually uses **squared loss** on ±1 labels. Squared hinge is LinearSVC.
- **3.1:** The claim that LR trains fastest isn't supported. LR and SGD both take ~0.19 s. Ridge is fastest (0.04 s).
- **3.2:** The markdown answer is a copy of 3.1.
- **3.4 / 4.5:** Some written answers use example numbers (e.g., threshold ~0.65, CLV ~$3,200) that don't match the real outputs (0.554, $2,293).
- **6.1:** "Validation PR-AUC = 0.66" is measured on data the final model was trained on, so it isn't a fair comparison. Compare test against the CV score instead.
- **6.2:** The model card table in the notebook is still empty.

---

## How to run

1. Open the notebook in Google Colab.
2. Run all cells in order. The dataset downloads automatically with `kagglehub`.
3. Libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `kagglehub`.
