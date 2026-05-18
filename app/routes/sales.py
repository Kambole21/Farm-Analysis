# the above file is sales.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from datetime import datetime
from app import (
    sales_collection, stock_on_hand_collection, revenue_collection,
    credit_sales_collection, expenses_collection,
    expected_deposit_collection, actual_deposit_collection, cash_on_hand_collection,
    closing_stock_collection, credit_owed_collection, dates_collection
)
from bson import ObjectId
import traceback

bp = Blueprint('sales', __name__)

# Initialize product types and their sections
PRODUCT_TYPES = {
    'eggs': {
        'name': 'Eggs',
        'sections': ['Big', 'Medium', 'White'],
        'units': 'tray'
    },
    'chicken': {
        'name': 'Chicken',
        'sections': ['Broiler', 'Layer', 'Roaster'],
        'units': 'kg'
    },
    'feed': {
        'name': 'Animal Feed',
        'sections': ['Starter', 'Grower', 'Finisher'],
        'units': 'bag'
    }
}

@bp.route('/Chatwala-Sales', methods=['GET'])
def sales_management():
    # Check if there's an active day session
    active_date = session.get('active_sales_date')
    sales_data = None
    
    if active_date:
        # Fetch existing data for this date
        sales_data = sales_collection.find_one({'date': active_date})
    
    # Get all available dates for dropdown
    dates = list(dates_collection.find().sort('date', -1))
    
    # Get today's date for default value
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('sales/sales_management.html', 
                         active_date=active_date,
                         sales_data=sales_data,
                         product_types=PRODUCT_TYPES,
                         dates=dates,
                         today=today)

@bp.route('/start-day', methods=['POST'])
def start_day():
    date_str = request.form.get('date')
    
    if not date_str:
        flash('Please select a date', 'danger')
        return redirect(url_for('sales.sales_management'))
    
    try:
        # Parse and format date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%Y-%m-%d')
        
        # Check if day already exists
        existing_day = sales_collection.find_one({'date': formatted_date})
        
        if existing_day:
            flash(f'Day {formatted_date} is already active!', 'warning')
        else:
            # Create new day record - using ARRAY format to match existing data
            day_record = {
                'date': formatted_date,
                'status': 'active',
                'created_at': datetime.now(),
                'opening_stock': [],  # Changed from {} to []
                'cash_sales': [],
                'credit_sales': [],
                'expenses': [],
                'bank_deposit': {},
                'closing_stock': {},
                'credits_to_farm': []
            }
            sales_collection.insert_one(day_record)
            
            # Add to dates collection
            dates_collection.update_one(
                {'date': formatted_date},
                {'$setOnInsert': {'date': formatted_date}},
                upsert=True
            )
            
            flash(f'Day {formatted_date} started successfully!', 'success')
        
        # Set active date in session
        session['active_sales_date'] = formatted_date
        
    except ValueError:
        flash('Invalid date format', 'danger')
    
    return redirect(url_for('sales.sales_management'))

