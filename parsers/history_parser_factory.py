from parsers.bittrex_parser import BittrexParser
from parsers.kraken_parser import KrakenParser
from parsers.poloniex_parser import PoloniexParser

class HistoryParserFactory():
    PARSERS = (BittrexParser, KrakenParser, PoloniexParser)

    @classmethod
    def detectParser(cls, header):
        for parser in cls.PARSERS:
            if header in parser.HEADERS:
                return parser
        return None
