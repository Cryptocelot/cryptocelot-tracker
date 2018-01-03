from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from model import Base
from names import ORDER_TYPE_BUY, ORDER_TYPE_SELL
from trading.order import Order

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    walletName = Column(String, ForeignKey('wallets.name'), nullable=False)
    wallet = relationship("Wallet", back_populates="positions")
    exchange = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    baseCurrency = Column(String, nullable=False)
    isOpen = Column(Boolean, nullable=False)
    closedDate = Column(DateTime)
    orders = relationship("Order", back_populates="position", lazy="dynamic")

    __table_args__ = (Index(
            'single_open_position_per_market',
            exchange,
            currency,
            baseCurrency,
            unique=True,
            sqlite_where=(isOpen == True)),)

    def __init__(self, wallet, exchange, currency, baseCurrency):
        self.wallet = wallet
        self.exchange = exchange
        self.currency = currency
        self.baseCurrency = baseCurrency
        self.isOpen = True

    def getOrders(self):
        return self.orders.order_by(Order.closedDate)

    def getOrderIds(self):
        return [order.id for order in self.orders]

    def addOrder(self, order):
        self.orders.append(order)

    def removeOrder(self, order):
        self.orders.remove(order)

    def currencyProfitLoss(self):
        return sum([order.netCurrency for order in self.orders])

    def baseProfitLoss(self):
        return sum([order.netBase for order in self.orders])

    def baseProfitPercent(self):
        absoluteBuys = 0
        absoluteSells = 0
        for order in self.orders:
            if order.orderType == ORDER_TYPE_BUY:
                absoluteBuys += abs(order.netBase)
            elif order.orderType == ORDER_TYPE_SELL:
                absoluteSells += abs(order.netBase)
        if absoluteBuys == 0 or absoluteSells == 0:
            return 0
        else:
            return (absoluteSells / absoluteBuys - 1) * 100

    def close(self):
        self.isOpen = False
        self.closedDate = self.orders.order_by(Order.closedDate.desc()).first().closedDate

    def __str__(self):
        if self.orders.count() > 0:
            openedDate = self.orders[0].closedDate
            closedDate = self.orders[-1].closedDate
        else:
            openedDate = "never"
            closedDate = "never"
        return "{} {}/{} opened {}, last order {}, net currency {}, net base {}".format(
                self.exchange, self.baseCurrency, self.currency, openedDate, closedDate,
                self.currencyProfitLoss(), self.baseProfitLoss())
