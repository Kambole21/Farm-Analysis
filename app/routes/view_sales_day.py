# the file below is view_sales_day.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
from app import (
    sales_collection, stock_on_hand_collection, revenue_collection,
    credit_sales_collection, expenses_collection,
    expected_deposit_collection, actual_deposit_collection, cash_on_hand_collection,
    closing_stock_collection, credit_owed_collection, dates_collection,
    users_collection  # Add this if not already imported
)
from bson import ObjectId
import traceback

bp = Blueprint('view_sales_day', __name__)

@bp.route('/View-Date')
def sales_day():
    # Get all dates with sales data, sorted by date (newest first)
    dates = list(sales_collection.find(
        {}, 
        {'date': 1, 'status': 1, 'created_at': 1, 'closed_at': 1}
    ).sort('date', -1))
    
    # Convert ObjectId to string for JSON serialization
    for date in dates:
        if '_id' in date:
            date['_id'] = str(date['_id'])
        if 'created_at' in date and isinstance(date['created_at'], datetime):
            date['created_at'] = date['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        if 'closed_at' in date and isinstance(date['closed_at'], datetime):
            date['closed_at'] = date['closed_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('sales/view_sales_day.html', dates=dates)

@bp.route('/get-day-details/<date>')
def get_day_details(date):
    """Get detailed information for a specific day"""
    try:
        # Get sales data for the day
        sales_data = sales_collection.find_one({'date': date})
        
        if not sales_data:
            return jsonify({'success': False, 'error': 'Day not found'}), 404
        
        # Get user information for all users who recorded data
        user_records = {}
        
        # Function to extract user info from data
        def extract_user_info(data, field_name='recorded_by'):
            if isinstance(data, dict):
                if field_name in data:
                    username = data[field_name]
                    if username and username not in user_records:
                        # Get user details from users collection
                        user = users_collection.find_one({'username': username})
                        if user:
                            user_records[username] = {
                                'username': username,
                                'full_name': f"{user.get('fname', '')} {user.get('lastname', '')}".strip(),
                                'role': user.get('role', 'Unknown')
                            }
                # Recursively check nested structures
                for value in data.values():
                    extract_user_info(value, field_name)
            elif isinstance(data, list):
                for item in data:
                    extract_user_info(item, field_name)
        
        # Extract user info from all sections
        extract_user_info(sales_data.get('opening_stock', []))
        extract_user_info(sales_data.get('cash_sales', []))
        extract_user_info(sales_data.get('credit_sales', []))
        extract_user_info(sales_data.get('expenses', []))
        extract_user_info(sales_data.get('credits_to_farm', []))
        
        # Convert MongoDB document to JSON serializable format
        def convert_for_json(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            return obj
        
        sales_data = convert_for_json(sales_data)
        
        # Calculate detailed totals and summaries
        totals = calculate_detailed_totals(sales_data)
        
        # Get activity log (who did what and when)
        activity_log = generate_activity_log(sales_data)
        
        return jsonify({
            'success': True,
            'sales_data': sales_data,
            'totals': totals,
            'user_records': user_records,
            'activity_log': activity_log,
            'summary': generate_summary_report(sales_data, totals)
        })
        
    except Exception as e:
        print(f"Error in get_day_details: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_detailed_totals(sales_data):
    """Calculate detailed totals for the day"""
    totals = {
        'opening_stock': {
            'total_value': 0,
            'product_count': 0,
            'section_count': 0,
            'products': []
        },
        'cash_sales': {
            'total_amount': 0,
            'count': 0,
            'items': []
        },
        'credit_sales': {
            'total_amount': 0,
            'count': 0,
            'credit_holders': {},
            'items': []
        },
        'expenses': {
            'total_amount': 0,
            'count': 0,
            'categories': {},
            'items': []
        },
        'bank_deposit': sales_data.get('bank_deposit', {}),
        'cash_on_hand': sales_data.get('cash_on_hand', 0),
        'closing_stock': {
            'product_count': 0,
            'section_count': 0
        },
        'credits_to_farm': {
            'total_amount': 0,
            'count': 0,
            'creditors': {}
        }
    }
    
    # Opening Stock Analysis
    opening_stock = sales_data.get('opening_stock', [])
    if isinstance(opening_stock, list):
        for product in opening_stock:
            product_info = {
                'product_type': product.get('product_type', 'Unknown'),
                'total_value': product.get('total_value', 0),
                'section_count': len(product.get('sections', [])),
                'sections': []
            }
            
            sections = product.get('sections', [])
            for section in sections:
                section_info = {
                    'name': section.get('name', 'Unknown'),
                    'quantity': section.get('quantity', 0),
                    'unit_price': section.get('unit_price', 0),
                    'section_total': section.get('section_total', 0),
                    'recorded_by': section.get('recorded_by', 'Unknown'),
                    'recorded_at': section.get('recorded_at', '')
                }
                product_info['sections'].append(section_info)
            
            totals['opening_stock']['products'].append(product_info)
            totals['opening_stock']['total_value'] += product.get('total_value', 0)
            totals['opening_stock']['product_count'] += 1
            totals['opening_stock']['section_count'] += len(sections)
    
    # Cash Sales Analysis
    cash_sales = sales_data.get('cash_sales', [])
    for sale in cash_sales:
        sale_info = {
            'name': sale.get('name', 'Unknown'),
            'amount': sale.get('amount', 0),
            'recorded_by': sale.get('recorded_by', 'Unknown'),
            'timestamp': sale.get('timestamp', '')
        }
        totals['cash_sales']['items'].append(sale_info)
        totals['cash_sales']['total_amount'] += sale.get('amount', 0)
        totals['cash_sales']['count'] += 1
    
    # Credit Sales Analysis
    credit_sales = sales_data.get('credit_sales', [])
    for sale in credit_sales:
        sale_info = {
            'credit_holder': sale.get('credit_holder', 'Unknown'),
            'product_type': sale.get('product_type', 'Unknown'),
            'section': sale.get('section', 'Unknown'),
            'quantity': sale.get('quantity', 0),
            'unit_price': sale.get('unit_price', 0),
            'total_amount': sale.get('total_amount', 0),
            'recorded_by': sale.get('recorded_by', 'Unknown'),
            'timestamp': sale.get('timestamp', '')
        }
        totals['credit_sales']['items'].append(sale_info)
        totals['credit_sales']['total_amount'] += sale.get('total_amount', 0)
        totals['credit_sales']['count'] += 1
        
        # Group by credit holder
        holder = sale.get('credit_holder', 'Unknown')
        if holder not in totals['credit_sales']['credit_holders']:
            totals['credit_sales']['credit_holders'][holder] = 0
        totals['credit_sales']['credit_holders'][holder] += sale.get('total_amount', 0)
    
    # Expenses Analysis
    expenses = sales_data.get('expenses', [])
    for expense in expenses:
        expense_info = {
            'description': expense.get('description', 'Unknown'),
            'amount': expense.get('amount', 0),
            'recorded_by': expense.get('recorded_by', 'Unknown'),
            'timestamp': expense.get('timestamp', '')
        }
        totals['expenses']['items'].append(expense_info)
        totals['expenses']['total_amount'] += expense.get('amount', 0)
        totals['expenses']['count'] += 1
        
        # Categorize expenses (simple keyword matching)
        description = expense.get('description', '').lower()
        category = 'Other'
        if 'feed' in description:
            category = 'Feed'
        elif 'transport' in description or 'fuel' in description:
            category = 'Transport'
        elif 'wage' in description or 'salary' in description:
            category = 'Labor'
        elif 'medicine' in description or 'vet' in description:
            category = 'Medical'
        elif 'water' in description or 'electric' in description:
            category = 'Utilities'
        
        if category not in totals['expenses']['categories']:
            totals['expenses']['categories'][category] = 0
        totals['expenses']['categories'][category] += expense.get('amount', 0)
    
    # Closing Stock Analysis
    closing_stock = sales_data.get('closing_stock', {})
    if isinstance(closing_stock, dict):
        for product_type, sections in closing_stock.items():
            if isinstance(sections, dict):
                totals['closing_stock']['product_count'] += 1
                totals['closing_stock']['section_count'] += len(sections)
    
    # Credits to Farm Analysis
    farm_credits = sales_data.get('credits_to_farm', [])
    for credit in farm_credits:
        credit_info = {
            'creditor_name': credit.get('creditor_name', 'Unknown'),
            'description': credit.get('description', ''),
            'amount': credit.get('amount', 0),
            'recorded_by': credit.get('recorded_by', 'Unknown'),
            'timestamp': credit.get('timestamp', '')
        }
        totals['credits_to_farm']['total_amount'] += credit.get('amount', 0)
        totals['credits_to_farm']['count'] += 1
        
        # Group by creditor
        creditor = credit.get('creditor_name', 'Unknown')
        if creditor not in totals['credits_to_farm']['creditors']:
            totals['credits_to_farm']['creditors'][creditor] = 0
        totals['credits_to_farm']['creditors'][creditor] += credit.get('amount', 0)
    
    # Calculate final summary
    totals['gross_income'] = totals['cash_sales']['total_amount'] + totals['credit_sales']['total_amount']
    totals['net_profit'] = totals['gross_income'] - totals['expenses']['total_amount']
    totals['total_credits_outstanding'] = totals['credits_to_farm']['total_amount'] + totals['credit_sales']['total_amount']
    
    # Calculate deposit variance
    expected = totals['bank_deposit'].get('expected', 0)
    actual = totals['bank_deposit'].get('actual', 0)
    totals['deposit_variance'] = actual - expected
    totals['deposit_variance_percent'] = (totals['deposit_variance'] / expected * 100) if expected > 0 else 0
    
    return totals

def generate_activity_log(sales_data):
    """Generate an activity log showing who did what and when"""
    activity_log = []
    
    def add_activity(activity_type, description, user, timestamp, details=None):
        if user and timestamp:
            activity_log.append({
                'type': activity_type,
                'description': description,
                'user': user,
                'timestamp': timestamp,
                'details': details or {}
            })
    
    # Opening Stock activities
    opening_stock = sales_data.get('opening_stock', [])
    if isinstance(opening_stock, list):
        for product in opening_stock:
            sections = product.get('sections', [])
            for section in sections:
                add_activity(
                    'Opening Stock',
                    f"Added {section.get('quantity', 0)} {section.get('name', '')} to opening stock",
                    section.get('recorded_by'),
                    section.get('recorded_at'),
                    {
                        'product_type': product.get('product_type'),
                        'section': section.get('name'),
                        'quantity': section.get('quantity'),
                        'unit_price': section.get('unit_price'),
                        'total': section.get('section_total')
                    }
                )
    
    # Cash Sales activities
    cash_sales = sales_data.get('cash_sales', [])
    for sale in cash_sales:
        add_activity(
            'Cash Sale',
            f"Recorded cash sale: {sale.get('name', 'Unknown')}",
            sale.get('recorded_by'),
            sale.get('timestamp'),
            {
                'amount': sale.get('amount'),
                'description': sale.get('name')
            }
        )
    
    # Credit Sales activities
    credit_sales = sales_data.get('credit_sales', [])
    for sale in credit_sales:
        add_activity(
            'Credit Sale',
            f"Recorded credit sale to {sale.get('credit_holder', 'Unknown')}",
            sale.get('recorded_by'),
            sale.get('timestamp'),
            {
                'credit_holder': sale.get('credit_holder'),
                'product': sale.get('product_type'),
                'section': sale.get('section'),
                'quantity': sale.get('quantity'),
                'total': sale.get('total_amount')
            }
        )
    
    # Expenses activities
    expenses = sales_data.get('expenses', [])
    for expense in expenses:
        add_activity(
            'Expense',
            f"Recorded expense: {expense.get('description', 'Unknown')}",
            expense.get('recorded_by'),
            expense.get('timestamp'),
            {
                'amount': expense.get('amount'),
                'description': expense.get('description')
            }
        )
    
    # Credits to Farm activities
    farm_credits = sales_data.get('credits_to_farm', [])
    for credit in farm_credits:
        add_activity(
            'Farm Credit',
            f"Recorded credit from {credit.get('creditor_name', 'Unknown')}",
            credit.get('recorded_by'),
            credit.get('timestamp'),
            {
                'creditor': credit.get('creditor_name'),
                'amount': credit.get('amount'),
                'description': credit.get('description')
            }
        )
    
    # Bank Deposit activities
    bank_deposit = sales_data.get('bank_deposit', {})
    if bank_deposit.get('expected') is not None:
        add_activity(
            'Bank Deposit',
            f"Set expected bank deposit: {bank_deposit.get('expected')}",
            sales_data.get('created_by', 'System'),
            sales_data.get('created_at', '')
        )
    if bank_deposit.get('actual') is not None:
        add_activity(
            'Bank Deposit',
            f"Set actual bank deposit: {bank_deposit.get('actual')}",
            sales_data.get('updated_by', 'System'),
            sales_data.get('updated_at', '')
        )
    
    # Cash on Hand activity
    if sales_data.get('cash_on_hand') is not None:
        add_activity(
            'Cash Management',
            f"Set cash on hand: {sales_data.get('cash_on_hand')}",
            sales_data.get('updated_by', 'System'),
            sales_data.get('updated_at', '')
        )
    
    # Sort activities by timestamp (newest first)
    activity_log.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
    
    return activity_log

def generate_summary_report(sales_data, totals):
    """Generate a summary report for the day"""
    return {
        'date': sales_data.get('date', 'Unknown Date'),
        'status': sales_data.get('status', 'unknown'),
        'created_at': sales_data.get('created_at', ''),
        'closed_at': sales_data.get('closed_at', ''),
        'financial_summary': {
            'total_sales': totals['gross_income'],
            'total_expenses': totals['expenses']['total_amount'],
            'net_profit': totals['net_profit'],
            'opening_stock_value': totals['opening_stock']['total_value'],
            'cash_on_hand': totals['cash_on_hand']
        },
        'transaction_counts': {
            'cash_sales': totals['cash_sales']['count'],
            'credit_sales': totals['credit_sales']['count'],
            'expenses': totals['expenses']['count'],
            'opening_stock_items': totals['opening_stock']['section_count']
        },
        'key_metrics': {
            'average_cash_sale': totals['cash_sales']['total_amount'] / totals['cash_sales']['count'] if totals['cash_sales']['count'] > 0 else 0,
            'average_expense': totals['expenses']['total_amount'] / totals['expenses']['count'] if totals['expenses']['count'] > 0 else 0,
            'profit_margin': (totals['net_profit'] / totals['gross_income'] * 100) if totals['gross_income'] > 0 else 0,
            'deposit_completion': (totals['bank_deposit'].get('actual', 0) / totals['bank_deposit'].get('expected', 1) * 100) if totals['bank_deposit'].get('expected', 0) > 0 else 0
        }
    }

@bp.route('/export-day-report/<date>')
def export_day_report(date):
    """Export day report as PDF or Excel"""
    try:
        # Get day details
        sales_data = sales_collection.find_one({'date': date})
        if not sales_data:
            return jsonify({'success': False, 'error': 'Day not found'}), 404
        
        # Convert to JSON serializable format
        def convert_for_json(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            return obj
        
        sales_data = convert_for_json(sales_data)
        totals = calculate_detailed_totals(sales_data)
        
        # For now, return JSON. Later you can add PDF/Excel generation
        return jsonify({
            'success': True,
            'date': date,
            'report_data': {
                'sales_data': sales_data,
                'totals': totals,
                'summary': generate_summary_report(sales_data, totals)
            }
        })
        
    except Exception as e:
        print(f"Error in export_day_report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/compare-days', methods=['GET'])
def compare_days():
    """Compare two days of sales data"""
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')
    
    if not date1 or not date2:
        return jsonify({'success': False, 'error': 'Both dates are required'}), 400
    
    try:
        # Get data for both days
        day1_data = sales_collection.find_one({'date': date1})
        day2_data = sales_collection.find_one({'date': date2})
        
        if not day1_data or not day2_data:
            return jsonify({'success': False, 'error': 'One or both days not found'}), 404
        
        # Convert to JSON serializable format
        def convert_for_json(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            return obj
        
        day1_data = convert_for_json(day1_data)
        day2_data = convert_for_json(day2_data)
        
        # Calculate totals for both days
        day1_totals = calculate_detailed_totals(day1_data)
        day2_totals = calculate_detailed_totals(day2_data)
        
        # Calculate comparison
        comparison = {
            'cash_sales_change': day2_totals['cash_sales']['total_amount'] - day1_totals['cash_sales']['total_amount'],
            'cash_sales_change_percent': ((day2_totals['cash_sales']['total_amount'] - day1_totals['cash_sales']['total_amount']) / day1_totals['cash_sales']['total_amount'] * 100) if day1_totals['cash_sales']['total_amount'] > 0 else 0,
            'expenses_change': day2_totals['expenses']['total_amount'] - day1_totals['expenses']['total_amount'],
            'expenses_change_percent': ((day2_totals['expenses']['total_amount'] - day1_totals['expenses']['total_amount']) / day1_totals['expenses']['total_amount'] * 100) if day1_totals['expenses']['total_amount'] > 0 else 0,
            'net_profit_change': day2_totals['net_profit'] - day1_totals['net_profit'],
            'net_profit_change_percent': ((day2_totals['net_profit'] - day1_totals['net_profit']) / abs(day1_totals['net_profit']) * 100) if day1_totals['net_profit'] != 0 else 0
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'day1': {
                'date': date1,
                'totals': day1_totals,
                'summary': generate_summary_report(day1_data, day1_totals)
            },
            'day2': {
                'date': date2,
                'totals': day2_totals,
                'summary': generate_summary_report(day2_data, day2_totals)
            }
        })
        
    except Exception as e:
        print(f"Error in compare_days: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500