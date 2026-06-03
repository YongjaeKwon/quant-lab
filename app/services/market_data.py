from math import sin


def generate_demo_prices(days: int = 120) -> list[float]:
    prices: list[float] = []
    price = 100.0
    for day in range(days):
        trend = 0.12 if day < days * 0.55 else -0.04
        wave = sin(day / 5) * 0.7
        price = max(20.0, price + trend + wave * 0.1)
        prices.append(round(price, 2))
    return prices
