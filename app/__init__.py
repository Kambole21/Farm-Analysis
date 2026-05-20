from flask import Flask
from pymongo import MongoClient
import datetime
import os
from pathlib import Path
from flask_mail import Mail

client = MongoClient('mongodb://localhost:27017/')
database = client['FARM']
users_collection = database['Users']

# SALES COLLECTIONS

sales_collection = database['DAILY SALES']
stock_on_hand_collection = database['STOCK ON HAND ']
revenue_collection = database['CASH SALES/REVENUE']
credit_sales_collection = database['CREDIT SALES']
expenses_collection = database['EXPENSES']
expected_deposit_collection = database['EXPECTED BANK DEPOSIT']
actual_deposit_collection = database['ACTUAL BANK DEPOSIT']
cash_on_hand_collection = database['CASH ON HAND']
closing_stock_collection = database['CLOSING STOCK']
credit_owed_collection = database['CREDIT OWED TO THE FARM']
dates_collection = database['STOCK DATES']

farm_report_collection = database['Farm Reports']
farm_dates_collection = database['Farm Dates']
farm_poultry_collection = database['Farm Poultry']
farm_sales_collection = database['Farm Sales']
farm_production_collection = database['Farm Production']
farm_feed_collection = database['Farm Feed']
farm_mortality_collection = database['Farm Mortality']
farm_percentage_collection = database['Farm Percentages']

#initializing the application
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = '44c5450b402af78d5b8851e210739a80' # setting up the secret key for the application



from app.routes import (login, registration, sales_dashboard, sales, view_sales_day, farm_sales, view_farm_day) 

app.register_blueprint(login.bp)
app.register_blueprint(registration.bp)
app.register_blueprint(sales_dashboard.bp)
app.register_blueprint(sales.bp)
app.register_blueprint(view_sales_day.bp)
app.register_blueprint(farm_sales.bp)
app.register_blueprint(view_farm_day.bp)


def format_date(value, fmt='%Y-%m-%d %H:%M'):
    """Format a datetime object or string."""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(fmt)

app.jinja_env.filters['format_date'] = format_date
