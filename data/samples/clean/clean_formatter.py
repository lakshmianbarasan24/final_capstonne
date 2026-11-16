def format_currency(amount: float, currency_symbol: str = '$') -> str:
    if amount < 0:
        return f'-{currency_symbol}{abs(amount):,.2f}'
    return f'{currency_symbol}{amount:,.2f}'
