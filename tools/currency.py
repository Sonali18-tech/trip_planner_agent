"""ExchangeRate-API wrapper — free tier, needs an email-signup API key.
Get your key at https://www.exchangerate-api.com
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_exchange_rate(from_cur: str, to_cur: str) -> float:
    """Fetch the raw conversion rate once — reuse it for multiple conversions
    instead of hitting the API per amount (keeps you well under free-tier limits)."""
    key = os.getenv("EXCHANGERATE_API_KEY")
    if not key:
        raise EnvironmentError("EXCHANGERATE_API_KEY missing from .env")

    url = f"https://v6.exchangerate-api.com/v6/{key}/pair/{from_cur}/{to_cur}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json().get("conversion_rate", 1.0)


def convert_currency(amount: float, from_cur: str, to_cur: str) -> float:
    rate = get_exchange_rate(from_cur, to_cur)
    return round(amount * rate, 2)


if __name__ == "__main__":
    print(convert_currency(100, "USD", "INR"))
