from decimal import Decimal

from dateutil.parser import parse

from names import ORDER_TYPE_BUY, ORDER_TYPE_SELL
from trading.order import Order
from trading.position import Position
from trading.trade import Trade

BASE_CURRENCY = "baseCurrency1"
CURRENCY = "currency1"
EXCHANGE = "exchange1"
EARLIER_DATE = parse('2017-12-20 22:33:44')
BASIC_DATE = parse('2018-01-03 20:35:48')
LATER_DATE = parse('2018-01-03 21:00:00')

def testProfit(prepareDatabase):
    session = prepareDatabase['session']
    wallet = prepareDatabase['wallet']
    with session.no_autoflush:
        position = Position(wallet, EXCHANGE, CURRENCY, BASE_CURRENCY)
        buy = _createBasicBuyOrder(wallet, position, BASIC_DATE)
        sell = _createProfitableSellOrder(wallet, position, LATER_DATE)
        expectedCurrencyProfitLoss = buy.netCurrency + sell.netCurrency
        expectedBaseProfitLoss = buy.netBase + sell.netBase
        expectedBaseProfitPercent = (abs(sell.netBase) / abs(buy.netBase) - 1) * 100
        position.addOrder(buy)
        position.addOrder(sell)
        session.commit()
        position.close()

    assert position.closedDate == LATER_DATE
    assert position.currencyProfitLoss() == expectedCurrencyProfitLoss
    assert position.baseProfitLoss() == expectedBaseProfitLoss
    assert position.baseProfitPercent() == expectedBaseProfitPercent

def testBuyOnlyProfit(prepareDatabase):
    wallet = prepareDatabase['wallet']
    position = Position(wallet, EXCHANGE, CURRENCY, BASE_CURRENCY)
    buy = _createBasicBuyOrder(wallet, position, BASIC_DATE)
    position.addOrder(buy)

    assert position.baseProfitPercent() == 0

def testSellOnlyProfit(prepareDatabase):
    wallet = prepareDatabase['wallet']
    position = Position(wallet, EXCHANGE, CURRENCY, BASE_CURRENCY)
    sell = _createProfitableSellOrder(wallet, position, LATER_DATE)
    position.addOrder(sell)

    assert position.baseProfitPercent() == 0

def _createBasicPosition(wallet):
    position = Position(wallet, EXCHANGE, CURRENCY, BASE_CURRENCY)
    position.addOrder(_createBasicBuyOrder(wallet, position, BASIC_DATE))
    position.addOrder(_createProfitableSellOrder(wallet, position, LATER_DATE))
    return position

def _createBasicBuyOrder(wallet, position, date):
    order = Order(Trade(
            id='trade1',
            orderId='order1',
            closedDate=date,
            exchange=EXCHANGE,
            orderType=ORDER_TYPE_BUY,
            currency=CURRENCY,
            baseCurrency=BASE_CURRENCY,
            quantity=Decimal('1.0'),
            subtotal=Decimal('50.0'),
            currencyFee=Decimal('0.01'),
            baseFee=Decimal('0.5')))
    order.wallet = wallet
    order.position = position
    return order

def _createProfitableSellOrder(wallet, position, date):
    order = Order(Trade(
            id='trade2',
            orderId='order2',
            closedDate=date,
            exchange=EXCHANGE,
            orderType=ORDER_TYPE_SELL,
            currency=CURRENCY,
            baseCurrency=BASE_CURRENCY,
            quantity=Decimal('0.9'),
            subtotal=Decimal('60.0'),
            currencyFee=Decimal('0.009'),
            baseFee=Decimal('0.6')))
    order.wallet = wallet
    order.position = position
    return order
