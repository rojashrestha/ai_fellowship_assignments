from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow.pyfunc
import pandas as pd

app = FastAPI(title="Telco Churn Prediction API")

model_name = "telco-churn-best"
stage = "Production"
try:
    model = mlflow.pyfunc.load_model(f"models:/{model_name}/{stage}")
except Exception as e:
    model = None
    print(f"Could not load model: {e}")

class CustomerData(BaseModel):
    gender: int
    SeniorCitizen: int
    Partner: int
    Dependents: int
    tenure: int
    PhoneService: int
    MultipleLines: int
    InternetService: int
    OnlineSecurity: int
    OnlineBackup: int
    DeviceProtection: int
    TechSupport: int
    StreamingTV: int
    StreamingMovies: int
    Contract: int
    PaperlessBilling: int
    PaymentMethod: int
    MonthlyCharges: float
    TotalCharges: float

@app.get("/health")
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy"}

@app.post("/predict")
def predict(data: CustomerData):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    df = pd.DataFrame([data.dict()])
    pred = model.predict(df)[0]
    # some models might not have proba in pyfunc natively depending on flavor, but assuming standard sklearn pyfunc wrapper
    return {"prediction": int(pred)}
