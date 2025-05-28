# forecast_controller.py

import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def linear_forecast(x, y, new_x):
    x = np.array(x).reshape(-1, 1)
    y = np.array(y)
    model = LinearRegression().fit(x, y)
    return model.predict(np.array(new_x).reshape(-1, 1))[0]

def run_rice_forecast(csv_path=None):
    if csv_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.normpath(os.path.join(base_dir, '..', 'static', 'data', 'monthly_product_data.csv'))

    df = pd.read_csv(csv_path)
    all_forecasts = []

    for product_id in df['product_id'].unique():
        product_df = df[df['product_id'] == product_id].copy()
        historical_df = product_df.iloc[:54].copy()

        for i in range(len(product_df) - 54):
            idx = 54 + i

            product_df.loc[idx, 'beginning_inventory_kg'] = linear_forecast(
                historical_df['month'], historical_df['beginning_inventory_kg'],
                [product_df.loc[idx, 'month']]
            )

            product_df.loc[idx, 'ending_inventory_kg'] = linear_forecast(
                historical_df['beginning_inventory_kg'], historical_df['ending_inventory_kg'],
                [product_df.loc[idx, 'beginning_inventory_kg']]
            )

            product_df.loc[idx, 'market_price_per_kg'] = linear_forecast(
                historical_df['ending_inventory_kg'], historical_df['market_price_per_kg'],
                [product_df.loc[idx, 'ending_inventory_kg']]
            )

            product_df.loc[idx, 'kilos_sold'] = linear_forecast(
                historical_df['market_price_per_kg'], historical_df['kilos_sold'],
                [product_df.loc[idx, 'market_price_per_kg']]
            )

            product_df.loc[idx, 'total_monthly_sale'] = linear_forecast(
                historical_df['kilos_sold'], historical_df['total_monthly_sale'],
                [product_df.loc[idx, 'kilos_sold']]
            )

            historical_df = pd.concat([historical_df, product_df.iloc[[idx]]], ignore_index=True)

        all_forecasts.append(product_df)

    return pd.concat(all_forecasts, ignore_index=True)