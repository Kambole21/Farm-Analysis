# the file below is farm_sales.py

from flask import Blueprint, session, render_template, redirect, request, flash, jsonify
from datetime import datetime
import os
from bson import ObjectId
from app import (
    farm_report_collection, 
    farm_dates_collection,
    farm_poultry_collection,
    farm_sales_collection,
    farm_production_collection,
    farm_feed_collection,
    farm_mortality_collection,
    farm_percentage_collection
)

bp = Blueprint('farm_report', __name__)

@bp.route('/Farm-Report')
def farm_management():
    """Main farm management dashboard"""
    return render_template('sales/farm/farm_management.html')

@bp.route('/farm-report')
def farm_report():
    """Farm report listing page"""
    # Get all report dates
    report_dates = list(farm_dates_collection.find().sort('date', -1))
    return render_template('sales/farm/farm_report.html', report_dates=report_dates)

@bp.route('/farm-report/<date>')
def view_farm_report_day(date):
    """View/Edit farm report for a specific date"""
    report_date = farm_dates_collection.find_one({'date': date})
    if not report_date:
        flash('Report date not found', 'error')
        return redirect('/farm-report')
    
    # Get all data for this date
    poultry_data = list(farm_poultry_collection.find({'date': date}))
    sales_data = list(farm_sales_collection.find({'date': date}))
    production_data = list(farm_production_collection.find({'date': date}))
    feed_data = list(farm_feed_collection.find({'date': date}))
    mortality_data = list(farm_mortality_collection.find({'date': date}))
    percentage_data = list(farm_percentage_collection.find({'date': date}))
    
    return render_template('sales/farm/view_farm_report_day.html',
                          date=date,
                          poultry_data=poultry_data,
                          sales_data=sales_data,
                          production_data=production_data,
                          feed_data=feed_data,
                          mortality_data=mortality_data,
                          percentage_data=percentage_data)

@bp.route('/farm-analysis')
def farm_analysis():
    """Farm analysis and reports page"""
    # Get all dates for analysis
    dates = list(farm_dates_collection.find().sort('date', -1).limit(30))
    return render_template('sales/farm/farm_analysis.html', dates=dates)

