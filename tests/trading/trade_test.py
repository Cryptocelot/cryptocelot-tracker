from decimal import Decimal

from names import ORDER_TYPE_BUY, ORDER_TYPE_SELL
from trading.trade import Trade

def testNetAmounts():
    trade = Trade(
            orderType=ORDER_TYPE_BUY,
            quantity=Decimal('1.0'),
            currencyFee=Decimal('0.01'),
            subtotal=Decimal('50.0'),
            baseFee=Decimal('0.5'))

    assert trade.netCurrency == Decimal('0.99')
    assert trade.netBase == Decimal('-50.5')

def testRecalculateOrderAmounts():
    trade = Trade()
    trade.orderType = ORDER_TYPE_BUY
    trade.quantity = Decimal('1.0')
    trade.currencyFee = Decimal('0.01')
    trade.subtotal = Decimal('50.0')
    trade.baseFee = Decimal('0.5')

    assert trade.netCurrency == 0
    assert trade.netBase == 0

    trade.recalculateNetAmounts()
    assert trade.netCurrency == Decimal('0.99')
    assert trade.netBase == Decimal('-50.5')

    trade.orderType = ORDER_TYPE_SELL
    trade.recalculateNetAmounts()
    assert trade.netCurrency == Decimal('-1.01')
    assert trade.netBase == Decimal('49.5')
