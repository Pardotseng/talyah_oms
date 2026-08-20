from decimal import Decimal, ROUND_UP
from datetime import datetime

def talyah_round(value: Decimal) -> int:
    """
    TalYah 專屬五捨六入規則：
    - 0.5（含）以下捨去
    - 0.5 以上進位
    範例：2362.5 -> 2362，2362.51 -> 2363
    """
    integer_part = int(value)
    fractional_part = value - integer_part
    if fractional_part <= Decimal('0.5'):
        return integer_part
    else:
        return int(value.quantize(Decimal('1'), rounding=ROUND_UP))

def generate_invoice_no(customer_code: str, session, order_model) -> str:
    """
    產生訂單編號：{客戶簡碼}{西元年末兩位}{5位流水號}
    例如：MWZX260001
    每個客戶各自獨立起算，每年重新起算 00001
    """
    current_year_str = datetime.now().strftime('%y') # 西元年末兩位，例如 26
    prefix = f"{customer_code.upper()}{current_year_str}"
    
    # 查詢該客戶當年度已存在的訂單數量來決定流水號
    # 假設 invoice_no 以 prefix 開頭
    existing_count = order_model.query.filter(
        order_model.customer_id == customer_code, # 假設以 customer_code 作為關聯
        order_model.invoice_no.like(f"{prefix}%")
    ).count()
    
    next_seq = existing_count + 1
    return f"{prefix}{next_seq:05d}"
