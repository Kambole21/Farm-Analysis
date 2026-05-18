from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from app.forms import RegistrationForm
from app import users_collection

bp = Blueprint('register', __name__)

ROLE_CODES = {
    "admin": "@HRM.BAY.ADMIN-520001-122301@2025",
    "hr_manager": "@HRM.BAY.HRM-527002-122302@2025", 
    "hr_ast": "@HRM.BAY.HRA-534003-122304@2025",
    "account": "@HRM.BAY.ACC-541004-122305@2025",
    "sales": "@HRM.BAY.SAL-541005-122305@2026"
}

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the entered code matches any role code
        matched_role = None
        for role, code in ROLE_CODES.items():
            if form.code.data == code:
                matched_role = role
                break
        
        if not matched_role:
            flash('Invalid registration code', 'danger')
            return redirect(url_for('register.register'))
            
        hashed_password = generate_password_hash(form.password.data)
        
        user_data = {
            "username": form.username.data,
            "email": form.email.data,
            "fname": form.fname.data,
            "lastname": form.lastname.data,
            "department": form.department.data,
            "position": form.position.data,
            "contact": form.contact.data,
            "role": matched_role,  # Use the matched role instead of form data
            "password": hashed_password
        }
        
        users_collection.insert_one(user_data)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login.login'))
    
    return render_template('register.html', form=form)