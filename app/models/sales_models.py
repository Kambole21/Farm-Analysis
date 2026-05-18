# app/models/sales_models.py
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import date

class StockSection(BaseModel):
    name: str
    quantity: float
    unit: str
    unit_price: float
    section_total: Optional[float] = None
    
    @validator('section_total', always=True)
    def calculate_section_total(cls, v, values):
        return values['quantity'] * values['unit_price']

class OpeningStock(BaseModel):
    product_type: str
    sections: List[StockSection]
    total_value: Optional[float] = None
    
    @validator('total_value', always=True)
    def calculate_total_value(cls, v, values):
        return sum(section.section_total for section in values['sections'])

class Revenue(BaseModel):
    revenue_name: str
    amount: float
    description: Optional[str] = ""

class CreditSale(BaseModel):
    credit_holder: str
    product_type: str
    section: str
    quantity: float
    unit_price: float
    total: Optional[float] = None
    due_date: Optional[date] = None
    
    @validator('total', always=True)
    def calculate_total(cls, v, values):
        return values['quantity'] * values['unit_price']

class Expense(BaseModel):
    description: str
    amount: float
    category: str = "general"

class BankDeposit(BaseModel):
    expected_deposit: float = 0
    actual_deposit: float = 0
    cash_on_hand: float = 0

class CreditOwed(BaseModel):
    debtor_name: str
    farm_name: Optional[str] = ""
    amount: float
    description: Optional[str] = ""
    due_date: Optional[date] = None