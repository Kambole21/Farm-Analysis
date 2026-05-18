from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app import database

users_collection = database['Users']

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=30)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email()
    ])
    fname = StringField('First Name', validators=[
        DataRequired(), Length(min=2, max=50)
    ])
    lastname = StringField('Last Name', validators=[
        DataRequired(), Length(min=2, max=50)
    ])
    department = StringField('Department', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    contact = StringField('Contact Number', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=2)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if users_collection.find_one({"username": {"$regex": f"^{username.data}$", "$options": "i"}}):
            raise ValidationError('This username is already taken.')

    def validate_email(self, email):
        if users_collection.find_one({"email": {"$regex": f"^{email.data}$", "$options": "i"}}):
            raise ValidationError('This email is already registered.')

class LoginForm(FlaskForm):
    login_id = StringField('Username or Email', validators=[
        DataRequired()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Login')