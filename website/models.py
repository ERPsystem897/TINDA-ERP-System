from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # One-to-many relationship with MonthlyProductData
    monthly_product_data = db.relationship('MonthlyProductData', backref='product_relation', lazy=True)
    
    # One-to-many relationship with InventoryHistory
    # Use back_populates to link it to the relationship in InventoryHistory
    inventory_history = db.relationship('InventoryHistory', back_populates='product', lazy=True)



class MonthlyProductData(db.Model):
    __tablename__ = 'monthly_product_data'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    beginning_inventory_kg = db.Column(db.Float, nullable=True)
    ending_inventory_kg = db.Column(db.Float, nullable=True)
    market_price_per_kg = db.Column(db.Float, nullable=True)
    kilos_sold = db.Column(db.Float, nullable=True)
    total_monthly_sale = db.Column(db.Float, nullable=True)
    seasonal_demand_pattern = db.Column(db.Boolean, nullable=True)
    promotional_activity = db.Column(db.Boolean, nullable=True)
    change_in_sales = db.Column(db.Integer, nullable=False)
    lag1_change_sales = db.Column(db.Integer, nullable=False)
    # Foreign key relationship to the Product
    product = db.relationship('Product', back_populates='monthly_product_data',viewonly=True)

class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stock_available = db.Column(db.Float, nullable=False, default=0)
    reserved_stock = db.Column(db.Float, nullable=False, default=0)
    reorder_level = db.Column(db.Float, nullable=False, default=0)

    product = db.relationship('Product', backref=db.backref('inventory', uselist=False))

    @property
    def available_for_sale(self):
        return self.stock_available - self.reserved_stock

    @property
    def total_inventory_value(self):
        # Fetch the most recent market price per kg for the product
        most_recent_price = db.session.query(MonthlyProductData.market_price_per_kg).filter(
            MonthlyProductData.product_id == self.product_id
        ).order_by(MonthlyProductData.month.desc()).first()
        
        # If the most recent price exists, calculate total inventory value
        if most_recent_price:
            return self.stock_available * most_recent_price[0]  # [0] to get the price from the tuple
        return 0  # If no price is found, return 0
    
class InventoryHistory(db.Model):
    __tablename__ = 'inventory_history'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    ending_inventory = db.Column(db.Integer, nullable=False)
    sales = db.Column(db.Integer, nullable=False)


    # Link back to the Product model using back_populates
    product = db.relationship('Product', back_populates='inventory_history', viewonly=False)

