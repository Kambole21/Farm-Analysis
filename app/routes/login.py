from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.forms import LoginForm
from app import users_collection
from werkzeug.security import check_password_hash

bp = Blueprint('login', __name__)

@bp.route('/')
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users_collection.find_one({
            "$or": [
                {"username": form.login_id.data},
                {"email": form.login_id.data},
                {"role": form.login_id.data}
            ]
        })
        
        if user and check_password_hash(user['password'], form.password.data):
            session['user_id'] = str(user['_id'])
            session['user_name'] = f"{user.get('fname', '')} {user.get('lastname', '')}"
            session['user_email'] = user.get('email', '')
            session['role'] = user.get('role', '')  # Set role in session
            print(f"DEBUG: User role set in login: {session['role']}")  # Debug print
            flash('Logged in successfully!', 'success')
            return redirect(url_for('sales.sales_management'))
        else:
            flash('Invalid username/email or password', 'danger')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login.login'))