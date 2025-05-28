import os
import numpy as np
import pandas as pd
from flask import Blueprint, logging, render_template
from flask_login import current_user, login_required

from website.controllers.forecast_controller import run_rice_forecast
from . import db
from sklearn.linear_model import LinearRegression
from .models import InventoryHistory, Product, MonthlyProductData, Inventory
from sqlalchemy.orm import aliased
from sqlalchemy import func, text
from collections import defaultdict
import calendar
from datetime import datetime
from flask import request, jsonify
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.metrics import r2_score

views = Blueprint('views', __name__)

@views.route('/')
def home():
    # Fetch all products
    products = Product.query.all()

    # Get all distinct years available in the MonthlyProductData table (sorted ascending)
    years = sorted({md.year for md in MonthlyProductData.query.with_entities(MonthlyProductData.year).distinct()})

    # Initialize rice-specific data variables
    ivory_rice_inventory = 0
    dona_conchita_inventory = 0
    ivory_rice_forecast_sales = 0
    dona_conchita_forecast_sales = 0
    ivory_rice_forecast_kilos = 0
    dona_conchita_forecast_kilos = 0

    # To calculate total sales and kilos for the latest year
    total_sales = 0
    total_kilos = 0
    current_year = years[-1] if years else None

    # Group monthly sales/kilos by year per product
    for product in products:
        product.data_by_year = {}

        for year in years:
            monthly_data = MonthlyProductData.query.filter_by(product_id=product.id, year=year) \
                                .order_by(MonthlyProductData.month).all()
            sales = [md.total_monthly_sale or 0 for md in monthly_data]
            kilos = [md.kilos_sold or 0 for md in monthly_data]
            product.data_by_year[year] = {
                'sales': sales,
                'kilos': kilos
            }

            # Accumulate total sales and kilos for the current_year
            if year == current_year:
                total_sales += sum(sales)
                total_kilos += sum(kilos)

        # Most recent monthly data (latest year/month)
        latest_data = MonthlyProductData.query.filter_by(product_id=product.id) \
                            .order_by(MonthlyProductData.year.desc(), MonthlyProductData.month.desc()).first()
        if latest_data:
            product.ending_inventory_kg = latest_data.ending_inventory_kg or 0
            product.most_recent_sales = latest_data.total_monthly_sale or 0
        else:
            product.ending_inventory_kg = 0
            product.most_recent_sales = 0

        # Assign specific rice data for Ivory Rice and Dona Conchita Rice
        if product.name == "Ivory Rice":
            ivory_rice_inventory = product.ending_inventory_kg
            ivory_rice_forecast_sales = product.most_recent_sales
            ivory_rice_forecast_kilos = sum([md.kilos_sold or 0 for md in MonthlyProductData.query.filter_by(product_id=product.id).all()])

        if product.name == "Dona Conchita Rice":
            dona_conchita_inventory = product.ending_inventory_kg
            dona_conchita_forecast_sales = product.most_recent_sales
            dona_conchita_forecast_kilos = sum([md.kilos_sold or 0 for md in MonthlyProductData.query.filter_by(product_id=product.id).all()])

    return render_template(
        'home.html',
        products=products,
        user=current_user,
        active_page='home',
        ivory_rice_inventory=ivory_rice_inventory,
        dona_conchita_inventory=dona_conchita_inventory,
        ivory_rice_forecast_sales=ivory_rice_forecast_sales,
        dona_conchita_forecast_sales=dona_conchita_forecast_sales,
        ivory_rice_forecast_kilos=ivory_rice_forecast_kilos,
        dona_conchita_forecast_kilos=dona_conchita_forecast_kilos,
        years=years,
        current_year=current_year,
        total_sales=total_sales,
        total_kilos=total_kilos
    )

