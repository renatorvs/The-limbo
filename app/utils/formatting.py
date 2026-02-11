import locale
from datetime import datetime

# Set locale for currency formatting (example for BRL)
# locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def format_currency(value: float) -> str:
    # return locale.currency(value, grouping=True)
    return f"R$ {value:,.2f}"

def format_date(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y")
