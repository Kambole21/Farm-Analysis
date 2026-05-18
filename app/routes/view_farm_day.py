# the file below is view_faarm.py

from flask import Blueprint, session, render_template, request, jsonify
from datetime import datetime
from app import (
    farm_dates_collection,
    farm_poultry_collection,
    farm_sales_collection,
    farm_production_collection,
    farm_feed_collection,
    farm_mortality_collection,
    farm_percentage_collection,
    users_collection
)
from bson import ObjectId
import traceback

bp = Blueprint('view_farm_day', __name__)

@bp.route('/View-Farm-Date')
def farm_day():
    """View all farm dates"""
    try:
        dates = list(farm_dates_collection.find(
            {},
            {'date': 1, 'created_at': 1, 'created_by': 1}
        ).sort('date', -1))

        print(f"Found {len(dates)} farm dates in database")  # Debug log
        
        # Convert ObjectId and datetime to string for JSON serialization
        for date in dates:
            if '_id' in date:
                date['_id'] = str(date['_id'])
            if 'created_at' in date and isinstance(date['created_at'], datetime):
                date['created_at'] = date['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Ensure date field exists
            if 'date' not in date:
                print(f"Warning: Date document missing 'date' field: {date}")
        
        # Print the dates being passed to template
        print(f"Dates being sent to template: {dates}")
        
        return render_template('sales/farm/view_farm_day.html', dates=dates)
    except Exception as e:
        print(f"Error in farm_day: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('sales/farm/view_farm_day.html', dates=[])

@bp.route('/get-farm-day-details/<date>')
def get_farm_day_details(date):
    """Get detailed information for a specific farm day"""
    try:
        # Check if date exists
        date_doc = farm_dates_collection.find_one({'date': date})
        if not date_doc:
            return jsonify({'success': False, 'error': 'Farm day not found'}), 404

        # Get all data for this date
        poultry_data = list(farm_poultry_collection.find({'date': date}))
        sales_data = list(farm_sales_collection.find({'date': date}))
        production_data = list(farm_production_collection.find({'date': date}))
        feed_data = list(farm_feed_collection.find({'date': date}))
        mortality_data = list(farm_mortality_collection.find({'date': date}))
        percentage_data = list(farm_percentage_collection.find({'date': date}))

        # Get user information for all users who recorded data
        user_records = {}

        # Function to extract user info from data
        def extract_user_info(data, field_name='updated_by'):
            if isinstance(data, dict):
                if field_name in data:
                    username = data[field_name]
                    if username and username not in user_records:
                        user = users_collection.find_one({'username': username})
                        if user:
                            user_records[username] = {
                                'username': username,
                                'full_name': f"{user.get('fname', '')} {user.get('lastname', '')}".strip(),
                                'role': user.get('role', 'Unknown')
                            }
                for value in data.values():
                    extract_user_info(value, field_name)
            elif isinstance(data, list):
                for item in data:
                    extract_user_info(item, field_name)

        # Extract user info from all sections
        extract_user_info(poultry_data)
        extract_user_info(sales_data)
        extract_user_info(production_data)
        extract_user_info(feed_data)
        extract_user_info(mortality_data)
        extract_user_info(percentage_data)
        
        # Add creator to user records
        if date_doc.get('created_by'):
            creator = date_doc['created_by']
            if creator not in user_records:
                user = users_collection.find_one({'username': creator})
                if user:
                    user_records[creator] = {
                        'username': creator,
                        'full_name': f"{user.get('fname', '')} {user.get('lastname', '')}".strip(),
                        'role': user.get('role', 'Unknown')
                    }

        # Convert MongoDB documents to JSON serializable format
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

        # Calculate detailed totals
        totals = calculate_farm_totals(
            poultry_data, sales_data, production_data, 
            feed_data, mortality_data, percentage_data
        )

        # Generate activity log
        activity_log = generate_farm_activity_log(
            poultry_data, sales_data, production_data, 
            feed_data, mortality_data, percentage_data, date_doc
        )

        # Generate summary report
        summary = generate_farm_summary(
            date_doc, poultry_data, sales_data, production_data, 
            feed_data, mortality_data, percentage_data, totals
        )

        return jsonify({
            'success': True,
            'date_info': convert_for_json(date_doc),
            'poultry_data': convert_for_json(poultry_data),
            'sales_data': convert_for_json(sales_data),
            'production_data': convert_for_json(production_data),
            'feed_data': convert_for_json(feed_data),
            'mortality_data': convert_for_json(mortality_data),
            'percentage_data': convert_for_json(percentage_data),
            'totals': totals,
            'user_records': user_records,
            'activity_log': activity_log,
            'summary': summary
        })

    except Exception as e:
        print(f"Error in get_farm_day_details: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_farm_totals(poultry_data, sales_data, production_data, feed_data, mortality_data, percentage_data):
    """Calculate detailed totals for farm data"""
    totals = {
        'poultry': {
            'total_gross': 0,
            'total_damage': 0,
            'total_net': 0,
            'houses': [],
            'count': 0
        },
        'sales': {
            'total_amount': 0,
            'by_product': {},
            'items': [],
            'count': 0
        },
        'production': {
            'total_quantity': 0,
            'by_product': {},
            'items': [],
            'count': 0
        },
        'feed': {
            'total_bags': 0,
            'by_house': {},
            'by_type': {},
            'items': [],
            'count': 0
        },
        'mortality': {
            'total_count': 0,
            'by_house': {},
            'by_reason': {},
            'items': [],
            'count': 0
        },
        'percentage': {
            'by_house': {},
            'by_type': {},
            'items': [],
            'count': 0
        }
    }

    # Poultry Data Analysis
    for poultry in poultry_data:
        house_data = {
            'house': poultry.get('poultry_house', 'Unknown'),
            'gross': poultry.get('gross_profit', 0),
            'damage': poultry.get('damage_value', 0),
            'net': poultry.get('net_production', 0),
            'updated_by': poultry.get('updated_by', 'Unknown'),
            'updated_at': poultry.get('updated_at', '')
        }
        totals['poultry']['houses'].append(house_data)
        totals['poultry']['total_gross'] += poultry.get('gross_profit', 0)
        totals['poultry']['total_damage'] += poultry.get('damage_value', 0)
        totals['poultry']['total_net'] += poultry.get('net_production', 0)
        totals['poultry']['count'] += 1

    # Sales Data Analysis
    for sale in sales_data:
        product = sale.get('product_type', 'Unknown')
        amount = sale.get('total_value', 0)
        
        sale_item = {
            'product_type': product,
            'quantity': sale.get('quantity', 0),
            'unit_price': sale.get('unit_price', 0),
            'total_value': amount,
            'updated_by': sale.get('updated_by', 'Unknown'),
            'updated_at': sale.get('updated_at', '')
        }
        totals['sales']['items'].append(sale_item)
        totals['sales']['total_amount'] += amount
        totals['sales']['count'] += 1
        
        if product not in totals['sales']['by_product']:
            totals['sales']['by_product'][product] = 0
        totals['sales']['by_product'][product] += amount

    # Production Data Analysis
    for prod in production_data:
        product = prod.get('product_type', 'Unknown')
        quantity = prod.get('quantity', 0)
        
        prod_item = {
            'product_type': product,
            'quantity': quantity,
            'updated_by': prod.get('updated_by', 'Unknown'),
            'updated_at': prod.get('updated_at', '')
        }
        totals['production']['items'].append(prod_item)
        totals['production']['total_quantity'] += quantity
        totals['production']['count'] += 1
        
        if product not in totals['production']['by_product']:
            totals['production']['by_product'][product] = 0
        totals['production']['by_product'][product] += quantity

    # Feed Data Analysis
    for feed in feed_data:
        house = feed.get('poultry_house', 'Unknown')
        feed_type = feed.get('feed_type', 'Standard')
        bags = feed.get('bags_used', 0)
        
        feed_item = {
            'house': house,
            'feed_type': feed_type,
            'bags_used': bags,
            'updated_by': feed.get('updated_by', 'Unknown'),
            'updated_at': feed.get('updated_at', '')
        }
        totals['feed']['items'].append(feed_item)
        totals['feed']['total_bags'] += bags
        totals['feed']['count'] += 1
        
        if house not in totals['feed']['by_house']:
            totals['feed']['by_house'][house] = 0
        totals['feed']['by_house'][house] += bags
        
        if feed_type not in totals['feed']['by_type']:
            totals['feed']['by_type'][feed_type] = 0
        totals['feed']['by_type'][feed_type] += bags

    # Mortality Data Analysis
    for mortality in mortality_data:
        house = mortality.get('poultry_house', 'Unknown')
        reason = mortality.get('mortality_reason', 'Unknown')
        count = mortality.get('mortality_count', 0)
        
        mortality_item = {
            'house': house,
            'reason': reason,
            'count': count,
            'updated_by': mortality.get('updated_by', 'Unknown'),
            'updated_at': mortality.get('updated_at', '')
        }
        totals['mortality']['items'].append(mortality_item)
        totals['mortality']['total_count'] += count
        totals['mortality']['count'] += 1
        
        if house not in totals['mortality']['by_house']:
            totals['mortality']['by_house'][house] = 0
        totals['mortality']['by_house'][house] += count
        
        if reason not in totals['mortality']['by_reason']:
            totals['mortality']['by_reason'][reason] = 0
        totals['mortality']['by_reason'][reason] += count

    # Percentage Data Analysis
    for percent in percentage_data:
        house = percent.get('poultry_house', 'Unknown')
        p_type = percent.get('percentage_type', 'Production')
        value = percent.get('percentage_value', 0)
        
        percent_item = {
            'house': house,
            'type': p_type,
            'value': value,
            'updated_by': percent.get('updated_by', 'Unknown'),
            'updated_at': percent.get('updated_at', '')
        }
        totals['percentage']['items'].append(percent_item)
        totals['percentage']['count'] += 1
        
        if house not in totals['percentage']['by_house']:
            totals['percentage']['by_house'][house] = {}
        if p_type not in totals['percentage']['by_house'][house]:
            totals['percentage']['by_house'][house][p_type] = value

    # Calculate derived metrics
    totals['efficiency_rate'] = (
        (totals['production']['total_quantity'] / totals['feed']['total_bags'] * 100) 
        if totals['feed']['total_bags'] > 0 else 0
    )
    totals['mortality_rate'] = (
        (totals['mortality']['total_count'] / (totals['poultry']['total_net'] + totals['mortality']['total_count']) * 100)
        if (totals['poultry']['total_net'] + totals['mortality']['total_count']) > 0 else 0
    )
    totals['profit_per_bag'] = (
        totals['poultry']['total_net'] / totals['feed']['total_bags']
        if totals['feed']['total_bags'] > 0 else 0
    )

    return totals

def generate_farm_activity_log(poultry_data, sales_data, production_data, feed_data, mortality_data, percentage_data, date_doc):
    """Generate activity log for farm day"""
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

    # Date creation activity
    if date_doc.get('created_at'):
        add_activity(
            'Day Created',
            f"Farm day {date_doc.get('date')} was created",
            date_doc.get('created_by', 'System'),
            date_doc.get('created_at'),
            {}
        )

    # Poultry activities
    for poultry in poultry_data:
        add_activity(
            'Poultry Update',
            f"Updated poultry house {poultry.get('poultry_house')}",
            poultry.get('updated_by'),
            poultry.get('updated_at'),
            {
                'house': poultry.get('poultry_house'),
                'gross': poultry.get('gross_profit'),
                'damage': poultry.get('damage_value'),
                'net': poultry.get('net_production')
            }
        )

    # Sales activities
    for sale in sales_data:
        add_activity(
            'Sales Update',
            f"Recorded {sale.get('product_type')} sales",
            sale.get('updated_by'),
            sale.get('updated_at'),
            {
                'product': sale.get('product_type'),
                'quantity': sale.get('quantity'),
                'total': sale.get('total_value')
            }
        )

    # Production activities
    for prod in production_data:
        add_activity(
            'Production Update',
            f"Recorded {prod.get('product_type')} production",
            prod.get('updated_by'),
            prod.get('updated_at'),
            {
                'product': prod.get('product_type'),
                'quantity': prod.get('quantity')
            }
        )

    # Feed activities
    for feed in feed_data:
        add_activity(
            'Feed Update',
            f"Recorded feed usage in house {feed.get('poultry_house')}",
            feed.get('updated_by'),
            feed.get('updated_at'),
            {
                'house': feed.get('poultry_house'),
                'bags': feed.get('bags_used'),
                'type': feed.get('feed_type')
            }
        )

    # Mortality activities
    for mortality in mortality_data:
        add_activity(
            'Mortality Update',
            f"Recorded mortality in house {mortality.get('poultry_house')}",
            mortality.get('updated_by'),
            mortality.get('updated_at'),
            {
                'house': mortality.get('poultry_house'),
                'count': mortality.get('mortality_count'),
                'reason': mortality.get('mortality_reason')
            }
        )

    # Percentage activities
    for percent in percentage_data:
        add_activity(
            'Percentage Update',
            f"Updated {percent.get('percentage_type')} percentage for house {percent.get('poultry_house')}",
            percent.get('updated_by'),
            percent.get('updated_at'),
            {
                'house': percent.get('poultry_house'),
                'type': percent.get('percentage_type'),
                'value': percent.get('percentage_value')
            }
        )

    # Sort activities by timestamp (newest first)
    activity_log.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
    
    return activity_log

def generate_farm_summary(date_doc, poultry_data, sales_data, production_data, feed_data, mortality_data, percentage_data, totals):
    """Generate summary report for farm day"""
    return {
        'date': date_doc.get('date', 'Unknown'),
        'created_at': date_doc.get('created_at', ''),
        'created_by': date_doc.get('created_by', 'Unknown'),
        'financial_summary': {
            'total_gross': totals['poultry']['total_gross'],
            'total_damage': totals['poultry']['total_damage'],
            'total_net': totals['poultry']['total_net'],
            'total_sales': totals['sales']['total_amount'],
            'total_production': totals['production']['total_quantity'],
            'total_feed_used': totals['feed']['total_bags']
        },
        'efficiency_metrics': {
            'feed_efficiency': totals['efficiency_rate'],
            'mortality_rate': totals['mortality_rate'],
            'profit_per_bag': totals['profit_per_bag'],
            'avg_production_per_house': totals['production']['total_quantity'] / totals['poultry']['count'] if totals['poultry']['count'] > 0 else 0
        },
        'transaction_counts': {
            'poultry_houses': totals['poultry']['count'],
            'sales_items': totals['sales']['count'],
            'production_items': totals['production']['count'],
            'feed_records': totals['feed']['count'],
            'mortality_records': totals['mortality']['count'],
            'percentage_records': totals['percentage']['count']
        }
    }

@bp.route('/compare-farm-days', methods=['GET'])
def compare_farm_days():
    """Compare two farm days"""
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')
    
    if not date1 or not date2:
        return jsonify({'success': False, 'error': 'Both dates are required'}), 400
    
    try:
        # Get data for both days
        def get_day_data(date):
            poultry = list(farm_poultry_collection.find({'date': date}))
            sales = list(farm_sales_collection.find({'date': date}))
            production = list(farm_production_collection.find({'date': date}))
            feed = list(farm_feed_collection.find({'date': date}))
            mortality = list(farm_mortality_collection.find({'date': date}))
            percentage = list(farm_percentage_collection.find({'date': date}))
            
            totals = calculate_farm_totals(poultry, sales, production, feed, mortality, percentage)
            return totals
        
        day1_totals = get_day_data(date1)
        day2_totals = get_day_data(date2)
        
        # Calculate comparison
        comparison = {
            'net_profit_change': day2_totals['poultry']['total_net'] - day1_totals['poultry']['total_net'],
            'net_profit_change_percent': (
                (day2_totals['poultry']['total_net'] - day1_totals['poultry']['total_net']) / 
                abs(day1_totals['poultry']['total_net']) * 100
            ) if day1_totals['poultry']['total_net'] != 0 else 0,
            
            'production_change': day2_totals['production']['total_quantity'] - day1_totals['production']['total_quantity'],
            'production_change_percent': (
                (day2_totals['production']['total_quantity'] - day1_totals['production']['total_quantity']) / 
                day1_totals['production']['total_quantity'] * 100
            ) if day1_totals['production']['total_quantity'] > 0 else 0,
            
            'feed_usage_change': day2_totals['feed']['total_bags'] - day1_totals['feed']['total_bags'],
            'feed_usage_change_percent': (
                (day2_totals['feed']['total_bags'] - day1_totals['feed']['total_bags']) / 
                day1_totals['feed']['total_bags'] * 100
            ) if day1_totals['feed']['total_bags'] > 0 else 0,
            
            'mortality_change': day2_totals['mortality']['total_count'] - day1_totals['mortality']['total_count'],
            'mortality_change_percent': (
                (day2_totals['mortality']['total_count'] - day1_totals['mortality']['total_count']) / 
                day1_totals['mortality']['total_count'] * 100
            ) if day1_totals['mortality']['total_count'] > 0 else 0,
            
            'efficiency_change': day2_totals['efficiency_rate'] - day1_totals['efficiency_rate'],
            'mortality_rate_change': day2_totals['mortality_rate'] - day1_totals['mortality_rate']
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'day1': {
                'date': date1,
                'totals': day1_totals
            },
            'day2': {
                'date': date2,
                'totals': day2_totals
            }
        })
        
    except Exception as e:
        print(f"Error in compare_farm_days: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/export-farm-day-report/<date>')
def export_farm_day_report(date):
    """Export farm day report as JSON (can be extended for PDF/Excel)"""
    try:
        # Get day details
        date_doc = farm_dates_collection.find_one({'date': date})
        if not date_doc:
            return jsonify({'success': False, 'error': 'Farm day not found'}), 404
        
        poultry_data = list(farm_poultry_collection.find({'date': date}))
        sales_data = list(farm_sales_collection.find({'date': date}))
        production_data = list(farm_production_collection.find({'date': date}))
        feed_data = list(farm_feed_collection.find({'date': date}))
        mortality_data = list(farm_mortality_collection.find({'date': date}))
        percentage_data = list(farm_percentage_collection.find({'date': date}))
        
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
        
        totals = calculate_farm_totals(
            poultry_data, sales_data, production_data, 
            feed_data, mortality_data, percentage_data
        )
        
        return jsonify({
            'success': True,
            'date': date,
            'date_info': convert_for_json(date_doc),
            'poultry_data': convert_for_json(poultry_data),
            'sales_data': convert_for_json(sales_data),
            'production_data': convert_for_json(production_data),
            'feed_data': convert_for_json(feed_data),
            'mortality_data': convert_for_json(mortality_data),
            'percentage_data': convert_for_json(percentage_data),
            'totals': totals
        })
        
    except Exception as e:
        print(f"Error in export_farm_day_report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500