from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from model import Base, Session
from trading.order import Order
from trading.position import Position
from trading.wallet import Wallet

class Portfolio(Base):
    __tablename__ = 'portfolios'

    id = Column(Integer, primary_key=True)
    wallets = relationship("Wallet", back_populates="portfolio", lazy="dynamic")

    def addOrders(self, orders, session, progressCallback, callback):
        progressCallback(text="Adding orders to portfolio...", value=0, maxValue=len(orders))
        for order in orders:
            if order.exchange not in [wallet.name for wallet in self.wallets]:
                wallet = Wallet(order.exchange)
                session.add(wallet)
                self.wallets.append(wallet)
            else:
                wallet = self.wallets.filter(Wallet.name == order.exchange, Wallet.portfolio == self).first()
            existingOrder = session.query(Order).get(order.id)
            if existingOrder:
                # incoming order is newer
                if not order == existingOrder:
                    existingOrder.replaceTotals(order)
            else:
                wallet.addOrder(order, session)
            progressCallback()
        progressCallback(text="Committing changes to database")
        session.commit()
        progressCallback(text="Done adding orders to database")
        callback()

    def getOrders(self):
        orders = []
        for wallet in self.wallets:
            orders += wallet.getOrders()
        orders.sort(key=lambda order: order.closedDate, reverse=True)
        return orders

    def getWallets(self):
        return self.wallets

    def getBalances(self):
        out = ""
        for wallet in self.wallets:
            out += "{}:\n{}".format(wallet.name, wallet.getPrintableBalances()) + "\n"
        return out

    def getOpenPositions(self):
        session = Session()
        positions = []
        for wallet in self.wallets:
            positions += wallet.getOpenPositions()
        return positions

    def getClosedPositions(self, session):
        return (session.query(Position)
                .filter(
                        Position.wallet.has(Wallet.portfolio == self),
                        Position.isOpen == False)
                .order_by(
                        Position.exchange.asc(),
                        Position.baseCurrency.asc(),
                        Position.currency.asc(),
                        Position.closedDate.desc()
                ))

    def closePosition(self, position):
        for wallet in self.wallets:
            if position in wallet.getOpenPositions():
                wallet.closePosition(position)
                return

    def createClosedPositionOffers(self):
        offers = []
        for wallet in self.wallets:
            offers += wallet.createClosedPositionOffers()
        return offers

    def moveOrdersToNewClosedPosition(self, position, orders):
        return position.wallet.moveOrdersToNewClosedPosition(position, orders)
