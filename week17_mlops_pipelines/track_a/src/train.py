import mlflow
import mlflow.sklearn
import mlflow.pyfunc
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, ConfusionMatrixDisplay, RocCurveDisplay
import matplotlib.pyplot as plt
import pandas as pd
import os
from data_preprocessing import load_and_preprocess_data

# Trust sklearn/xgboost types for mlflow's skops serialization
SKOPS_TRUSTED = [
    "sklearn.tree._tree.Tree",
    "sklearn.preprocessing._label.LabelBinarizer",
    "numpy.dtype",
    "xgboost.core.Booster",
    "xgboost.sklearn.XGBClassifier",
]

def eval_metrics(actual, pred, pred_proba):
    accuracy = accuracy_score(actual, pred)
    precision = precision_score(actual, pred)
    recall = recall_score(actual, pred)
    f1 = f1_score(actual, pred)
    roc_auc = roc_auc_score(actual, pred_proba)
    return accuracy, precision, recall, f1, roc_auc

def train_models():
    X_train, X_test, y_train, y_test, _, _ = load_and_preprocess_data()
    
    mlflow.set_experiment("telco-churn-mlops")
    
    models = {
        "Logistic Regression": (Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(C=1.0, max_iter=2000, solver='lbfgs'))]), {"C": 1.0, "max_iter": 2000, "solver": "lbfgs", "scaler": "StandardScaler"}),
        "Random Forest": (RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42), {"n_estimators": 200, "max_depth": 10, "random_state": 42}),
        "Gradient Boosting": (GradientBoostingClassifier(n_estimators=150, max_depth=5, learning_rate=0.1), {"n_estimators": 150, "max_depth": 5, "learning_rate": 0.1}),
        "XGBoost": (XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric='logloss'), {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1, "eval_metric": "logloss"})
    }
    
    results = []
    best_f1 = -1
    best_run_id = None
    best_model_name = None
    
    os.makedirs("artifacts", exist_ok=True)
    
    for name, (model, params) in models.items():
        with mlflow.start_run(run_name=name):
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            pred_proba = model.predict_proba(X_test)[:, 1]
            
            accuracy, precision, recall, f1, roc_auc = eval_metrics(y_test, pred, pred_proba)
            
            mlflow.log_params(params)
            mlflow.log_metrics({"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1, "roc_auc": roc_auc})
            mlflow.set_tag("model_type", name)
            
            # Plots
            fig_cm, ax_cm = plt.subplots()
            ConfusionMatrixDisplay.from_predictions(y_test, pred, ax=ax_cm)
            cm_path = f"artifacts/{name.replace(' ', '_')}_cm.png"
            plt.savefig(cm_path)
            mlflow.log_artifact(cm_path)
            plt.close(fig_cm)
            
            fig_roc, ax_roc = plt.subplots()
            RocCurveDisplay.from_predictions(y_test, pred_proba, ax=ax_roc)
            roc_path = f"artifacts/{name.replace(' ', '_')}_roc.png"
            plt.savefig(roc_path)
            mlflow.log_artifact(roc_path)
            plt.close(fig_roc)
            
            mlflow.sklearn.log_model(model, "model", skops_trusted_types=SKOPS_TRUSTED)
            
            run_id = mlflow.active_run().info.run_id
            results.append({
                "Model": name, "Accuracy": accuracy, "Precision": precision, 
                "Recall": recall, "F1": f1, "ROC-AUC": roc_auc, "Run ID": run_id
            })
            
            if f1 > best_f1:
                best_f1 = f1
                best_run_id = run_id
                best_model_name = name

    # Results table
    results_df = pd.DataFrame(results)
    print("\nModel Comparison:")
    print(results_df.to_string(index=False))
    
    results_csv_path = "artifacts/model_comparison.csv"
    results_df.to_csv(results_csv_path, index=False)
    
    # Register and transition best model
    client = MlflowClient()
    model_uri = f"runs:/{best_run_id}/model"
    model_details = mlflow.register_model(model_uri, "telco-churn-best")
    
    client.transition_model_version_stage(
        name="telco-churn-best",
        version=model_details.version,
        stage="Staging"
    )
    
    client.transition_model_version_stage(
        name="telco-churn-best",
        version=model_details.version,
        stage="Production"
    )
    print(f"\nRegistered {best_model_name} (Run: {best_run_id}) as 'telco-churn-best' in Production.")

if __name__ == '__main__':
    train_models()
