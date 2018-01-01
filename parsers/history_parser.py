from kivy.logger import Logger

from trading.order import Order

class HistoryParser():

    @staticmethod
    def parseHistory(filename, progressCallback, callback):
        f = open(filename)
        header = f.readline().strip()
        f.close()

        parser = HistoryParser.detectParser(header)
        if parser:
            try:
                orders = parser.parseHistory(filename, progressCallback)
                progressCallback(text="Done parsing history.")
                callback(orders)
            except Exception as e:
                Logger.error("Error parsing history file: %s", e)
        else:
            Logger.warning("Unsupported history file with header: %s", header)
            progressCallback(text="Unsupported history file.")

    @staticmethod
    def ordersFromTrades(trades):
        orders = {}
        for trade in trades:
            if trade.orderId not in orders:
                orders[trade.orderId] = Order()
            orders[trade.orderId].addTrade(trade)
        return orders.values()

    @staticmethod
    def detectParser(header):
        from parsers.bittrex_parser import BittrexParser
        from parsers.kraken_parser import KrakenParser
        from parsers.poloniex_parser import PoloniexParser
        PARSERS = (BittrexParser, KrakenParser, PoloniexParser)

        for parser in PARSERS:
            if header in parser.HEADERS:
                return parser
        return None
