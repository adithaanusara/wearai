def format_lkr(amount: int) -> str:
    """Whole rupees as the website shows them: 4450 becomes 'LKR 4,450.00'."""
    return f"LKR {amount:,.2f}"
