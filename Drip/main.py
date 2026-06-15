
# 차후 유저마다 데이터베이스화 작업 필수
api_key = "tsck_live_**"
secret_key = "tssk_live_**"


import requests

# 1. 엑세스 토큰 발급
r = requests.post(
    "https://openapi.tossinvest.com/oauth2/token",
    headers={
      "Content-Type": "application/x-www-form-urlencoded"
    },
    data={
      "grant_type": "client_credentials",
      "client_id": api_key,
      "client_secret": secret_key
    }
)
 

print(r.status_code)
print(r.json())

