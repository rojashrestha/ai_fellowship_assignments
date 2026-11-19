# S&P 500 Index Forecasting: Classical to Modern Forecasters

This project contains the implementation for **Week 8 — Forecasting Assignment** of the Fusemachines AI Fellowship. The goal is to forecast the monthly closing price of the S&P 500 index over a 60-month test period (2020–2024) using historical monthly data from 1990 to 2019.

---

## 📂 Project Structure

```text
Fusemachine_fellowship/
├── assignment/
│   └── sp500_sarima_v1.pkl           # Saved SARIMA (ARIMA(0,1,0)) model object
└── week8/
    ├── W8_Forecasting_Assignment (Roja Shrestha).ipynb # Completed Jupyter notebook with code & answers
    ├── README.md                     # Project documentation (this file)
    └── W8_Forecasting_Assignment_backup.ipynb # Backup copy of original notebook
```

---

## 📈 Model Performance & Evaluation

We trained and evaluated **8 different forecasting models** using recursive step-by-step prediction over a 60-month horizon ($H=60$). The models are evaluated using scale-free metrics (MASE) as well as absolute error metrics (MAE, RMSE, MAPE) against the actual S&P 500 test prices.

### Performance Summary Table (Sorted by MASE)

| Model | MAE (S&P pts) | RMSE (S&P pts) | MAPE (%) | WMAE | WMAPE (%) | MASE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **LSTM** | 434.4461 | 568.5257 | 9.7168% | 478.3191 | 10.1714% | **2.5440** |
| **Holt-Winters** | 448.3844 | 574.0635 | 9.9117% | 494.2212 | 10.4977% | **2.6257** |
| **Prophet** | 489.9555 | 621.0115 | 10.7211% | 541.1597 | 11.4710% | **2.8691** |
| **Naive** | 1092.5781 | 1298.2251 | 23.5979% | 1215.9665 | 25.5798% | **6.3979** |
| **SARIMA** | 1092.5781 | 1298.2251 | 23.5979% | 1215.9665 | 25.5798% | **6.3979** |
| **S-Naive** | 1342.7261 | 1534.6318 | 29.3258% | 1474.6725 | 31.4364% | **7.8627** |
| **LightGBM** | 1537.5883 | 1738.9467 | 33.6534% | 1684.3038 | 35.9986% | **9.0038** |
| **MLP** | 4181.2753 | 4257.0352 | 97.7206% | 4326.4194 | 97.8935% | **24.4847** |

---

## 🔍 Key Insights & Statistical Findings

1. **Best Model (LSTM)**:
   - The deep learning **LSTM** model with a lookback window of 12 months achieved the lowest MASE of **2.5440** and RMSE of **568.5**, outperforming all other models.
   - A Diebold-Mariano test comparing the LSTM's squared errors against the average Ensemble of the top 4 models yielded a test statistic of **-5.6194** ($p = 0.0000$), confirming that the LSTM's superior accuracy is **statistically significant**.

2. **The Random Walk Baseline & SARIMA**:
   - The classical **SARIMA** optimization automatically selected **ARIMA(0, 1, 0)** as the best fit (lowest AIC of -1257.44). 
   - An ARIMA(0,1,0) model is mathematically equivalent to a random walk. As a result, the SARIMA model simply repeated the last training price for all future horizons, matching the **Naïve** baseline's performance identically (MASE = 6.3979).

3. **Structural Breaks and Volatility Shortfalls**:
   - The test set contains the March 2020 COVID crash, where the S&P 500 closed down **-20.0%** month-over-month. The LSTM model predicted a milder decline of **-10.3%**.
   - Due to the massive out-of-distribution volatility introduced by the pandemic and subsequent recovery, the LightGBM 95% Quantile Prediction Interval achieved only **5.0% empirical coverage** on the test set, indicating that intervals built on historical training periods (1990-2019) were heavily under-calibrated.

---

## 🚀 How to Run the Notebook

1. **Install Dependencies**:
   ```bash
   pip install yfinance prophet lightgbm xgboost tensorflow statsmodels scikit-learn pandas numpy matplotlib scipy
   ```

2. **Open and Run the Jupyter Notebook**:
   ```bash
   jupyter notebook week8/W8_Forecasting_Assignment.ipynb
   ```
   All cells can be run sequentially from top-to-bottom. The pickled SARIMA model is automatically saved to `assignment/sp500_sarima_v1.pkl` upon running Q22.
