from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class BittrexParser(HistoryParser):
    HEADERS = (
            'OrderUuid,Exchange,Type,Quantity,Limit,CommissionPaid,Price,Opened,Closed',
            'O\x00r\x00d\x00e\x00r\x00U\x00u\x00i\x00d\x00,\x00E\x00x\x00c\x00h\x00a\x00n\x00g\x00e'
                '\x00,\x00T\x00y\x00p\x00e\x00,\x00Q\x00u\x00a\x00n\x00t\x00i\x00t\x00y\x00,\x00L'
                '\x00i\x00m\x00i\x00t\x00,\x00C\x00o\x00m\x00m\x00i\x00s\x00s\x00i\x00o\x00n\x00P'
                '\x00a\x00i\x00d\x00,\x00P\x00r\x00i\x00c\x00e\x00,\x00O\x00p\x00e\x00n\x00e\x00d'
                '\x00,\x00C\x00l\x00o\x00s\x00e\x00d\x00'
    )
    PARSER_TYPE = "BittrexCSV"

    @classmethod
    def parse(cls, lines, progressCallback, callback):
        lines = [line.replace('\x00', '').strip() for line in lines]
        lines = [line for line in lines if line]
        trades = []
        progressCallback(value=0, maxValue=len(lines))
        for line in lines:
            trade = Trade()
            Mapper.mapRecordToTrade(line.split(','), trade, cls.PARSER_TYPE)
            trade.price = trade.subtotal / trade.quantity
            trade.recalculateNetAmounts()
            trades.append(trade)
            progressCallback()
        callback(cls.ordersFromTrades(trades))
