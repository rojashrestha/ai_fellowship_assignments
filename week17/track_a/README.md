# Telco Customer Churn MLOps Project (Track A)

## a. Environment & Reproducibility (uv)
This project uses `uv` for lightning-fast, reproducible dependency management. `uv` ensures exact dependency pinning via the `uv.lock` file, eliminating "it works on my machine" issues. 
- **Setup**: To install all dependencies exactly as specified, simply run `uv sync`.
- `pyproject.toml` and `uv.lock` together guarantee a byte-identical virtual environment across all environments.

## b. Experiment Tracking Strategy (MLflow)
We trained 4 distinct models and tracked their configurations, metrics, and artifacts via MLflow:
1. **Logistic Regression** (Pipeline with StandardScaler, C=1.0, max_iter=2000, solver='lbfgs')
2. **Random Forest** (n_estimators=200, max_depth=10, random_state=42)
3. **Gradient Boosting** (n_estimators=150, max_depth=5, learning_rate=0.1)
4. **XGBoost** (n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric='logloss')

Because the churn dataset is inherently imbalanced (~26% positive class), accuracy is an unreliable metric. We rely primarily on **F1 Score** and **ROC-AUC** to compare models.

### Actual Metrics Comparison Table
| Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Run ID |
|-------|----------|-----------|--------|----------|---------|--------|
| **Logistic Regression** | **0.8005** | **0.6429** | **0.5615** | **0.5994** | **0.8355** | `cd9d872e4785434bb24b75b6a7b58142` |
| Random Forest | 0.7900 | 0.6347 | 0.4955 | 0.5566 | 0.8297 | `f591d9320dfb466490e746236f40f767` |
| Gradient Boosting | 0.7844 | 0.6194 | 0.4902 | 0.5473 | 0.8216 | `a17103b47bb64a1894ee9e0710f50e4b` |
| XGBoost | 0.7777 | 0.5970 | 0.5045 | 0.5469 | 0.8185 | `ce9ff50eb5c040a08c5a673f3cfcf335` |

**Model Registration**: Logistic Regression achieved the highest F1 Score (0.5994) and highest ROC-AUC (0.8355) on test data. The script automatically registered it in the MLflow Model Registry as `telco-churn-best`, transitioned it to `Staging`, and promoted it to `Production`.

## c. Monitoring & Drift Strategy (Evidently AI)
To simulate a real-world production drift scenario, the reference dataset is the training set, and the current dataset is perturbed with synthetic production drift:

**Injected Drift**:
1. **Numerical Feature Drift**: Shifted `MonthlyCharges` by adding Gaussian noise ($\mu=20, \sigma=5$), causing a mean difference of +14.66.
2. **Categorical Distribution Drift**: Oversampled the `Contract` feature so that Month-to-month contracts make up 80% of the distribution.
3. **Target / Concept Drift**: Randomly flipped 10% of `Churn` labels, simulating sudden external macroeconomic churn fluctuation.

**Evidently AI Reports**:
Generated in `reports/`:
- `reports/data_drift.html`: Identifies significant feature distribution drift using two-sample statistical tests.
- `reports/data_summary.html`: Provides column-level distribution summaries between reference and drifted current sets.
- Custom metrics logged to MLflow: `diff_monthly_charges` (+14.66), `diff_churn_rate` (-0.095).

## d. Orchestration — Optional Bonus (Airflow)
Located in [`dags/telco_churn_drift_dag.py`](file:///c:/Users/acer/Desktop/week17/track_a/dags/telco_churn_drift_dag.py):
- **DAG ID**: `telco_churn_drift_monitoring`
- **Schedule**: `@weekly` (Runs automated drift checks every Sunday midnight).
- **Trigger Condition**:
  - `evaluate_data_drift` task computes real-time distribution delta.
  - If `diff_monthly_charges > 10.0` or `diff_churn > 0.08`, branch to `trigger_retraining_pipeline`.
  - Otherwise, branch to `log_drift_healthy`.
- **Action on Drift**:
  - Automatically executes the end-to-end retraining pipeline across all 4 model architectures.
  - Re-evaluates candidate models on holdout sets and updates MLflow Model Registry if a new candidate surpasses the active Production model.

## e. How to Run
1. Install dependencies:
   ```bash
   uv sync
   ```
2. Start the MLflow UI:
   ```bash
   uv run mlflow ui
   ```
3. Run model training and registration:
   ```bash
   uv run python src/train.py
   ```
4. Run monitoring and drift report generation:
   ```bash
   uv run python src/monitor.py
   ```
5. Test the Airflow DAG:
   ```bash
   uv run python dags/telco_churn_drift_dag.py
   ```
6. Start the FastAPI inference service:
   ```bash
   uv run uvicorn src.serve:app --reload
   ```
