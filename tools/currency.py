"""ExchangeRate-API wrapper — free tier, needs an email-signup API key.
Get your key at https://www.exchangerate-api.com
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def convert_currency(amount: float, from_cur: str, to_cur: str) -> float:
    key = os.getenv("EXCHANGERATE_API_KEY")
    if not key:
        raise EnvironmentError("EXCHANGERATE_API_KEY missing from .env")

    url = f"https://v6.exchangerate-api.com/v6/{key}/pair/{from_cur}/{to_cur}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    rate = r.json().get("conversion_rate", 1.0)
    return round(amount * rate, 2)


if __name__ == "__main__":
    print(convert_currency(100, "USD", "INR"))
