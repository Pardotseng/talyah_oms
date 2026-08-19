from flask import Blueprint, render_template

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
def orders_page():
    return "訂單模組建置中"
