"""Airflow DAG for Track A: Telco Customer Churn Drift Monitoring & Automated Retraining.

Schedule: Weekly (@weekly)
Trigger Condition: Triggers retraining if feature/target drift exceeds tolerance threshold.
"""

from datetime import datetime, timedelta
import os
import sys

# Airflow standard imports with fallback mocks for standalone local testing
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator, BranchPythonOperator
    from airflow.operators.empty import EmptyOperator
except ImportError:
    # Lightweight shim for environments where Airflow is run via container or CLI
    class DAG:
        def __init__(self, dag_id, *args, **kwargs):
            self.dag_id = dag_id
            self.default_args = kwargs.get("default_args")
            self.schedule_interval = kwargs.get("schedule_interval")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class PythonOperator:
        def __init__(self, task_id, python_callable, op_kwargs=None, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable
            self.op_kwargs = op_kwargs or {}

        def __rshift__(self, other):
            return other

    class BranchPythonOperator(PythonOperator):
        pass

    class EmptyOperator:
        def __init__(self, task_id, **kwargs):
            self.task_id = task_id

        def __rshift__(self, other):
            return other


# Add track_a root to sys.path so project modules can be loaded
TRACK_A_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if TRACK_A_ROOT not in sys.path:
    sys.path.insert(0, TRACK_A_ROOT)


def check_drift_and_evaluate(**context):
    """Run Evidently drift detection and determine if retraining is warranted."""
    import numpy as np
    import pandas as pd
    from src.data_preprocessing import load_and_preprocess_data
    from evidently import Report
    from evidently.presets import DataDriftPreset
    import mlflow

    print("Executing scheduled drift check...")
    _, _, _, _, ref_df, cur_df = load_and_preprocess_data()

    # In production, cur_df represents the recent inference window.
    # Run Evidently DataDriftPreset report
    report = Report([DataDriftPreset()])
    snapshot = report.run(ref_df, cur_df)

    reports_dir = os.path.join(TRACK_A_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "scheduled_data_drift.html")
    snapshot.save_html(report_path)

    # Compute key drift statistics
    mean_ref = ref_df["MonthlyCharges"].mean()
    mean_cur = cur_df["MonthlyCharges"].mean()
    diff_mc = abs(mean_cur - mean_ref)

    churn_ref = ref_df["Churn"].mean()
    churn_cur = cur_df["Churn"].mean()
    diff_churn = abs(churn_cur - churn_ref)

    print(f"MonthlyCharges shift: {diff_mc:.2f} | Churn rate shift: {diff_churn:.4f}")

    # Threshold condition for drift alert/retraining
    DRIFT_THRESHOLD_MONTHLY_CHARGES = 10.0
    DRIFT_THRESHOLD_CHURN = 0.08

    is_drifted = (diff_mc > DRIFT_THRESHOLD_MONTHLY_CHARGES) or (diff_churn > DRIFT_THRESHOLD_CHURN)

    if is_drifted:
        print("[ALERT] Significant data/target drift detected! Branching to retraining pipeline.")
        return "trigger_retraining_pipeline"
    else:
        print("[OK] Data distributions remain healthy. No retraining needed.")
        return "log_drift_healthy"


def execute_retraining(**context):
    """Execute model retraining when drift is confirmed."""
    from src.train import train_models
    print("Initiating automated retraining across model candidates...")
    train_models()
    print("Retraining completed successfully. Production candidate registered in MLflow Model Registry.")


def log_healthy_status(**context):
    """Log verification when no drift is observed."""
    print("Drift check passed with normal tolerances. Model in production remains active.")


default_args = {
    "owner": "mlops_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="telco_churn_drift_monitoring",
    default_args=default_args,
    description="Weekly automated drift detection and conditional retraining for Telco Customer Churn",
    schedule_interval="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mlops", "track_a", "monitoring", "evidently", "mlflow"],
) as dag:

    start_task = EmptyOperator(task_id="start_pipeline")

    drift_check_task = BranchPythonOperator(
        task_id="evaluate_data_drift",
        python_callable=check_drift_and_evaluate,
    )

    retrain_task = PythonOperator(
        task_id="trigger_retraining_pipeline",
        python_callable=execute_retraining,
    )

    healthy_task = PythonOperator(
        task_id="log_drift_healthy",
        python_callable=log_healthy_status,
    )

    end_task = EmptyOperator(task_id="end_pipeline")

    start_task >> drift_check_task
    drift_check_task >> retrain_task >> end_task
    drift_check_task >> healthy_task >> end_task
