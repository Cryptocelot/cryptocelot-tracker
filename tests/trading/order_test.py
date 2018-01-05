from decimal import Decimal

from dateutil.parser import parse

from names import ORDER_TYPE_BUY
from trading.order import Order
from trading.trade import Trade

EARLIER_DATE = parse('2017-12-20 22:33:44')
BASIC_DATE = parse('2018-01-03 20:35:48')
LATER_DATE = parse('2018-01-03 21:00:00')

def testBasicOrder():
    order = _createBasicOrder()
    subtotal = order.subtotal
    quantity = order.quantity

    assert order.averagePrice() == subtotal / quantity

# verify that an order constructed from chronological trades
# takes on the most recent closed date and correct totals
def testSortedMultiTradeOrder():
    order = _createBasicOrder()
    trade = _createBasicTrade(LATER_DATE)
    expectedOrder = _combineOrderWithTrade(order, trade, trade.closedDate)

    order.addTrade(trade)

    assert order == expectedOrder
    assert order.averagePrice() == expectedOrder.subtotal / expectedOrder.quantity

# verify that an order constructed from non-chronological trades
# takes on the most recent closed date and correct totals
def testUnsortedMultiTradeOrder():
    order = _createBasicOrder()
    trade = _createBasicTrade(EARLIER_DATE)
    expectedOrder = _combineOrderWithTrade(order, trade, order.closedDate)

    order.addTrade(trade)

    assert order == expectedOrder
    assert order.averagePrice() == expectedOrder.subtotal / expectedOrder.quantity

def testReplaceTotals():
    order = _createBasicOrder()
    expectedOrder = Order(_createBasicTrade(EARLIER_DATE))

    order.replaceTotals(expectedOrder)

    assert order == expectedOrder

def _createBasicOrder():
    trade = Trade(
            id='trade1',
            orderId='order1',
            closedDate=BASIC_DATE,
            orderType=ORDER_TYPE_BUY,
            quantity=Decimal('1.0'),
            subtotal=Decimal('50.0'),
            currencyFee=Decimal('0.01'),
            baseFee=Decimal('0.5'))
    trade.recalculateNetAmounts()
    return Order(trade)

def _createBasicTrade(date):
    trade = Trade(
            id='trade2',
            orderId='order1',
            closedDate=date,
            orderType=ORDER_TYPE_BUY,
            quantity=Decimal('2.2'),
            subtotal=Decimal('105.0'),
            currencyFee=Decimal('0.022'),
            baseFee=Decimal('1.05'))
    trade.recalculateNetAmounts()
    return trade

def _combineOrderWithTrade(order, trade, dateToKeep):
    return Order(Trade(
            id=trade.id,
            orderId=order.id,
            closedDate=dateToKeep,
            orderType=order.orderType,
            quantity=order.quantity + trade.quantity,
            subtotal=order.subtotal + trade.subtotal,
            currencyFee=order.currencyFee + trade.currencyFee,
            baseFee=order.baseFee + trade.baseFee,
            netCurrency=order.netCurrency + trade.netCurrency,
            netBase=order.netBase + trade.netBase))