@bp.route('/api/farm-analysis-data')
def get_farm_analysis_data():
    """API endpoint for farm analysis data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 0))
    
    query = {}
    if start_date and end_date:
        query['date'] = {'$gte': start_date, '$lte': end_date}
    
    dates_cursor = farm_dates_collection.find(query).sort('date', -1)
    if limit > 0:
        dates_cursor = dates_cursor.limit(limit)
    
    dates = list(dates_cursor)
    
    analysis_data = []
    for date_doc in dates:
        date = date_doc['date']
        
        # Get poultry data
        poultry_data = list(farm_poultry_collection.find({'date': date}))
        total_gross = sum(p.get('gross_profit', 0) for p in poultry_data)
        total_damage = sum(p.get('damage_value', 0) for p in poultry_data)
        total_net = sum(p.get('net_production', 0) for p in poultry_data)
        
        # Get sales data
        sales_data = list(farm_sales_collection.find({'date': date}))
        total_sales = sum(s.get('total_value', 0) for s in sales_data)
        
        # Get production data
        production_data = list(farm_production_collection.find({'date': date}))
        total_production = sum(p.get('quantity', 0) for p in production_data)
        
        # Get mortality data
        mortality_data = list(farm_mortality_collection.find({'date': date}))
        total_mortality = sum(m.get('mortality_count', 0) for m in mortality_data)
        
        # Get feed data
        feed_data = list(farm_feed_collection.find({'date': date}))
        total_feed = sum(f.get('bags_used', 0) for f in feed_data)
        
        analysis_data.append({
            'date': date,
            'total_gross': total_gross,
            'total_damage': total_damage,
            'total_net': total_net,
            'total_sales': total_sales,
            'total_production': total_production,
            'total_mortality': total_mortality,
            'total_feed': total_feed
        })
    
    return jsonify(analysis_data)

@bp.route('/api/create-report-date', methods=['POST'])
def create_report_date():
    """Create a new report date"""
    date = request.form.get('date')
    
    if not date:
        return jsonify({'success': False, 'message': 'Date is required'})
    
    # Check if date already exists
    existing = farm_dates_collection.find_one({'date': date})
    if existing:
        return jsonify({'success': False, 'message': 'Report date already exists'})
    
    # Create date entry
    farm_dates_collection.insert_one({
        'date': date,
        'created_at': datetime.now(),
        'created_by': session.get('username', 'Unknown')
    })
    
    return jsonify({'success': True, 'message': 'Report date created successfully'})

@bp.route('/api/update-poultry', methods=['POST'])
def update_poultry():
    """Update poultry data"""
    date = request.form.get('date')
    poultry_house = request.form.get('poultry_house')
    
    data = {
        'date': date,
        'poultry_house': poultry_house,
        'gross_profit': float(request.form.get('gross_profit', 0)),
        'damage_value': float(request.form.get('damage_value', 0)),
        'net_production': float(request.form.get('net_production', 0)),
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_poultry_collection.update_one(
        {'date': date, 'poultry_house': poultry_house},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Poultry data updated successfully'})

@bp.route('/api/update-sales', methods=['POST'])
def update_sales():
    """Update farm sales data"""
    date = request.form.get('date')
    product_type = request.form.get('product_type')
    quantity = float(request.form.get('quantity', 0))
    unit_price = float(request.form.get('unit_price', 0))
    
    data = {
        'date': date,
        'product_type': product_type,
        'quantity': quantity,
        'unit_price': unit_price,
        'total_value': quantity * unit_price,
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_sales_collection.update_one(
        {'date': date, 'product_type': product_type},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Sales data updated successfully'})

@bp.route('/api/update-production', methods=['POST'])
def update_production():
    """Update production data"""
    date = request.form.get('date')
    product_type = request.form.get('product_type')
    
    data = {
        'date': date,
        'product_type': product_type,
        'quantity': float(request.form.get('quantity', 0)),
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_production_collection.update_one(
        {'date': date, 'product_type': product_type},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Production data updated successfully'})

@bp.route('/api/update-feed', methods=['POST'])
def update_feed():
    """Update feed data"""
    date = request.form.get('date')
    poultry_house = request.form.get('poultry_house')
    
    data = {
        'date': date,
        'poultry_house': poultry_house,
        'bags_used': float(request.form.get('bags_used', 0)),
        'feed_type': request.form.get('feed_type', 'Standard'),
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_feed_collection.update_one(
        {'date': date, 'poultry_house': poultry_house},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Feed data updated successfully'})

@bp.route('/api/update-mortality', methods=['POST'])
def update_mortality():
    """Update mortality data"""
    date = request.form.get('date')
    poultry_house = request.form.get('poultry_house')
    
    data = {
        'date': date,
        'poultry_house': poultry_house,
        'mortality_count': int(request.form.get('mortality_count', 0)),
        'mortality_reason': request.form.get('mortality_reason', ''),
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_mortality_collection.update_one(
        {'date': date, 'poultry_house': poultry_house},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Mortality data updated successfully'})

@bp.route('/api/update-percentage', methods=['POST'])
def update_percentage():
    """Update percentage data"""
    date = request.form.get('date')
    poultry_house = request.form.get('poultry_house')
    
    data = {
        'date': date,
        'poultry_house': poultry_house,
        'percentage_value': float(request.form.get('percentage_value', 0)),
        'percentage_type': request.form.get('percentage_type', 'Production'),
        'updated_at': datetime.now(),
        'updated_by': session.get('username', 'Unknown')
    }
    
    # Update or insert
    farm_percentage_collection.update_one(
        {'date': date, 'poultry_house': poultry_house},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({'success': True, 'message': 'Percentage data updated successfully'})

@bp.route('/api/get-report-data/<date>')
def get_report_data(date):
    """Get all report data for a specific date"""
    poultry_data = list(farm_poultry_collection.find({'date': date}))
    sales_data = list(farm_sales_collection.find({'date': date}))
    production_data = list(farm_production_collection.find({'date': date}))
    feed_data = list(farm_feed_collection.find({'date': date}))
    mortality_data = list(farm_mortality_collection.find({'date': date}))
    percentage_data = list(farm_percentage_collection.find({'date': date}))
    
    # Calculate totals
    total_poultry = {
        'total_gross': sum(p.get('gross_profit', 0) for p in poultry_data),
        'total_damage': sum(p.get('damage_value', 0) for p in poultry_data),
        'total_net': sum(p.get('net_production', 0) for p in poultry_data)
    }
    
    total_sales = sum(s.get('total_value', 0) for s in sales_data)
    total_production = sum(p.get('quantity', 0) for p in production_data)
    total_feed = sum(f.get('bags_used', 0) for f in feed_data)
    total_mortality = sum(m.get('mortality_count', 0) for m in mortality_data)
    
    return jsonify({
        'poultry_data': poultry_data,
        'sales_data': sales_data,
        'production_data': production_data,
        'feed_data': feed_data,
        'mortality_data': mortality_data,
        'percentage_data': percentage_data,
        'totals': {
            'poultry': total_poultry,
            'sales': total_sales,
            'production': total_production,
            'feed': total_feed,
            'mortality': total_mortality
        }
    })

@bp.route('/api/delete-report-date/<date>', methods=['DELETE'])
def delete_report_date(date):
    """Delete a report date and all associated data"""
    # Delete all data for this date
    farm_dates_collection.delete_one({'date': date})
    farm_poultry_collection.delete_many({'date': date})
    farm_sales_collection.delete_many({'date': date})
    farm_production_collection.delete_many({'date': date})
    farm_feed_collection.delete_many({'date': date})
    farm_mortality_collection.delete_many({'date': date})
    farm_percentage_collection.delete_many({'date': date})
    
    return jsonify({'success': True, 'message': 'Report date deleted successfully'})