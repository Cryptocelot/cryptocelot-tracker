from names import ORDER_TYPE_BUY, ORDER_TYPE_SELL

class Trade():

    def __init__(
            self, id=None, orderId=None, closedDate=None, exchange=None, orderType=None,
            currency=None, baseCurrency=None, quantity=0, price=0, subtotal=0,
            currencyFee=0, baseFee=0, netCurrency=0, netBase=0):
        self.id = id
        self.orderId = orderId
        self.closedDate = closedDate
        self.exchange = exchange
        self.orderType = orderType
        self.currency = currency
        self.baseCurrency = baseCurrency
        self.quantity = quantity
        self.price = price
        self.subtotal = subtotal
        self.currencyFee = currencyFee
        self.baseFee = baseFee
        self.netCurrency = netCurrency
        self.netBase = netBase

    def recalculateNetAmounts(self):
        if self.orderType == ORDER_TYPE_BUY:
            self.netCurrency = self.quantity - self.currencyFee
            self.netBase = -self.subtotal - self.baseFee
        elif self.orderType == ORDER_TYPE_SELL:
            self.netCurrency = -self.quantity - self.currencyFee
            self.netBase = self.subtotal - self.baseFee
