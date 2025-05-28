# website/forecast_utils.py
from sqlalchemy import func

def run_forecast(months_combined, sheets_sold_combined, sales_combined):
    from sklearn.linear_model import LinearRegression
    import numpy as np

    # Fit Linear Regression Model for sheets sold
    X = np.array(months_combined).reshape(-1, 1)
    y_sheets = np.array(sheets_sold_combined)
    model_sheets = LinearRegression()
    model_sheets.fit(X, y_sheets)

    # Fit Linear Regression Model for sales revenue
    y_sales = np.array(sales_combined)
    model_sales = LinearRegression()
    model_sales.fit(X, y_sales)

    # Predict future months (e.g., 2025)
    future_months = list(range(13, 25))
    X_future = np.array(future_months).reshape(-1, 1)

    forecast_sheets_sold = model_sheets.predict(X_future)
    forecast_sales = model_sales.predict(X_future)

    return forecast_sheets_sold, forecast_sales