@views.route('/inventory')
def inventory():

    # Fetch last 2 months data (sorted descending by year/month)
    monthly_data_items = db.session.query(MonthlyProductData, Product.name)\
        .join(Product, Product.id == MonthlyProductData.product_id)\
        .order_by(MonthlyProductData.year.desc(), MonthlyProductData.month.desc(), Product.name)\
        .all()

    # Collect unique months (year, month) in descending order
    unique_months = []
    seen_months = set()
    for md, _ in monthly_data_items:
        ym = (md.year, md.month)
        if ym not in seen_months:
            unique_months.append(ym)
            seen_months.add(ym)
        if len(unique_months) >= 2:
            break

    # Filter data for only those 2 months, then sort ascending by year/month
    filtered_data = []
    for year, month in sorted(unique_months):
        for md, product_name in monthly_data_items:
            if (md.year, md.month) == (year, month):
                filtered_data.append({
                    'month': calendar.month_name[month],
                    'year': year,
                    'product_name': product_name,
                    'beginning_inventory': md.beginning_inventory_kg or 0,
                    'current_stock': md.ending_inventory_kg or 0,
                    'market_price_per_kg': md.market_price_per_kg or 0,
                    'id': md.id
                })

    # Determine latest month/year from unique_months for conditional Action button
    latest_year, latest_month = max(unique_months) if unique_months else (None, None)
    latest_month_name = calendar.month_name[latest_month] if latest_month else None

    # Get latest month data records
    latest_month_data = [record for record in filtered_data if record['year'] == latest_year and record['month'] == latest_month_name]

    stock_levels = {}

    for record in latest_month_data:
        beginning = record['beginning_inventory']
        current = record['current_stock']

        # Use beginning_inventory as "max" stock, calculate % of current stock to beginning
        if beginning > 0:
            percentage = (current / beginning) * 100
        else:
            percentage = 0

        if percentage >= 51:
            level = 'High'
        elif percentage >= 21:
            level = 'Moderate'
        else:
            level = 'Low'

        stock_levels[record['product_name']] = {
            'level': level,
            'percentage': percentage,
            'beginning': beginning,
            'current': current
        }

    # Latest inventory for summary cards (Ivory Rice and Dona Conchita)
    ivory_latest = db.session.query(MonthlyProductData).join(Product).filter(Product.name == 'Ivory Rice')\
        .order_by(MonthlyProductData.year.desc(), MonthlyProductData.month.desc()).first()
    dona_latest = db.session.query(MonthlyProductData).join(Product).filter(Product.name == 'Dona Conchita Rice')\
        .order_by(MonthlyProductData.year.desc(), MonthlyProductData.month.desc()).first()

    ivory_rice_inventory_value = ivory_latest.ending_inventory_kg if ivory_latest else 0
    dona_conchita_inventory_value = dona_latest.ending_inventory_kg if dona_latest else 0

    # Use beginning_inventory of latest month as max stock dynamically
    max_stock_ivory_rice = ivory_latest.beginning_inventory_kg if ivory_latest else 1  # Avoid div by zero
    max_stock_dona_conchita = dona_latest.beginning_inventory_kg if dona_latest else 1

    products = Product.query.all()

    return render_template(
        'inventory.html',
        inventory_history=filtered_data,
        ivory_rice_inventory=ivory_rice_inventory_value,
        dona_conchita_inventory=dona_conchita_inventory_value,
        products=products,
        user=current_user,
        max_stock_ivory_rice=max_stock_ivory_rice,
        max_stock_dona_conchita=max_stock_dona_conchita,
        active_page='inventory',
        latest_year=latest_year,
        latest_month_name=latest_month_name,
        stock_levels=stock_levels
    )

