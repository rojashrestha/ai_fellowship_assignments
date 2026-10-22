import pandas as pd
import numpy as np
import requests
import io
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text))
    
    # Clean data
    df = df.drop(columns=['customerID'])
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df = df.dropna()
    
    # Encode categorical columns
    le = LabelEncoder()
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        df[col] = le.fit_transform(df[col])
        
    # Split features and target
    X = df.drop(columns=['Churn'])
    y = df['Churn']
    
    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    
    # Data for Evidently
    reference_df = X_train.copy()
    reference_df['Churn'] = y_train
    
    current_df = X_test.copy()
    current_df['Churn'] = y_test
    
    return X_train, X_test, y_train, y_test, reference_df, current_df

if __name__ == "__main__":
    X_train, X_test, y_train, y_test, ref_df, cur_df = load_and_preprocess_data()
    print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
