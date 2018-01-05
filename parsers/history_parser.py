from kivy.logger import Logger

from trading.order import Order

class HistoryParser():

    @classmethod
    def parse(cls, lines, progressCallback, callback):
        raise NotImplementedError()

    @staticmethod
    def ordersFromTrades(trades):
        orders = {}
        for trade in trades:
            if trade.orderId not in orders:
                orders[trade.orderId] = Order(trade)
            else:
                orders[trade.orderId].addTrade(trade)
        return orders.values()
