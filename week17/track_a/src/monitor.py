import pandas as pd
import numpy as np
import os
import mlflow
from evidently import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset
from data_preprocessing import load_and_preprocess_data

def run_monitor():
    X_train, X_test, y_train, y_test, ref_df, cur_df = load_and_preprocess_data()
    
    # Inject Drift
    # 1. Shift MonthlyCharges
    noise = np.random.normal(20, 5, cur_df.shape[0])
    cur_df['MonthlyCharges'] += noise
    
    # 2. Oversample Contract == 2 (Month-to-month) to 80%
    contract_2_indices = cur_df[cur_df['Contract'] == 2].index
    other_indices = cur_df[cur_df['Contract'] != 2].index
    
    target_count = int(0.8 * len(cur_df))
    oversampled_contract_2 = np.random.choice(contract_2_indices, target_count, replace=True)
    other_samples = np.random.choice(other_indices, len(cur_df) - target_count, replace=True)
    
    cur_df = cur_df.loc[np.concatenate([oversampled_contract_2, other_samples])].reset_index(drop=True)
    
    # 3. Flip 10% of Churn labels
    flip_indices = np.random.choice(cur_df.index, size=int(0.1 * len(cur_df)), replace=False)
    cur_df.loc[flip_indices, 'Churn'] = 1 - cur_df.loc[flip_indices, 'Churn']
    
    # Compute custom metrics
    mean_mc_ref = ref_df['MonthlyCharges'].mean()
    mean_mc_cur = cur_df['MonthlyCharges'].mean()
    diff_mc = mean_mc_cur - mean_mc_ref
    
    churn_rate_ref = ref_df['Churn'].mean()
    churn_rate_cur = cur_df['Churn'].mean()
    diff_churn = churn_rate_cur - churn_rate_ref
    
    print(f"Mean MonthlyCharges difference: {diff_mc:.2f}")
    print(f"Churn rate difference: {diff_churn:.4f}")
    
    # Evidently Reports
    os.makedirs("reports", exist_ok=True)
    
    # 1. Data Drift Report (covers all features + target drift)
    data_drift_report = Report([DataDriftPreset()])
    data_drift_snapshot = data_drift_report.run(ref_df, cur_df)
    data_drift_path = "reports/data_drift.html"
    data_drift_snapshot.save_html(data_drift_path)
    print(f"Data drift report saved to {data_drift_path}")
    
    # 2. Data Summary Report (reference vs current distribution comparison)
    summary_report = Report([DataSummaryPreset()])
    summary_snapshot = summary_report.run(ref_df, cur_df)
    summary_path = "reports/data_summary.html"
    summary_snapshot.save_html(summary_path)
    print(f"Data summary report saved to {summary_path}")
    
    # Log to MLflow
    mlflow.set_experiment("telco-churn-monitoring")
    with mlflow.start_run():
        mlflow.log_artifact(data_drift_path)
        mlflow.log_artifact(summary_path)
        mlflow.log_metric("diff_monthly_charges", diff_mc)
        mlflow.log_metric("diff_churn_rate", diff_churn)
        mlflow.log_metric("mean_monthly_charges_ref", mean_mc_ref)
        mlflow.log_metric("mean_monthly_charges_cur", mean_mc_cur)
        mlflow.log_metric("churn_rate_ref", churn_rate_ref)
        mlflow.log_metric("churn_rate_cur", churn_rate_cur)
        
    print("\nInterpretation:")
    print("1. MonthlyCharges shows significant drift due to injected noise (+20 mean shift).")
    print("2. Contract shows distribution drift due to oversampling Month-to-month to 80%.")
    print("3. Target (Churn) drift is observed due to label flipping and feature drift.")
    print("Model retraining and data pipeline investigation is recommended.")

if __name__ == '__main__':
    run_monitor()
