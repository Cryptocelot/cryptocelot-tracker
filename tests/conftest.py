import pytest

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from model import Base
# import all entities so they are known to the ORM
from trading.order import Order
from trading.portfolio import Portfolio
from trading.trade import Trade
from trading.wallet import Wallet

@pytest.fixture(autouse=True)
def prepareDatabase(request):
    engine = create_engine('sqlite://', echo=False)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = Session()
    with session.no_autoflush:
        portfolio = Portfolio()
        wallet = Wallet('wallet', portfolio)
        session.add(portfolio)
        session.commit()
    return {
            'session': session,
            'wallet': wallet}
