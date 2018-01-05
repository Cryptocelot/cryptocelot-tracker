from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, String, TypeDecorator, VARCHAR
from sqlalchemy.orm import relationship

from model import Base

# adapted from https://stackoverflow.com/questions/10355767/how-should-i-handle-decimal-in-sqlalchemy-sqlite/10386911#10386911
# store Python Decimal as a String to prevent loss of precision
class SqliteNumeric(TypeDecorator):
    impl = String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(VARCHAR(100))

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return Decimal(value)

class Order(Base):
    __tablename__ = 'orders'

    id = Column(String, primary_key=True)
    walletName = Column(String, ForeignKey('wallets.name'), nullable=False)
    wallet = relationship("Wallet", back_populates="orders")
    positionId = Column(String, ForeignKey('positions.id'), nullable=False)
    position = relationship("Position", back_populates="orders")
    closedDate = Column(DateTime, nullable=False)
    exchange = Column(String, nullable=False)
    orderType = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    baseCurrency = Column(String, nullable=False)
    quantity = Column(SqliteNumeric, nullable=False)
    subtotal = Column(SqliteNumeric, nullable=False)
    currencyFee = Column(SqliteNumeric)
    baseFee = Column(SqliteNumeric)
    netCurrency = Column(SqliteNumeric, nullable=False)
    netBase = Column(SqliteNumeric, nullable=False)

    def __init__(self, trade):
        self.id = trade.orderId
        self.walletName = None
        self.position = None
        self.closedDate = trade.closedDate
        self.exchange = trade.exchange
        self.orderType = trade.orderType
        self.currency = trade.currency
        self.baseCurrency = trade.baseCurrency
        self.quantity = trade.quantity
        self.subtotal = trade.subtotal
        self.currencyFee = trade.currencyFee
        self.baseFee = trade.baseFee
        self.netCurrency = trade.netCurrency
        self.netBase = trade.netBase

    def addTrade(self, trade):
        self.closedDate = max(self.closedDate, trade.closedDate)
        self.quantity += trade.quantity
        self.subtotal += trade.subtotal
        self.currencyFee += trade.currencyFee
        self.baseFee += trade.baseFee
        self.netCurrency += trade.netCurrency
        self.netBase += trade.netBase

    def averagePrice(self):
        return self.subtotal / self.quantity

    def replaceTotals(self, other):
        self.closedDate = other.closedDate
        self.quantity = other.quantity
        self.subtotal = other.subtotal
        self.currencyFee = other.currencyFee
        self.baseFee = other.baseFee
        self.netCurrency = other.netCurrency
        self.netBase = other.netBase

    def __str__(self):
        return "{0} {1} {2} {3} at {4} {5}/{3} for {6} {5} on {7}".format(
                self.closedDate, self.orderType, self.quantity, self.currency, self.averagePrice(),
                self.baseCurrency, abs(self.netBase), self.exchange)

    def __eq__(self, other):
        return (
                self.id == other.id
                and self.exchange == other.exchange
                and self.orderType == other.orderType
                and self.currency == other.currency
                and self.baseCurrency == other.baseCurrency
                and self.closedDate == other.closedDate
                and self.quantity == other.quantity
                and self.subtotal == other.subtotal
                and self.currencyFee == other.currencyFee
                and self.baseFee == other.baseFee
                and self.netCurrency == other.netCurrency
                and self.netBase == other.netBase)
