from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class KrakenParser(HistoryParser):
    HEADERS = (
            '"txid","ordertxid","pair","time","type","ordertype",'
            '"price","cost","fee","vol","margin","misc","ledgers"',)
    PARSER_TYPE = "KrakenCSV"

    @classmethod
    def parse(cls, lines, progressCallback, callback):
        lines = [line.strip() for line in lines]
        trades = []
        progressCallback(value=0, maxValue=len(lines))
        for line in lines:
            # remove problematic comma-separated ledger IDs
            line = line[:line.rstrip('"').rfind('"')-1]
            line = line.replace('"', '').split(',')
            trade = Trade()
            Mapper.mapRecordToTrade(line, trade, cls.PARSER_TYPE)
            trade.recalculateNetAmounts()
            trades.append(trade)
            progressCallback()
        callback(cls.ordersFromTrades(trades))
