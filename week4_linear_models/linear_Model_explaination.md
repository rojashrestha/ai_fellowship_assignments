# Telco Customer Churn – Linear Models Assignment  
## Complete Explanation of All Topics and Terms

This document explains every concept, model, metric, and step used in the assignment. It is designed to help you understand the theory behind the code.

---

## 1. Problem Formulation (Block 1)

### What is an ML Problem?

Every machine learning problem has five formal components:

| Symbol | Name | Meaning |
|--------|------|---------|
| **X** | Feature space | All input columns used to make predictions (e.g., tenure, contract type, monthly charges) |
| **y** | Target variable | What we want to predict (Churn: Yes/No) |
| **H** | Hypothesis class | The family of functions we search over (here: linear models) |
| **L** | Loss function | Measures how wrong the prediction is (e.g., binary cross-entropy) |
| **E** | Evaluation metric | How business success is measured (e.g., PR-AUC, recall, F1) |

### Empirical Risk Minimisation (ERM)

We cannot minimise the true risk (because we don’t have all possible data), so we minimise the **average loss over the training set** as a proxy:
training data ma model le gareko mistake or error lai sakesamma kam banaune parameter khojchau teslai nai erm vancha 

$$\hat{\theta} = \arg\min_{\theta} \frac{1}{n} \sum_{i=1}^{n} L(y_i, f_\theta(x_i))$$

### Probability Distributions and Loss Functions

The distribution of the target determines the correct loss:

| Distribution | Example | Loss function |
|--------------|---------|----------------|
| Bernoulli | Binary Churn (Yes/No) | Binary cross-entropy |
| Gaussian | MonthlyCharges | Mean Squared Error (MSE) |
| Poisson | Count of support tickets | Poisson deviance |
| Gamma / Log-Normal | Right-skewed continuous (TotalCharges) | MAE / Tweedie |

**Key insight:** Churn is binary → Bernoulli → binary cross-entropy is the natural loss.

### Sources of Uncertainty

- **Sampling noise** – 7043 customers may not represent all customers.
- **Label noise** – Churn may be recorded incorrectly.
- **Missing data** – `TotalCharges` has whitespace nulls.
- **Biased sampling** – Data might not cover all regions/plans.
- **Distribution shift** – Customer behaviour may change over time.
- **Model misspecification** – Linear boundary may be wrong.

---

## 2. Data Inspection & Cleaning (Block 1.1 – 1.3)

### Key Terms

- **`df.shape`** – Number of rows and columns.
- **`df.head()`** – First 5 rows to see sample data.
- **`df.info()`** – Data types and non-null counts.
- **`df.describe()`** – Summary statistics (mean, std, min, max, quartiles).
- **`pd.to_numeric(..., errors='coerce')`** – Converts a column to numbers; invalid entries become `NaN`.
- **`df.dropna()`** – Removes rows with missing values.

### Why `TotalCharges` is object and has nulls

The dataset contains whitespace strings `' '` instead of numbers. This is a common data quality issue. We fix it by converting to numeric (coerce errors to NaN) and then dropping those rows.

### Encode target variable

`Churn` is given as `'Yes'`/`'No'`. We map to `1`/`0` so that scikit-learn can process it.

---

## 3. Naive Baseline (Block 1.4)

### What is a naive baseline?

A simple model that always predicts the majority class (No Churn). It serves as a sanity check.

- **Accuracy** = proportion of correct predictions (≈73%).
- **Recall** = TP / (TP + FN) = 0 because it never predicts churn.
- **F1** = harmonic mean of precision and recall = 0.

**Why it's worthless:** It catches no churners. The business would waste retention budget.

---

## 4. Evaluation Metrics for Imbalanced Data (Block 3)

### Confusion Matrix

| Actual \ Predicted | No Churn (0) | Churn (1) |
|--------------------|--------------|------------|
| No Churn (0) | TN | FP |
| Churn (1) | FN | TP |

### Metrics

