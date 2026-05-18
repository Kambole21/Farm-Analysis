# the file below is sales_dashboard.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from datetime import datetime, timedelta
from flask import jsonify
from app import (
	 sales_collection, stock_on_hand_collection, revenue_collection,
	 credit_sales_collection, expenses_collection, 
	 expected_deposit_collection, actual_deposit_collection, cash_on_hand_collection,
	 closing_stock_collection, credit_owed_collection
	)


bp = Blueprint('sales_dashboard', __name__)

# Custom login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'danger')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/sales-dashboard')  
def sales_dashboard():
    # Import timedelta if not already imported
    from datetime import datetime, timedelta
    
    # Get last 7 days of sales data
    end_date = datetime.now()
    start_date = datetime.now() - timedelta(days=7)
    
    # Query sales data for the last 7 days
    recent_sales = list(sales_collection.find({
        'date': {
            '$gte': start_date.strftime('%Y-%m-%d'),
            '$lte': end_date.strftime('%Y-%m-%d')
        }
    }).sort('date', -1))
    
    # Calculate totals
    total_revenue_week = sum(sale.get('totals', {}).get('revenue', 0) for sale in recent_sales)
    total_expenses_week = sum(sale.get('totals', {}).get('expenses', 0) for sale in recent_sales)
    
    # Get user info from session
    user_info = {
        'username': session.get('user_name', 'User'),
        'role': session.get('role', '')
    }
    
    # Pass current_user to the template (CHANGE THIS LINE)
    return render_template('sales/sales_dashboard.html',
                         recent_sales=recent_sales,
                         total_revenue=total_revenue_week,
                         total_expenses=total_expenses_week,
                         current_user=user_info)  


@bp.route('/api/sales-data')
def get_sales_data():
    """API endpoint for sales data charts"""
    period = request.args.get('period', 'week')
    
    end_date = datetime.now()
    
    if period == 'week':
        start_date = end_date - timedelta(days=7)
        # Group by day
        date_format = '%Y-%m-%d'
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
        # Group by day
        date_format = '%Y-%m-%d'
    else:  # year
        start_date = end_date - timedelta(days=365)
        # Group by month
        date_format = '%Y-%m'
    
    # Query sales data
    sales_data = list(sales_collection.find({
        'date': {
            '$gte': start_date.strftime('%Y-%m-%d'),
            '$lte': end_date.strftime('%Y-%m-%d')
        }
    }).sort('date', 1))
    
    # Process data based on period
    labels = []
    cash_data = []
    credit_data = []
    
    if period == 'year':
        # Group by month
        monthly_data = {}
        
        # Initialize all months
        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            month_label = current.strftime('%b %Y')  # e.g., "Jan 2024"
            monthly_data[month_key] = {
                'label': month_label,
                'cash': 0,
                'credit': 0
            }
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        # Aggregate sales by month
        for sale in sales_data:
            sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
            month_key = sale_date.strftime('%Y-%m')
            
            if month_key in monthly_data:
                cash_total = sum(s.get('amount', 0) for s in sale.get('cash_sales', []))
                credit_total = sum(s.get('total_amount', 0) for s in sale.get('credit_sales', []))
                
                monthly_data[month_key]['cash'] += cash_total
                monthly_data[month_key]['credit'] += credit_total
        
        # Sort months and create labels/data
        sorted_months = sorted(monthly_data.keys())
        for month_key in sorted_months:
            labels.append(monthly_data[month_key]['label'])
            cash_data.append(monthly_data[month_key]['cash'])
            credit_data.append(monthly_data[month_key]['credit'])
    
    elif period == 'week':
        # Last 7 days
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%a'))  # Mon, Tue, etc.
            
            day_sales = next((s for s in sales_data if s.get('date') == date_str), None)
            if day_sales:
                cash_total = sum(s.get('amount', 0) for s in day_sales.get('cash_sales', []))
                credit_total = sum(s.get('total_amount', 0) for s in day_sales.get('credit_sales', []))
            else:
                cash_total = 0
                credit_total = 0
            
            cash_data.append(cash_total)
            credit_data.append(credit_total)
            current += timedelta(days=1)
    
    else:  # month
        # Last 30 days
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%d'))  # Day of month
            
            day_sales = next((s for s in sales_data if s.get('date') == date_str), None)
            if day_sales:
                cash_total = sum(s.get('amount', 0) for s in day_sales.get('cash_sales', []))
                credit_total = sum(s.get('total_amount', 0) for s in day_sales.get('credit_sales', []))
            else:
                cash_total = 0
                credit_total = 0
            
            cash_data.append(cash_total)
            credit_data.append(credit_total)
            current += timedelta(days=1)
    
    return jsonify({
        'success': True,
        'labels': labels,
        'cashData': cash_data,
        'creditData': credit_data
    })