@views.route('/inventory/edit/<int:id>', methods=['POST'])
def edit_inventory(id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    try:
        # Get the current record by id
        record = MonthlyProductData.query.get(id)
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404

        # Get the data from the request
        ending_inventory = data.get('ending_inventory_kg')
        kilos_sold = data.get('kilos_sold')
        total_sales = data.get('total_sales')

        # If kilos_sold is being updated, just update kilos_sold
        if kilos_sold is not None:
            record.kilos_sold = kilos_sold

        # If ending_inventory_kg is being updated, update it
        if ending_inventory is not None:
            record.ending_inventory_kg = ending_inventory

        # If total_sales is being updated, update it
        if total_sales is not None:
            record.total_monthly_sale = total_sales

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@views.route('/inventory/add', methods=['POST'])
def add_inventory():
    data = request.get_json()

    try:
        year = int(data.get('year'))
        month = int(data.get('month'))
        product_id = int(data.get('product_id'))
        beginning_inventory = float(data.get('beginning_inventory_kg'))
        ending_inventory = float(data.get('ending_inventory_kg'))
        market_price = float(data.get('market_price_per_kg'))
    except (TypeError, ValueError):
        return jsonify(success=False, error="Invalid input data"), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify(success=False, error="Product not found"), 404

    kilos_sold = max(0, beginning_inventory - ending_inventory)
    total_monthly_sale = kilos_sold * market_price

    new_inventory = MonthlyProductData(
        year=year,
        month=month,
        product_id=product_id,
        beginning_inventory_kg=beginning_inventory,
        ending_inventory_kg=ending_inventory,
        market_price_per_kg=market_price,
        kilos_sold=kilos_sold,  # <-- add this line
        total_monthly_sale=total_monthly_sale,
        seasonal_demand_pattern=0,
        promotional_activity=0
    )


    try:
        db.session.add(new_inventory)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 500


# Accuracy Metrics Functions
def calculate_mae(actual, forecasted):
    return sum(abs(a - f) for a, f in zip(actual, forecasted)) / len(actual)

def calculate_mse(actual, forecasted):
    return sum((a - f) ** 2 for a, f in zip(actual, forecasted)) / len(actual)

def calculate_rmse(actual, forecasted):
    return (sum((a - f) ** 2 for a, f in zip(actual, forecasted)) / len(actual)) ** 0.5

def calculate_mape(actual, forecasted):
    return sum(abs((a - f) / a) for a, f in zip(actual, forecasted)) / len(actual) * 100

@views.route('/future-forecast')
def future_forecast():
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Calculate previous month and year
    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year

    # Get current month data for forecasting (i.e., use it to forecast next month)
    current_month_data = db.session.query(MonthlyProductData).filter(
        MonthlyProductData.year == current_year,
        MonthlyProductData.month == current_month
    ).all()

    # Get actual sales for previous month for accuracy calculation
    previous_month_data_all = db.session.query(MonthlyProductData).filter(
        MonthlyProductData.year == previous_year,
        MonthlyProductData.month == previous_month
    ).all()

    # Accuracy metrics calculation
    actual_sales_dona = []
    forecasted_sales_dona = []
    actual_sales_ivory = []
    forecasted_sales_ivory = []

    for data in previous_month_data_all:
        product_name = data.product.name

        if product_name == "Dona Conchita Rice":
            actual_sales_dona.append(data.kilos_sold)
        elif product_name == "Ivory Rice":
            actual_sales_ivory.append(data.kilos_sold)

        previous_data = db.session.query(MonthlyProductData).filter(
            MonthlyProductData.product_id == data.product_id,
            MonthlyProductData.year == previous_year,
            MonthlyProductData.month == previous_month - 1 if previous_month > 1 else 12
        ).first()

        if previous_data:
            change = data.kilos_sold - previous_data.kilos_sold
            forecast = data.kilos_sold + 22.8 + 0.5 * change

            if product_name == "Dona Conchita Rice":
                forecasted_sales_dona.append(forecast)
            elif product_name == "Ivory Rice":
                forecasted_sales_ivory.append(forecast)

    mae_dona = calculate_mae(actual_sales_dona, forecasted_sales_dona)
    mse_dona = calculate_mse(actual_sales_dona, forecasted_sales_dona)
    rmse_dona = calculate_rmse(actual_sales_dona, forecasted_sales_dona)
    mape_dona = calculate_mape(actual_sales_dona, forecasted_sales_dona)

    mae_ivory = calculate_mae(actual_sales_ivory, forecasted_sales_ivory)
    mse_ivory = calculate_mse(actual_sales_ivory, forecasted_sales_ivory)
    rmse_ivory = calculate_rmse(actual_sales_ivory, forecasted_sales_ivory)
    mape_ivory = calculate_mape(actual_sales_ivory, forecasted_sales_ivory)

    forecasts = []

    for data in current_month_data:
        product_name = data.product.name
        product_id = data.product_id

        latest_kilos_sold = data.kilos_sold
        change = data.change_in_sales if data.change_in_sales is not None else 0

        forecasted_sales = latest_kilos_sold + 22.8 + 0.5 * change
        recommended_order_kg = (forecasted_sales * 1.2) - latest_kilos_sold

        forecasted_sales = max(0, round(forecasted_sales))
        recommended_order_kg = round(recommended_order_kg, 2)

        forecast_data = {
            'product_id': product_id,
            'product_name': product_name,
            'year': current_year,
            'month': current_month + 1 if current_month < 12 else 1,
            'month_abbreviation': (current_date.replace(month=(current_month + 1 if current_month < 12 else 1)).strftime('%b')),
            'forecasted_sales': forecasted_sales,
            'previous_month_kilos_sold': latest_kilos_sold,
            'recommended_order_kg': recommended_order_kg
        }

        forecasts.append(forecast_data)

    return render_template('future-forecast.html',
                           forecasts=forecasts,
                           mae_dona=mae_dona, mse_dona=mse_dona, rmse_dona=rmse_dona, mape_dona=mape_dona,
                           mae_ivory=mae_ivory, mse_ivory=mse_ivory, rmse_ivory=rmse_ivory, mape_ivory=mape_ivory)