- **Accuracy** = (TP + TN) / (TP + TN + FP + FN) – not reliable for imbalanced data.
- **Precision** = TP / (TP + FP) – Of those predicted churn, how many actually churned?
- **Recall (Sensitivity)** = TP / (TP + FN) – Of actual churners, how many did we catch?
- **F1 Score** = 2 × (Precision × Recall) / (Precision + Recall) – Harmonic mean, balances both.
- **ROC-AUC** – Area under the ROC curve (True Positive Rate vs False Positive Rate). Measures ranking ability.
- **PR-AUC** – Area under the Precision-Recall curve. **Preferred for imbalanced data** because it focuses on the positive (churn) class.
- **Log Loss** – Penalises overconfident wrong predictions. Measures probability calibration.

### Precision-Recall vs ROC

ROC can be optimistic when the positive class is rare because it includes many true negatives. PR-AUC is more sensitive to the minority class.

---

## 5. Classification Models (Block 3)

### Logistic Regression

- **Loss function:** Binary cross-entropy (log loss).
- **Optimiser:** Batch gradient descent (L-BFGS) – uses full dataset for each step.
- **Output:** Calibrated probabilities.
- **Interpretability:** Coefficients represent change in log-odds.

### Ridge Classifier

- **Loss function:** Squared hinge loss (treats classification as regression with L2 penalty).
- **Output:** Decision function (can be converted to pseudo-probabilities but not true probabilities).
- **No probability output** → less useful for threshold tuning.

### SGD Classifier

- **Loss function:** Configurable (e.g., `log_loss` for logistic regression).
- **Optimiser:** Stochastic Gradient Descent – updates weights one sample (or mini-batch) at a time.
- **Advantage:** Scales to very large datasets.
- **Disadvantage:** Noisy convergence; may not reach exact optimum.

### Batch vs Stochastic Gradient Descent

- **Batch GD:** Computes gradient over all training examples. Stable but memory-intensive.
- **SGD:** Uses one sample per update. Fast and memory-efficient; can escape local minima but produces noisy path.

---

## 6. Threshold Tuning (Block 3.4)

### Business constraint

Retention team can only call **200 customers per week**. So we don't use the default 0.5 threshold.

### Strategy

1. Sort all customers by predicted churn probability (descending).
2. Take the top 200.
3. The threshold = the probability of the 200th customer.
4. Evaluate precision and recall on that threshold.

### Why not default 0.5?

Default threshold may flag more than 200 (or fewer) and does not respect the budget.

---

## 7. Coefficient Interpretation (Block 3.5)

Logistic regression coefficients are in **log-odds**:

- Positive coefficient → increase in feature increases churn risk.
- Negative coefficient → increase in feature decreases churn risk.

**Example:** `Contract_Month-to-month` has positive coefficient → month‑to‑month customers are more likely to churn.

### Feature importance

We look at **absolute coefficients** – larger magnitude means stronger influence.

---

## 8. Regression Models (Block 4)

### Target options

- **A – Tenure (survival time):** Predict how many months a customer stays.
- **B – Churn probability score:** Use classifier’s output as target.
- **C – Customer Lifetime Value (CLV):** CLV = MonthlyCharges × predicted tenure.

### Linear regression family

| Model | Penalty | Effect |
|-------|---------|--------|
| LinearRegression | None | Unconstrained, can overfit |
| Ridge (L2) | λ Σ β² | Shrinks coefficients towards 0 but never exactly 0 |
| Lasso (L1) | λ Σ |β| | Some coefficients become exactly 0 → sparse |
| Elastic Net | λ₁ Σ |β| + λ₂ Σ β² | Combines L1 and L2 |

### Regression metrics

- **MAE** = Mean Absolute Error – average error in original units. Robust to outliers.
- **RMSE** = Root Mean Squared Error – penalises large errors more.
- **R²** = Coefficient of determination – proportion of variance explained by the model.

**Interpretation of R² = 0.55:** The model explains 55% of the variance in tenure. The remaining 45% is unexplained.

### Residual plots

Residuals = actual – predicted. Ideal: randomly scattered around zero.

- **Fan shape** → heteroscedasticity (variance increases with prediction).
- **Curve** → non‑linear relationship not captured.

### Regularisation geometry

