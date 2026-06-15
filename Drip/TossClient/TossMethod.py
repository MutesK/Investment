from json import decoder
import requests 

# 토스증권 OpenApi의 기능들을 단순 호출할수 있게 만든 모듈들 입니다.
# datetime의 예시 = 2026-03-25T09%3A30%3A00%2B09%3A00

# OAuth2 액세스 토큰 발급​
class Auth:
    @classmethod
    def Do(api_key , secret_key):
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

        return r

# 호가 조회
class OrderBook:
    @classmethod
    def Do(access_token, symbol) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/orderbook",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "symbol": symbol
            }
        )

        return r

# 현재가 조회
class Price :
    @classmethod
    def Do(access_token, symbol) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/prices",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "symbols": symbol
            }
        )
        
        return r

# 최근 체결 내역 조회
class Trades : 
    @classmethod
    # 최대 50개
    def Do(access_token, symbol, count) : 
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/trades",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
                "symbol": symbol,
                "count": count
                }
            )

        return r

# 상/하한가 조회
class PriceLimits :
    @classmethod
    def Do(access_token, symbol) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/price-limits",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "symbol": symbol
            }
        )
            
        return r

# 캔들 차트 조회
class CandleChart :
    @classmethod
    # symbol 종목 심볼 
    # interval 봉 단위 , 1m, 1d
    # count 조회 봉수 최대 200
    # before 페이지네이션 상한, 미 지정시 가장 최신 봉 부터 반환, 다음 페이지 요청시 이전 응답의 nextBefore 값을 그대로 전달
    # adjusted 수정 주가 적용 여부
    def Do(access_token, symbol, interval, count, before, adjuested) :
            r = requests.get(
                "https://openapi.tossinvest.com/api/v1/candles",
                headers={
                "Authorization": "Bearer " + access_token
                },
                params={
                "symbol": symbol,
                "interval": interval,
                "count": count,
                "before": before,
                "adjusted": adjuested
                }
            )

            return r

# 종목 정보 조회
class Stocks:
    @classmethod
    def Do(access_token, symbol) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/stocks",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "symbol": symbol
            }
        )
            
        return r

# 매수 유의사항 조회
class TradeWarning :
    @classmethod
    def Do(access_token, symbol) : 
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/stocks/" + symbol + "/warnings",
            headers={
            "Authorization": "Bearer " + access_token
            }
        )
            
        return r

# 환율 조회
class ExchangeRate :
    @classmethod
    def Do(access_token, dateTime, baseCurrency, quoteCurrency) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/exchange-rate",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "dateTime": dateTime,
            "baseCurrency": baseCurrency,
            "quoteCurrency": quoteCurrency
            }
        )

        return r

# 장 운영 정보 조회
class MarketCalender :
    @classmethod
    # country : KR, US
    # dateTime : 2026-03-25
    def Do(access_token, country, dateTime) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/market-calendar/KR",
            headers={
            "Authorization": "Bearer " + access_token
            },
            params={
            "date": dateTime
            }
        )

        return r

# 계좌 목록 조회
class Accounts :
    @classmethod
    def Do(access_token) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/accounts",
            headers={
            "Authorization": "Bearer " + access_token
            }
        )

        return r

# 보유 주식 조회
class Holdings :
    @classmethod
    # X-Tossinvent-Account API 요청시 계좌의 /api/v1/accounts 응답의 accountSeq값을 사용한다.
    def Do(access_token, account_id, symbol) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/holdings",
            headers={
            "X-Tossinvest-Account": account_id,
            "Authorization": "Bearer " + access_token
            },
            params={
                "symbol": symbol
                }
            )

        return r

class Orders :
    @classmethod
    # 국내주식 지정가 매수
    def KRLimitOrder(access_token, account_id, symbol, order_id, side, quantity, price ) :
        r = requests.post(
            "https://openapi.tossinvest.com/api/v1/orders",
            headers={
            "X-Tossinvest-Account": account_id,
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            },
            json={
            "clientOrderId": order_id,
            "symbol": symbol,
            "side": side,
            "orderType": "LIMIT",
            "quantity": quantity,
            "price": price
            }
        )

        return r
    
    # 해외주식 소수점 시장가 매수 (금액)
    @classmethod
    def USFractionalMarketOrder(access_token, account_id, symbol, side, amount ) :
        r = requests.post(
                "https://openapi.tossinvest.com/api/v1/orders",
                headers={
                "X-Tossinvest-Account":  account_id,
                "Content-Type": "application/json",
                "Authorization": "Bearer " + access_token
                },
                json={
                "symbol": symbol,
                "side": side,
                "orderType": "MARKET",
                "orderAmount": amount
                }
            )

        return r
    
    # 해외주식 종가 지정가 매수 ( LOC = LIMIT + CLS )
    @classmethod
    def USLimitOnCloseOrder(access_token, account_id, symbol, side, quantity, price) :
        r= requests.post(
            "https://openapi.tossinvest.com/api/v1/orders",
            headers={
            "X-Tossinvest-Account": account_id,
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            },
            json={
            "symbol": symbol,
            "side": side,
            "orderType": "LIMIT",
            "timeInForce": "CLS",
            "quantity": quantity,
            "price": price
            }
        )

        return r

class OrderModify : 
    @classmethod
    def KRModify(access_token, account_id, order_id, quantity, price) :
        r = requests.post(
            "https://openapi.tossinvest.com/api/v1/orders/" + order_id + "/modify",
            headers={
            "X-Tossinvest-Account": account_id,
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            },
            json={
            "orderType": "LIMIT",
            "quantity": quantity,
            "price": price
            }
        )

        return r
    
    @classmethod
    def USModify(access_token, account_id, order_id, price ) :
        r = requests.post(
            "https://openapi.tossinvest.com/api/v1/orders/",order_id ,"/modify",
            headers={
            "X-Tossinvest-Account": account_id,
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            },
            json={
            "orderType": "LIMIT",
            "price": price
            }
        )

        return r

class CancleOrder :
    @classmethod
    def Do(access_token, account_id, order_id) :
        r = requests.post(
            "https://openapi.tossinvest.com/api/v1/orders/0d5QIHjmtksbsmM-hBRAgP-ExI8iodGm9fAR5txelPfnMM8XQ_swoJdwL5RpGWMo/cancel",
            headers={
            "X-Tossinvest-Account": account_id,
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token
            },
            json={}
        )
                
        return r

class OrderHistory:
    @classmethod
    def Do(access_token, account_id, status, symbol, start_time, end_time, limit=100) :
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/orders",
            headers={
            "X-Tossinvest-Account": account_id,
            "Authorization": "Bearer " + access_token
            },
            params={
            "status": status,
            "symbol": symbol,
            "from": start_time,
            "to": end_time,
            "cursor": "",
            "limit": limit
            }
        )

        return r

class QueryOrderInfo :
    @classmethod
    def Do(access_token, account_id, order_id) : 
        r = requests.get(
            "https://openapi.tossinvest.com/api/v1/orders/" + order_id,
            headers={
            "X-Tossinvest-Account": account_id,
            "Authorization": "Bearer " + access_token
            }
        )

        return r
                
