from bittrex.bittrex import Bittrex
from kivy.logger import Logger

from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class BittrexPoller():
    METHOD = "BittrexAPI"

    def __init__(self, key, secret):
        self.bittrex = Bittrex(key, secret)

    def getOrders(self, progressCallback, callback):
        progressCallback(text="Processing orders...")
        trades = []
        reply = self.bittrex.get_order_history()
        if reply['success']:
            orderRecords = reply['result']
            progressCallback(text="Processing orders...", value=0, maxValue=len(orderRecords))
            for record in orderRecords:
                trade = Trade()
                Mapper.mapRecordToTrade(record, trade, self.METHOD)
                trade.recalculateNetAmounts()
                trades.append(trade)
                progressCallback()
            progressCallback(text="Done retrieving orders.")
        else:
            Logger.error("Problem retrieving orders from Bittrex. The reply was: %s", reply)
        callback(HistoryParser.ordersFromTrades(trades))
