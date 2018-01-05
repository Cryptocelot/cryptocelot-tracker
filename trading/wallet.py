from decimal import Decimal

from kivy.logger import Logger
from sqlalchemy import Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.orm import relationship

from trading.order import Order
from trading.position import Position

# import last so classes are detected for corresponding tables
from model import Base, Session

class Wallet(Base):
    __tablename__ = 'wallets'
    name = Column(String, primary_key=True)
    portfolioId = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    portfolio = relationship("Portfolio", back_populates="wallets")
    balances = Column(PickleType)
    orders = relationship("Order", order_by=Order.closedDate, back_populates="wallet", lazy="dynamic")
    positions = relationship("Position", back_populates="wallet", lazy="dynamic")

    def __init__(self, name, portfolio):
        self.name = name
        self.portfolio = portfolio
        self.balances = {}

    def addOrder(self, order, session=None):
        if not session:
            session = Session()
        # find an open position this order can be put in
        positions = session.query(Position).filter(
                Position.exchange == order.exchange,
                Position.currency == order.currency,
                Position.baseCurrency == order.baseCurrency,
                Position.isOpen == True).all()
        if len(positions) > 1:
            Logger.error(
                    "Multiple open positions in same market. Database constraint violated: %s %s/%s",
                    order.exchange, order.baseCurrency, order.currency)
        elif len(positions) == 1:
            position = positions[0]
        else:
            position = Position(self, order.exchange, order.currency, order.baseCurrency)
            session.add(position)
        # prevent order from being added to session until references
        # to other database objects are finalized
        with session.no_autoflush:
            order.wallet = self
            order.position = position

        if order.currency not in self.balances:
            self.balances[order.currency] = Decimal(0.0)
        if order.baseCurrency not in self.balances:
            self.balances[order.baseCurrency] = Decimal(0.0)

        self.balances[order.currency] += order.netCurrency
        self.balances[order.baseCurrency] += order.netBase

    def getOrders(self):
        return self.orders

    def closePosition(self, position):
        position.close()

    def moveOrdersToNewClosedPosition(self, position, orders):
        newPosition = Position(self, position.exchange, position.currency, position.baseCurrency)
        for order in orders:
            position.removeOrder(order)
            newPosition.addOrder(order)
        newPosition.close()
        self.positions.append(newPosition)
        return newPosition

    def createClosedPositionOffers(self):
        offers = []
        for position in self.getOpenPositions():
            orderIds = []
            netCurrency = 0
            netBase = 0
            for order in position.getOrders():
                orderIds.append(order.id)
                netCurrency += order.netCurrency
                netBase += order.netBase
                # found a sequence of orders from the beginning of the position that
                # yields a net zero currency, not necessarily positive net base
                if netCurrency == 0:
                    offers.append({
                            'positionId': position.id, 'orderIds': orderIds, 'netBase': netBase})
                    orderIds = []
                    netCurrency = 0
                    netBase = 0
        return offers

    def getOpenPositions(self):
        return self.positions.filter(Position.isOpen).all()

    def getClosedPositions(self):
        return self.positions.filter(Position.isOpen == False).all()

    def getPrintableBalances(self):
        return "\n".join([
                "{}: {}"
                .format(currency, quantity) for currency, quantity in self.balances.items()])