@bp.route('/api/expenses-data')
def get_expenses_data():
    """API endpoint for expenses data charts"""
    period = request.args.get('period', 'week')
    
    end_date = datetime.now()
    
    if period == 'week':
        start_date = end_date - timedelta(days=7)
    elif period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    # Query expenses data
    expenses_data = list(expenses_collection.find({
        'date': {
            '$gte': start_date.strftime('%Y-%m-%d'),
            '$lte': end_date.strftime('%Y-%m-%d')
        }
    }).sort('date', 1))
    
    # Process data based on period
    labels = []
    expenses_total = []
    
    # Track by category
    expense_categories = {}
    
    if period == 'year':
        # Group by month
        monthly_expenses = {}
        monthly_categories = {}
        
        # Initialize all months
        current = start_date
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            month_label = current.strftime('%b %Y')
            monthly_expenses[month_key] = 0
            monthly_categories[month_key] = {}
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        # Aggregate expenses by month
        for expense in expenses_data:
            expense_date = datetime.strptime(expense['date'], '%Y-%m-%d')
            month_key = expense_date.strftime('%Y-%m')
            amount = expense.get('amount', 0)
            description = expense.get('description', 'Other')
            
            if month_key in monthly_expenses:
                monthly_expenses[month_key] += amount
                
                # Track by category
                if description not in monthly_categories[month_key]:
                    monthly_categories[month_key][description] = 0
                monthly_categories[month_key][description] += amount
        
        # Sort months and create labels/data
        sorted_months = sorted(monthly_expenses.keys())
        for month_key in sorted_months:
            labels.append(monthly_expenses[month_key]['label'] if isinstance(monthly_expenses[month_key], dict) else month_key)
            expenses_total.append(monthly_expenses[month_key])
            
            # Build category data
            for cat_name, cat_amount in monthly_categories[month_key].items():
                if cat_name not in expense_categories:
                    expense_categories[cat_name] = [0] * len(sorted_months)
                month_index = sorted_months.index(month_key)
                expense_categories[cat_name][month_index] = cat_amount
    
    elif period == 'week':
        # Last 7 days
        current = start_date
        day_index = 0
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%a'))  # Mon, Tue, etc.
            
            day_expenses = [e for e in expenses_data if e.get('date') == date_str]
            day_total = sum(e.get('amount', 0) for e in day_expenses)
            expenses_total.append(day_total)
            
            # Track by category
            for expense in day_expenses:
                description = expense.get('description', 'Other')
                if description not in expense_categories:
                    expense_categories[description] = [0] * 7
                expense_categories[description][day_index] += expense.get('amount', 0)
            
            day_index += 1
            current += timedelta(days=1)
    
    else:  # month
        # Last 30 days
        current = start_date
        day_index = 0
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            labels.append(current.strftime('%d'))  # Day of month
            
            day_expenses = [e for e in expenses_data if e.get('date') == date_str]
            day_total = sum(e.get('amount', 0) for e in day_expenses)
            expenses_total.append(day_total)
            
            # Track by category
            for expense in day_expenses:
                description = expense.get('description', 'Other')
                if description not in expense_categories:
                    expense_categories[description] = [0] * 30
                expense_categories[description][day_index] += expense.get('amount', 0)
            
            day_index += 1
            current += timedelta(days=1)
    
    # Format categories for response
    categories = []
    for cat_name, cat_data in expense_categories.items():
        # Trim data to match labels length
        trimmed_data = cat_data[:len(labels)]
        categories.append({
            'name': cat_name,
            'data': trimmed_data
        })
    
    return jsonify({
        'success': True,
        'labels': labels,
        'expensesData': expenses_total,
        'categories': categories
    })