- **L2 (Ridge) constraint** = circle → touches loss contours at curved edge → coefficients shrink but never zero.
- **L1 (Lasso) constraint** = diamond → touches at corners → coefficients become exactly zero (sparse).

### Elastic Net

Preferred when features are highly correlated. Lasso may pick only one from a correlated group; Elastic Net tends to keep groups.

### CLV (Customer Lifetime Value)

- **What it enables:** Rank customers by **expected revenue loss** not just churn risk.
- A high‑value customer with moderate churn risk may be more important than a low‑value customer with high risk.

---

## 9. Evaluation Integrity (Block 5)

### Cross-validation

- **Stratified K‑Fold:** Splits data into K folds while preserving class distribution. Each fold is used once as validation.
- **Why:** Reduces variance of performance estimate; more reliable than a single holdout.
- **High variance across folds** → model is sensitive to which data it sees.

### Learning curves

Plot training and validation scores against training set size.

- **Underfitting:** Both scores low and plateau.
- **Overfitting:** Training score high, validation low.
- **Good fit:** Both high and close together; adding more data helps.

### Data leakage

**Definition:** Information from outside the training window (e.g., future events) is used to train the model.

**Examples:**
- Target leakage: `tenure × Churn` – `Churn` is not known at prediction time.
- Train-test contamination: Scaling on full data before split.
- Temporal leakage: Using future billing data to predict past churn.

**Consequences:** Model looks excellent in development but fails in production because the leaked feature is not available.

**Leakage demo:** Adding `tenure * Churn + noise` inflates ROC-AUC from ~0.84 to >0.99. The leakage feature dominates coefficients. Cross-validation does **not** detect it because the feature exists in every fold.

---

## 10. Production Decision (Block 6)

### Model Card

A document that must be filled before deployment. Contains:

- Chosen model and hyperparameters
- Key metrics on test set
- Threshold and justification
- Known limitations
- Failure modes
- Monitoring plan

### Are linear models sufficient?

**Stick with linear when:**
- Interpretability is required (e.g., regulated industries)
- Dataset is small
- Linear model already meets business performance

**Go complex when:**
- Learning curves show underfitting
- Strong non‑linear interactions exist
- Tree‑based baseline significantly outperforms

### Final evaluation on test set

- Only run after all decisions are made.
- Compare test metrics to validation metrics.
- A big drop → overfitting to validation set.

---

## 11. Final Reflection Questions – Short Answers

1. **Model Selection:** Logistic Regression performed best (highest PR-AUC and calibration). SGD had higher recall but lower precision; we resolved by prioritising PR-AUC and top‑200 precision.

2. **Evaluation Choices:** Reported PR-AUC, recall, precision, F1, log loss – because accuracy hides poor recall on minority class. Only accuracy would have hidden that we catch only 55% of churners.

3. **Regularization:** Lasso path showed that month‑to‑month contract, fiber optic, paperless billing are strongest features. Biggest difference between Ridge and Lasso at high alpha: Lasso zeros coefficients, Ridge only shrinks.

4. **Leakage:** AUC inflated by >0.15. Cross-validation cannot detect it because leakage exists in all folds. Only business logic (asking if feature is available at prediction time) can catch it.

5. **Improvements:** Try feature engineering (interactions), non‑linear models (Random Forest). Evidence: learning curves show no overfitting, but small performance gain possible.

---

## 12. Summary Table

| Topic | Key Takeaway |
|-------|---------------|
| Problem Formulation | X, y, hypothesis class, loss, metric – each is a formal commitment |
| Distributions & Loss | The distribution of y determines your loss. Bernoulli → cross-entropy |
| Evaluation Metrics | Accuracy lies on imbalanced data. Use PR-AUC |
| Linear Models & GD | Three classifiers; each optimises a different objective |
| Generalisation | Low training error means nothing. Learning curves tell the truth |
| Regularization | L1 is sparse, L2 is stable, Elastic Net is both |
| Leakage | One future feature inflated AUC – and kills the model in production |
| Production Decision | Model card = commitment; if you cannot fill it, you are not ready to ship |

---

**End of document**