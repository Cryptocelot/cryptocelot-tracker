from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class PoloniexParser(HistoryParser):
    HEADERS = (
            'Date,Market,Category,Type,Price,Amount,Total,Fee,Order Number,'
            'Base Total Less Fee,Quote Total Less Fee',)
    PARSER_TYPE = "PoloniexCSV"

    @classmethod
    def parse(cls, lines, progressCallback, callback):
        lines = [line.strip() for line in lines]
        trades = []
        progressCallback(value=0, maxValue=len(lines))
        for line in lines:
            trade = Trade()
            Mapper.mapRecordToTrade(line.split(','), trade, cls.PARSER_TYPE)
            trade.currencyFee = trade.quantity - abs(trade.netCurrency)
            trade.baseFee = trade.subtotal - abs(trade.netBase)
            trades.append(trade)
            progressCallback()
        callback(cls.ordersFromTrades(trades))
