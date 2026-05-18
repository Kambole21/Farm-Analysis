# app/forms/sales_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class OpeningStockForm(FlaskForm):
    product_type = SelectField('Product Type', validators=[DataRequired()])
    submit = SubmitField('Save Opening Stock')

class RevenueForm(FlaskForm):
    revenue_name = StringField('Revenue Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description')
    submit = SubmitField('Add Revenue')

class CreditSaleForm(FlaskForm):
    credit_holder = StringField('Credit Holder', validators=[DataRequired()])
    product_type = SelectField('Product Type', validators=[DataRequired()])
    section = SelectField('Section', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = FloatField('Unit Price', validators=[DataRequired(), NumberRange(min=0)])
    due_date = DateField('Due Date', validators=[Optional()])
    submit = SubmitField('Add Credit Sale')

class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('general', 'General'),
        ('feed', 'Animal Feed'),
        ('labor', 'Labor'),
        ('maintenance', 'Maintenance'),
        ('transport', 'Transport'),
        ('other', 'Other')
    ])
    submit = SubmitField('Add Expense')

class BankDepositForm(FlaskForm):
    expected_deposit = FloatField('Expected Deposit', validators=[Optional(), NumberRange(min=0)])
    actual_deposit = FloatField('Actual Deposit', validators=[Optional(), NumberRange(min=0)])
    cash_on_hand = FloatField('Cash on Hand', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Bank Details')

class CreditOwedForm(FlaskForm):
    debtor_name = StringField('Debtor Name', validators=[DataRequired()])
    farm_name = StringField('Farm Name')
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description')
    due_date = DateField('Due Date', validators=[Optional()])
    submit = SubmitField('Add Credit Owed')