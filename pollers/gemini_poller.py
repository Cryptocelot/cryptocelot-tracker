import base64
from decimal import Decimal
from hashlib import sha384
import hmac
import json
import time

import requests
from kivy.logger import Logger

from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class GeminiPoller():
    BASE_URL = "https://api.gemini.com"
    MAX_TRADES_RETURNED = 500
    METHOD = "GeminiAPI"

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def getOrders(self, progressCallback, callback):
        progressCallback(text="Processing orders...")
        trades = []
        endpoint = "/v1/mytrades"
        markets = [
                {'baseCurrency': 'USD', 'currency': 'BTC'},
                {'baseCurrency': 'USD', 'currency': 'ETH'},
                {'baseCurrency': 'BTC', 'currency': 'ETH'}
        ]
        for market in markets:
            symbol = (market['currency'] + market['baseCurrency']).lower()
            payload = {
                    'request': endpoint,
                    'nonce': int(time.time() * 1000),
                    'symbol': symbol,
                    'limit_trades': self.MAX_TRADES_RETURNED
            }
            encodedPayload = base64.b64encode(json.dumps(payload).encode())
            signature = hmac.new(self.secret.encode(), encodedPayload, sha384).hexdigest()
            headers = {
                    'Content-Type': "text/plain",
                    'Content-Length': "0",
                    'X-GEMINI-APIKEY': self.key,
                    'X-GEMINI-PAYLOAD': encodedPayload,
                    'X-GEMINI-SIGNATURE': signature,
                    'Cache-Control': "no-cache"
            }
            response = requests.request("POST", self.BASE_URL + endpoint, headers=headers)
            if response.ok:
                records = response.json(parse_float=Decimal)
                progressCallback(text="Processing orders...", value=0, maxValue=len(records))
                for record in records:
                    trade = Trade()
                    Mapper.mapRecordToTrade(record, trade, self.METHOD)
                    trade.subtotal = trade.price * trade.quantity
                    trade.currency = market['currency']
                    trade.baseCurrency = market['baseCurrency']
                    feeCurrency = record['fee_currency']
                    if feeCurrency.upper() == trade.baseCurrency:
                        trade.baseFee = Decimal(record['fee_amount'])
                    elif feeCurrency.upper() == trade.currency:
                        trade.currencyFee = Decimal(record['fee_amount'])
                    else:
                        Logger.warning(
                                "Trade at %s in %s order %s had invalid"
                                " currency %s for fee amount.",
                                trade.closedDate, trade.exchange, trade.orderId, feeCurrency)
                    trade.recalculateNetAmounts()
                    trades.append(trade)
                    progressCallback()
            else:
                Logger.error("Problem retrieving orders from Gemini. The reply was: %s", response)
            progressCallback(text="Done retrieving orders.")
        callback(HistoryParser.ordersFromTrades(trades))
