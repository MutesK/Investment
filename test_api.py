import requests
import json

url = "http://127.0.0.1:5001/backtest/run/dca"
data = {
    "assets": [
        {"ticker": "QLD", "initial": 10000000, "monthly": 600000},
        {"ticker": "USD", "initial": 5000000, "monthly": 300000}
    ],
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "investment_day": 1
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    res_json = response.json()
    print("Summary:", res_json['summary'])
    # Print first few data points of the chart to see if it's linear
    x = res_json['chart']['data'][0]['x'][:5]
    y = res_json['chart']['data'][0]['y'][:5]
    print("First 5 points (X):", x)
    print("First 5 points (Y):", y)
else:
    print(response.text)
