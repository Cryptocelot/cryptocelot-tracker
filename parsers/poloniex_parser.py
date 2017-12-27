from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class PoloniexParser(HistoryParser):
    HEADERS = (
            'Date,Market,Category,Type,Price,Amount,Total,Fee,Order Number,'
            'Base Total Less Fee,Quote Total Less Fee',)
    METHOD = "PoloniexCSV"

    @staticmethod
    def parseHistory(history, progressCallback):
        f = open(history)
        lines = f.readlines()

        trades = []
        progressCallback(text="Parsing {}...".format(history), value=0, maxValue=len(lines))
        for line in lines[1:]:
            line = line.strip().split(',')
            trade = Trade()
            Mapper.mapRecordToTrade(line, trade, PoloniexParser.METHOD)
            trade.currencyFee = trade.quantity - abs(trade.netCurrency)
            trade.baseFee = trade.subtotal - abs(trade.netBase)
            trades.append(trade)
            progressCallback()
        return HistoryParser.ordersFromTrades(trades)
