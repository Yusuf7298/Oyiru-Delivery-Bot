from datetime import datetime
def generate_order_number(order_id: int) -> str:
    """
    Generate a unique Oyiru order number.
    Example:
    OYR-20260718-0001
    """
    date = datetime.now().strftime("%Y%m%d")
    return f"OYR-{date}-{order_id:04d}"