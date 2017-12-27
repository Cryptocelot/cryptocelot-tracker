from mapper import Mapper
from parsers.history_parser import HistoryParser
from trading.trade import Trade

class KrakenParser(HistoryParser):
    HEADERS = (
            '"txid","ordertxid","pair","time","type","ordertype",'
            '"price","cost","fee","vol","margin","misc","ledgers"',)
    METHOD = "KrakenCSV"

    @staticmethod
    def parseHistory(filename, progressCallback):
        f = open(filename)
        lines = [line.strip() for line in f.readlines()]
        lines.pop(0)

        trades = []
        progressCallback(text="Parsing {}...".format(filename), value=0, maxValue=len(lines))
        for line in lines:
            # remove problematic comma-separated ledger IDs
            line = line[:line.rstrip('"').rfind('"')-1]
            line = line.replace('"', '').split(',')
            trade = Trade()
            Mapper.mapRecordToTrade(line, trade, KrakenParser.METHOD)
            trade.recalculateNetAmounts()
            trades.append(trade)
            progressCallback()
        return HistoryParser.ordersFromTrades(trades)