# In sales.py, update the add_opening_stock function:
@bp.route('/add-opening-stock', methods=['POST'])
def add_opening_stock():
    try:
        active_date = session.get('active_sales_date')
        username = session.get('user_name')  # Get logged in user
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day. Please start a day first.'}), 400
        
        if not username:
            return jsonify({'success': False, 'message': 'User not logged in'}), 401
        
        product_type = request.form.get('product_type')
        section = request.form.get('section')
        quantity = request.form.get('quantity')
        unit_price = request.form.get('unit_price')
        
        # Validate required fields
        if not all([product_type, section, quantity, unit_price]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        quantity = float(quantity)
        unit_price = float(unit_price)
        
        # Prepare section data WITH USER INFO
        section_data = {
            'name': section.capitalize(),
            'quantity': quantity,
            'unit_price': unit_price,
            'section_total': quantity * unit_price,
            'recorded_by': username,  # Add user who recorded
            'recorded_at': datetime.now()
        }
        
        # Get the current day record
        day_record = sales_collection.find_one({'date': active_date})
        if not day_record:
            return jsonify({'success': False, 'message': 'Day not found'}), 404
        
        # Check if opening_stock exists as array
        opening_stock = day_record.get('opening_stock', [])
        
        # Find if product type already exists
        product_index = -1
        for i, product in enumerate(opening_stock):
            if product.get('product_type') == product_type:
                product_index = i
                break
        
        # Prepare section data
        section_data = {
            'name': section.capitalize(),
            'quantity': quantity,
            'unit_price': unit_price,
            'section_total': quantity * unit_price
        }
        
        if product_index == -1:
            # Create new product entry
            new_product = {
                'product_type': product_type,
                'sections': [section_data],
                'total_value': quantity * unit_price
            }
            
            # Add to opening_stock array
            result = sales_collection.update_one(
                {'date': active_date},
                {'$push': {'opening_stock': new_product}}
            )
        else:
            # Check if section already exists
            section_index = -1
            for i, sec in enumerate(opening_stock[product_index].get('sections', [])):
                if sec.get('name') == section.capitalize():
                    section_index = i
                    break
            
            if section_index == -1:
                # Add new section
                result = sales_collection.update_one(
                    {'date': active_date, 'opening_stock.product_type': product_type},
                    {'$push': {'opening_stock.$.sections': section_data}}
                )
            else:
                # Update existing section
                result = sales_collection.update_one(
                    {'date': active_date, 'opening_stock.product_type': product_type},
                    {'$set': {
                        f'opening_stock.$.sections.{section_index}.quantity': quantity,
                        f'opening_stock.$.sections.{section_index}.unit_price': unit_price,
                        f'opening_stock.$.sections.{section_index}.section_total': quantity * unit_price
                    }}
                )
            
            # Recalculate total value
            product_record = sales_collection.find_one(
                {'date': active_date, 'opening_stock.product_type': product_type},
                {'opening_stock.$': 1}
            )
            
            if product_record and product_record.get('opening_stock'):
                product = product_record['opening_stock'][0]
                total_value = sum(sec.get('section_total', 0) for sec in product.get('sections', []))
                
                sales_collection.update_one(
                    {'date': active_date, 'opening_stock.product_type': product_type},
                    {'$set': {'opening_stock.$.total_value': total_value}}
                )
        
        
        return jsonify({
            'success': True, 
            'message': 'Opening stock added successfully',
            'data': section_data
        })
            
    except ValueError as e:
        print(f"ValueError: {e}")
        return jsonify({'success': False, 'message': 'Invalid number format'}), 400
    except Exception as e:
        print(f"Error in add_opening_stock: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
    

@bp.route('/add-cash-sale', methods=['POST'])
def add_cash_sale():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day. Please start a day first.'}), 400
        
        sale_name = request.form.get('sale_name')
        amount = request.form.get('amount')
        
        if not sale_name or not amount:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        amount = float(amount)
        
        cash_sale = {
            'name': sale_name,
            'amount': amount,
            'timestamp': datetime.now()
        }
        
        # Add to sales collection
        result = sales_collection.update_one(
            {'date': active_date},
            {'$push': {'cash_sales': cash_sale}}
        )
        
        # Also update revenue collection
        revenue_collection.insert_one({
            'date': active_date,
            'type': 'cash_sale',
            'name': sale_name,
            'amount': amount,
            'recorded_at': datetime.now()
        })
        
        return jsonify({
            'success': True, 
            'message': 'Cash sale recorded',
            'data': cash_sale
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        print(f"Error in add_cash_sale: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/add-credit-sale', methods=['POST'])
def add_credit_sale():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        credit_holder = request.form.get('credit_holder')
        product_type = request.form.get('product_type')
        section = request.form.get('section')
        quantity = request.form.get('quantity')
        unit_price = request.form.get('unit_price')
        
        if not all([credit_holder, product_type, section, quantity, unit_price]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        quantity = float(quantity)
        unit_price = float(unit_price)
        
        total_amount = quantity * unit_price
        
        credit_sale = {
            'credit_holder': credit_holder,
            'product_type': product_type,
            'section': section.capitalize(),
            'quantity': quantity,
            'unit_price': unit_price,
            'total_amount': total_amount,
            'timestamp': datetime.now()
        }
        
        sales_collection.update_one(
            {'date': active_date},
            {'$push': {'credit_sales': credit_sale}}
        )
        
        # Update credit sales collection
        credit_sales_collection.insert_one({
            'date': active_date,
            'credit_holder': credit_holder,
            'product_type': product_type,
            'section': section.capitalize(),
            'quantity': quantity,
            'unit_price': unit_price,
            'total_amount': total_amount,
            'status': 'pending',
            'recorded_at': datetime.now()
        })
        
        return jsonify({
            'success': True, 
            'message': 'Credit sale recorded',
            'data': credit_sale
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid number format'}), 400
    except Exception as e:
        print(f"Error in add_credit_sale: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/add-expense', methods=['POST'])
def add_expense():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        description = request.form.get('description')
        amount = request.form.get('amount')
        
        if not description or not amount:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        amount = float(amount)
        
        expense = {
            'description': description,
            'amount': amount,
            'timestamp': datetime.now()
        }
        
        sales_collection.update_one(
            {'date': active_date},
            {'$push': {'expenses': expense}}
        )
        
        # Update expenses collection
        expenses_collection.insert_one({
            'date': active_date,
            'description': description,
            'amount': amount,
            'recorded_at': datetime.now()
        })
        
        return jsonify({
            'success': True, 
            'message': 'Expense recorded',
            'data': expense
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        print(f"Error in add_expense: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/update-bank-deposit', methods=['POST'])
def update_bank_deposit():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        deposit_type = request.form.get('deposit_type')  # 'expected' or 'actual'
        amount = request.form.get('amount')
        
        if not deposit_type or not amount:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        amount = float(amount)
        
        # Get current bank deposit data
        day_record = sales_collection.find_one({'date': active_date})
        bank_deposit = day_record.get('bank_deposit', {}) if day_record else {}
        
        # Update the specific deposit type
        bank_deposit[deposit_type] = amount
        
        # Update sales collection
        result = sales_collection.update_one(
            {'date': active_date},
            {'$set': {'bank_deposit': bank_deposit}}
        )
        
        # Update specific deposit collection
        if deposit_type == 'expected':
            expected_deposit_collection.update_one(
                {'date': active_date},
                {'$set': {'amount': amount}},
                upsert=True
            )
        elif deposit_type == 'actual':
            actual_deposit_collection.update_one(
                {'date': active_date},
                {'$set': {'amount': amount}},
                upsert=True
            )
        
        return jsonify({
            'success': True, 
            'message': f'{deposit_type.capitalize()} deposit updated',
            'data': {deposit_type: amount}
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        print(f"Error in update_bank_deposit: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/update-cash-on-hand', methods=['POST'])
def update_cash_on_hand():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        amount = request.form.get('amount')
        
        if not amount:
            return jsonify({'success': False, 'message': 'Amount is required'}), 400
        
        amount = float(amount)
        
        # Update sales collection
        result = sales_collection.update_one(
            {'date': active_date},
            {'$set': {'cash_on_hand': amount}}
        )
        
        # Update cash on hand collection
        cash_on_hand_collection.update_one(
            {'date': active_date},
            {'$set': {'amount': amount}},
            upsert=True
        )
        
        return jsonify({
            'success': True, 
            'message': 'Cash on hand updated',
            'data': {'cash_on_hand': amount}
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        print(f"Error in update_cash_on_hand: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/add-closing-stock', methods=['POST'])
def add_closing_stock():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        product_type = request.form.get('product_type')
        section = request.form.get('section')
        quantity = request.form.get('quantity')
        
        if not all([product_type, section, quantity]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        quantity = float(quantity)
        
        # Get current closing stock
        day_record = sales_collection.find_one({'date': active_date})
        closing_stock = day_record.get('closing_stock', {}) if day_record else {}
        
        # Initialize product type if not exists
        if product_type not in closing_stock:
            closing_stock[product_type] = {}
        
        # Update section quantity
        closing_stock[product_type][section] = {'quantity': quantity}
        
        # Update sales collection
        result = sales_collection.update_one(
            {'date': active_date},
            {'$set': {'closing_stock': closing_stock}}
        )
        
        # Update closing stock collection
        closing_stock_collection.update_one(
            {
                'date': active_date,
                'product_type': product_type,
                'section': section
            },
            {'$set': {
                'quantity': quantity,
                'updated_at': datetime.now()
            }},
            upsert=True
        )
        
        return jsonify({
            'success': True, 
            'message': 'Closing stock updated',
            'data': {
                'product_type': product_type,
                'section': section,
                'quantity': quantity
            }
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity format'}), 400
    except Exception as e:
        print(f"Error in add_closing_stock: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@bp.route('/add-farm-credit', methods=['POST'])
def add_farm_credit():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            return jsonify({'success': False, 'message': 'No active day'}), 400
        
        creditor_name = request.form.get('creditor_name')
        description = request.form.get('description')
        amount = request.form.get('amount')
        
        if not all([creditor_name, description, amount]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        amount = float(amount)
        
        farm_credit = {
            'creditor_name': creditor_name,
            'description': description,
            'amount': amount,
            'timestamp': datetime.now()
        }
        
        sales_collection.update_one(
            {'date': active_date},
            {'$push': {'credits_to_farm': farm_credit}}
        )
        
        # Update credit owed collection
        credit_owed_collection.insert_one({
            'date': active_date,
            'creditor_name': creditor_name,
            'description': description,
            'amount': amount,
            'status': 'outstanding',
            'recorded_at': datetime.now()
        })
        
        return jsonify({
            'success': True, 
            'message': 'Farm credit recorded',
            'data': farm_credit
        })
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
    except Exception as e:
        print(f"Error in add_farm_credit: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@bp.route('/close-day', methods=['POST'])
def close_day():
    try:
        active_date = session.get('active_sales_date')
        
        if not active_date:
            flash('No active day', 'danger')
            return redirect(url_for('sales.sales_management'))  # change to your actual route
        
        # Update status to closed
        result = sales_collection.update_one(
            {'date': active_date},
            {'$set': {
                'status': 'closed',
                'closed_at': datetime.now()
            }}
        )
        
        if result.modified_count == 0:
            flash('Failed to close day', 'danger')
            return redirect(url_for('sales.sales_management'))
        
        # Clear active date from session
        session.pop('active_sales_date', None)
        
        flash(f'Day {active_date} closed successfully', 'success')
        return redirect(url_for('sales.sales_management'))
        
    except Exception as e:
        print(f"Error in close_day: {str(e)}")
        flash(str(e), 'danger')
        return redirect(url_for('your_blueprint.your_view'))

@bp.route('/get-day-summary/<date>')
def get_day_summary(date):
    """Get summary for a specific day"""
    try:
        sales_data = sales_collection.find_one({'date': date})
        
        if not sales_data:
            return jsonify({'error': 'Day not found'}), 404
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in sales_data:
            sales_data['_id'] = str(sales_data['_id'])
        
        # Convert timestamps in cash_sales
        if 'cash_sales' in sales_data and isinstance(sales_data['cash_sales'], list):
            for sale in sales_data['cash_sales']:
                if 'timestamp' in sale and isinstance(sale['timestamp'], datetime):
                    sale['timestamp'] = sale['timestamp'].isoformat()
        
        # Convert timestamps in credit_sales
        if 'credit_sales' in sales_data and isinstance(sales_data['credit_sales'], list):
            for sale in sales_data['credit_sales']:
                if 'timestamp' in sale and isinstance(sale['timestamp'], datetime):
                    sale['timestamp'] = sale['timestamp'].isoformat()
        
        # Convert timestamps in expenses
        if 'expenses' in sales_data and isinstance(sales_data['expenses'], list):
            for expense in sales_data['expenses']:
                if 'timestamp' in expense and isinstance(expense['timestamp'], datetime):
                    expense['timestamp'] = expense['timestamp'].isoformat()
        
        # Convert timestamps in credits_to_farm
        if 'credits_to_farm' in sales_data and isinstance(sales_data['credits_to_farm'], list):
            for credit in sales_data['credits_to_farm']:
                if 'timestamp' in credit and isinstance(credit['timestamp'], datetime):
                    credit['timestamp'] = credit['timestamp'].isoformat()
        
        # Convert datetime objects in other fields
        if 'created_at' in sales_data and isinstance(sales_data['created_at'], datetime):
            sales_data['created_at'] = sales_data['created_at'].isoformat()
        
        if 'closed_at' in sales_data and isinstance(sales_data['closed_at'], datetime):
            sales_data['closed_at'] = sales_data['closed_at'].isoformat()
        
        # Calculate totals
        totals = {
            'opening_stock_total': 0,
            'cash_sales_total': 0,
            'credit_sales_total': 0,
            'expenses_total': 0,
            'expected_deposit': sales_data.get('bank_deposit', {}).get('expected', 0),
            'actual_deposit': sales_data.get('bank_deposit', {}).get('actual', 0),
            'cash_on_hand': sales_data.get('cash_on_hand', 0),
            'farm_credits_total': 0
        }
        
        # Calculate opening stock total (handling array format)
        opening_stock = sales_data.get('opening_stock', [])
        if isinstance(opening_stock, list):
            for product in opening_stock:
                if isinstance(product, dict):
                    totals['opening_stock_total'] += product.get('total_value', 0)
        elif isinstance(opening_stock, dict):
            # Handle old format just in case
            for product_type in opening_stock.values():
                for section in product_type.values():
                    totals['opening_stock_total'] += section.get('total_value', 0)
        
        # Calculate cash sales total
        cash_sales = sales_data.get('cash_sales', [])
        for sale in cash_sales:
            if isinstance(sale, dict):
                totals['cash_sales_total'] += sale.get('amount', 0)
        
        # Calculate credit sales total
        credit_sales = sales_data.get('credit_sales', [])
        for sale in credit_sales:
            if isinstance(sale, dict):
                totals['credit_sales_total'] += sale.get('total_amount', 0)
        
        # Calculate expenses total
        expenses = sales_data.get('expenses', [])
        for expense in expenses:
            if isinstance(expense, dict):
                totals['expenses_total'] += expense.get('amount', 0)
        
        # Calculate farm credits total
        farm_credits = sales_data.get('credits_to_farm', [])
        for credit in farm_credits:
            if isinstance(credit, dict):
                totals['farm_credits_total'] += credit.get('amount', 0)
        
        # Calculate profit/loss
        totals['gross_profit'] = totals['cash_sales_total'] + totals['credit_sales_total']
        totals['net_profit'] = totals['gross_profit'] - totals['expenses_total']
        
        return jsonify({
            'success': True,
            'sales_data': sales_data, 
            'totals': totals
        })
        
    except Exception as e:
        print(f"Error in get_day_summary: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/select-day', methods=['POST'])
def select_day():
    date = request.form.get('date')
    
    if not date:
        flash('Please select a date', 'danger')
        return redirect(url_for('sales.sales_management'))
    
    # Set as active date
    session['active_sales_date'] = date
    flash(f'Day {date} selected', 'success')
    
    return redirect(url_for('sales.sales_management'))