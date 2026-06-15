
from TossClient.TossMethod import *


class TossClient :
    def __init__(self , api_key , secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
    
    # 인증 절차
    def auth(self):
        res = Auth.Do(self.api_key, self.secret_key)

        data = res.json()

        if res.status_code != 200:
            print("error : ", data["error"], " ", data["error_description"])
            return 1
        else:
            self.token = {
                "access_token" : data["access_token"],
                "token_type" : data["token_type"],
                "expires_in" : data["expires_in"]
            }
            return 0
        
    # 매수/매도 호가 및 잔량 조회
    def orderbook(self, symbol) :
        res = OrderBook.Do(self.token["access_token"], symbol)

        data = res.json()

        if res.status_code != 200:
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]


    # 현재가 조회
    def price(self, symbol) :
        res = Price.Do(self.token["access_token"], symbol)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]


    # 최근 체결 내역 조회
    def trades(self, symbol, count=50) :
        res = Trades.Do(self.token["access_token", symbol, count])

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]
            

    # 상/하한가 조회
    def price_limit(self, symbol) :
        res = PriceLimits.Do(self.token["access_token"], symbol)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]
        
    
    def ohlcv(self, symbol, interval, count, before, adjusted) :
        res = CandleChart.Do(self.token["access_token"], symbol, interval, count, before, adjusted)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

    def stocks(self, symbol) :
        res = Stocks.Do(self.token["access_token"], symbol)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

    def trade_warning(self, symbol) : 
        res = TradeWarning.Do(self.token["access_token"], symbol)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

    
    def exchange_rate(self, datetime, base, quote) :
        res = ExchangeRate.Do(self.token["access_token"], datetime, base, quote)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

    
    def market_calender(self, country, datetime) :
        res = MarketCalender.Do(self.token["access_token"], country, datetime)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

    def accounts(self) :
        res = Accounts.Do(self.token["access_token"])

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            for account in data["result"] :
                if account["accountType"] == "BROKERAGE" :
                    self.account_seq = account["accountSeq"]

            return data["result"]


    def holdings(self, symbol) :
        if self.account_seq == 0 :
            self.accounts()

        res = Holdings.Do(self.token["access_token"], self.account_seq, symbol)

        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]
    
    def orders(self, order_type, side, symbol, quantity, price) : 
        if order_type == "KR_LIMIT_ORDER" : 
            res = Orders.KRLimitOrder(self.token["access_token"], self.account_seq, symbol, quantity, price)
            data = res.json()

            if res.status_code != 200 :
                print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
            else:
                return data["result"]

        elif order_type == "US_FRAC_ORDER" : 
            res = Orders.USFractionalMarketOrder(self.token["access_tokens"], self.account_seq, symbol, side, quantity)
            data = res.json()

            if res.status_code != 200 :
                print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
            else:
                return data["result"]

        elif order_type == "US_LOC" :
            res = Orders.USLimitOnCloseOrder(self.token["access_token"], self.account_seq, symbol, side, quantity, price)
            data = res.json()

            if res.status_code != 200 :
                print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
            else:
                return data["result"]
            
    def modify_order(self, order_type, order_id, quantity, price  ) :
        if order_type == "KR" :
            res = OrderModify.KRModify(self.token["access_token"], self.account_seq, order_id, quantity, price)
            data = res.json()

            if res.status_code != 200 :
                print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
            else:
                return data["result"]
        
        elif order_type == "US" :
            res = OrderModify.USModify(self.token["access_token"], self.account_seq, order_id, price)
            data = res.json()

            if res.status_code != 200 :
                print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
            else:
                return data["result"]


    def cancle_order(self, order_id) :
        res = CancleOrder.Do(self.token["access_token"], self.account_seq, order_id)
        data = res.json()

        if res.status_code != 200 :
            print("error : ", data["requestId"], ": ", data["code"], " ",  data["message"])
        else:
            return data["result"]

        