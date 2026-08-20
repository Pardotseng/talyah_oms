from decimal import Decimal, ROUND_UP
from datetime import datetime

def talyah_round(value: Decimal) -> int:
    """
    TalYah 專屬五捨六入規則：
    - 0.5（含）以下捨去
    - 0.5 以上進位
    """
    integer_part = int(value)
    fractional_part = value - integer_part
    if fractional_part <= Decimal('0.5'):
        return integer_part
    else:
        return int(value.quantize(Decimal('1'), rounding=ROUND_UP))

def generate_invoice_no(customer_code, session, order_model):
    """
    產生訂單編號：{客戶簡碼}{西元年末兩位}{5位流水號}
    """
    current_year_str = datetime.now().strftime('%y')
    prefix = f"{customer_code.upper()}{current_year_str}"
    
    # 統計該客戶當年度已存在的訂單數量
    # 這裡假設 order_model 有 invoice_no 欄位
    existing_count = order_model.query.filter(
        order_model.invoice_no.like(f"{prefix}%")
    ).count()
    
    next_seq = existing_count + 1
    return f"{prefix}{next_seq:05d}"
