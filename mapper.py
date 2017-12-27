from datetime import datetime
from decimal import Decimal
import re

from dateutil.parser import parse

from definition import Definition
from names import ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TYPE_UNKNOWN

def normalizeOrderType(orderType):
    buyStrings = ("limit_buy", "buy")
    sellStrings = ("limit_sell", "sell")
    if orderType.lower() in buyStrings:
        return ORDER_TYPE_BUY
    elif orderType.lower() in sellStrings:
        return ORDER_TYPE_SELL
    else:
        return ORDER_TYPE_UNKNOWN

def normalizeKrakenMarket(market):
    # change e.g. ZUSD to USD, XETH to ETH
    market = re.sub(r'^[XZ]([A-Z]{3})[XZ]([A-Z]{3})$', r'\1\2', market)
    # change to standard representation
    market = market.replace('XBT', 'BTC')
    currency, baseCurrency = market[:len(market)//2], market[len(market)//2:]
    return currency, baseCurrency

def normalizeKrakenDate(date):
    return parse(date[:date.rfind('.')])

class Mapper():
    # map Trade attributes to keys in a record with optional post-processor function
    MAPPINGS = {
            'BittrexAPI': {
                    'orderId': Definition(key='OrderUuid'),
                    'closedDate': Definition(key='Closed', transform=parse),
                    'exchange': Definition(value='Bittrex'),
                    'orderType': Definition(key='OrderType', transform=normalizeOrderType),
                    'currency': Definition(key='Exchange', transform=lambda market: market.split('-')[1]),
                    'baseCurrency': Definition(key='Exchange', transform=lambda market: market.split('-')[0]),
                    'quantity': Definition(key='Quantity'),
                    'price': Definition(key='Limit'),
                    'subtotal': Definition(key='Price'),
                    'currencyFee': Definition(value=Decimal(0.0)),
                    'baseFee': Definition(key='Commission')
            },
            'BittrexCSV': {
                    'orderId': Definition(key=0),
                    'closedDate': Definition(key=8, transform=parse),
                    'exchange': Definition(value='Bittrex'),
                    'orderType': Definition(key=2, transform=normalizeOrderType),
                    'currency': Definition(key=1, transform=lambda market: market.split('-')[1]),
                    'baseCurrency': Definition(key=1, transform=lambda market: market.split('-')[0]),
                    'quantity': Definition(key=3, transform=Decimal),
                    'subtotal': Definition(key=6, transform=Decimal),
                    'currencyFee': Definition(value=Decimal(0.0)),
                    'baseFee': Definition(key=5, transform=Decimal)
            },
            'GeminiAPI': {
                    'id': Definition(key='tid'),
                    'orderId': Definition(key='order_id'),
                    'closedDate': Definition(key='timestamp', transform=datetime.fromtimestamp),
                    'exchange': Definition(value='Gemini'),
                    'orderType': Definition(key='type', transform=normalizeOrderType),
                    'quantity': Definition(key='amount', transform=Decimal),
                    'price': Definition(key='price', transform=Decimal),
                    'currencyFee': Definition(value=Decimal(0.0)),
                    'baseFee': Definition(value=Decimal(0.0)),
            },
            'KrakenCSV': {
                    'id': Definition(key=0),
                    'orderId': Definition(key=1),
                    'closedDate': Definition(key=3, transform=normalizeKrakenDate),
                    'exchange': Definition(value='Kraken'),
                    'orderType': Definition(key=4, transform=normalizeOrderType),
                    'currency': Definition(key=2, transform=lambda market: normalizeKrakenMarket(market)[0]),
                    'baseCurrency': Definition(key=2, transform=lambda market: normalizeKrakenMarket(market)[1]),
                    'quantity': Definition(key=9, transform=Decimal),
                    'price': Definition(key=6, transform=Decimal),
                    'subtotal': Definition(key=7, transform=Decimal),
                    'currencyFee': Definition(value=Decimal(0.0)),
                    'baseFee': Definition(key=8, transform=Decimal)
            },
            'PoloniexCSV': {
                    'orderId': Definition(key=8),
                    'closedDate': Definition(key=0, transform=parse),
                    'exchange': Definition(value='Poloniex'),
                    'orderType': Definition(key=3, transform=normalizeOrderType),
                    'currency': Definition(key=1, transform=lambda market: market.split('/')[0]),
                    'baseCurrency': Definition(key=1, transform=lambda market: market.split('/')[1]),
                    'quantity': Definition(key=5, transform=Decimal),
                    'price': Definition(key=4, transform=Decimal),
                    'subtotal': Definition(key=6, transform=Decimal),
                    'netCurrency': Definition(key=10, transform=Decimal),
                    'netBase': Definition(key=9, transform=Decimal)
            }
    }

    @classmethod
    def mapRecordToTrade(cls, record, trade, mappingKey):
        for attribute, definition in cls.MAPPINGS[mappingKey].items():
            # a specified value overrides the value in the corresponding key or
            # provides a default where the record does not contain this data
            if definition.value is not None:
                setattr(trade, attribute, definition.value)
            elif definition.key is not None:
                setattr(trade, attribute, record[definition.key])

            # post-processing is done if needed, e.g. converting a date string to a DateTime
            if definition.transform is not None:
                value = definition.transform(getattr(trade, attribute))
                setattr(trade, attribute, value)
