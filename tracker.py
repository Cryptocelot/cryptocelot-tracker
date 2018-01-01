"""Main module for the trade tracker program."""

from decimal import getcontext
import sys
import threading

from kivy.app import App
from kivy.clock import mainthread
from kivy.logger import Logger, LOG_LEVELS
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.tabbedpanel import TabbedPanelItem

from keys import KEYS
from model import Base, engine, Session
from parsers.history_parser import HistoryParser
from pollers.bittrex_poller import BittrexPoller
from pollers.gemini_poller import GeminiPoller
from trading.order import Order
from trading.portfolio import Portfolio
from trading.position import Position
from ui.import_dialog import ImportDialog
from ui.order_list_view import OrderListView, NUM_DISPLAY_COLUMNS
from ui.position_list_item import PositionListItem
from ui.position_order_list_dialog import PositionOrderListDialog

NUM_DECIMAL_PLACES = 8

class TrackerApp(App):
    """Main GUI class created on startup. Allows the user to add and interact with order records."""

    HEADER_LABELS = [
            "Closed Date", "Exchange", "Type", "Currency", "Base", "Quantity",
            "Price", "Subtotal", "Net Currency", "Net Base"]

    def __init__(self, **kwargs):
        super(TrackerApp, self).__init__(**kwargs)
        getcontext().prec = NUM_DECIMAL_PLACES
        Base.metadata.create_all(engine)

        self.portfolioId = None
        self.ordersTable = None
        self.openPositionsTable = None
        self.closedPositionsTable = None
        self.closedPositionOffers = []
        self.importDialog = None
        self.importProgressView = None
        self.progressBarLabel = None
        self.progressBar = None

    @mainthread
    def _parseHistory(self, view, path):
        """Start a background thread to process the selected trade history file."""

        view.dismiss()
        if len(path) > 0:
            self.openImportProgressView()
            threading.Thread(
                    target=HistoryParser.parseHistory,
                    kwargs={
                            'filename': path[0],
                            'progressCallback': self.updateProgress,
                            'callback': self.doneParseHistory
                    }).start()

    @mainthread
    def openImportProgressView(self):
        self.importProgressView.open()

    @mainthread
    def updateProgress(self, text=None, value=None, maxValue=None):
        """Called by worker threads to perform a status update in the GUI thread."""

        if text:
            self.progressBarLabel.text = text
        if maxValue and maxValue != self.progressBar.max:
            self.progressBar.max = maxValue
        if value is not None:
            self.progressBar.value = value
        elif not value and not text and not maxValue:
            self.progressBar.value += 1

    @mainthread
    def doneParseHistory(self, orders):
        """Start a background thread to add order objects to the database.

        Called by worker threads after orders have been parsed
        from a history file or retrieved from an exchange.
        """

        threading.Thread(target=self._addParsedOrders, kwargs={
                'orders': orders,
                'progressCallback': self.updateProgress,
                'callback': self.doneAddParsedOrders}).start()

    def _addParsedOrders(self, orders, progressCallback, callback):
        """Add order objects to the database."""

        session = Session()
        self._currentPortfolio(session).addOrders(orders, session, progressCallback, callback)
        session.close()

    @mainthread
    def doneAddParsedOrders(self):
        """Start a background thread to perform post-import tasks.

        Called by worker threads after orders have been added to the database.
        """

        threading.Thread(target=self._updateAllDisplays, kwargs={
                'progressCallback': self.updateProgress,
                'callback': self.doneImport}).start()

    def _updateAllDisplays(self, progressCallback, callback):
        """Refresh all displayed portfolio data in the GUI."""

        self.openImportProgressView()
        self._updateOrderData(progressCallback)
        self._updateOpenPositionData(progressCallback)
        self._updateClosedPositionData(progressCallback)
        if callback:
            callback()

    def _updateOrderData(self, progressCallback):
        progressCallback(text='Updating order list...')
        session = Session()
        # save header
        data = self.ordersTable.data[0:NUM_DISPLAY_COLUMNS]
        orders = self._currentPortfolio(session).getOrders()
        progressCallback(value=0, maxValue=len(orders))
        for o in orders:
            values = [
                    str(o.closedDate).rsplit('.', 1)[0], o.exchange, o.orderType, o.currency,
                    o.baseCurrency, "{:.8f}".format(o.quantity), "{:.8f}".format(o.averagePrice()),
                    "{:.8f}".format(o.subtotal), "{:.8f}".format(o.netCurrency),
                    "{:.8f}".format(o.netBase)]
            data += [{'text': value, 'orderId': o.id} for value in values]
            progressCallback()
        session.close()
        self._updateOrderList(data, progressCallback)

    @mainthread
    def _updateOrderList(self, data, progressCallback):
        self.ordersTable.data = data
        progressCallback(text='Finished updating order list.')

    def _updateOpenPositionData(self, progressCallback):
        session = Session()
        positions = self._currentPortfolio(session).getOpenPositions()
        positionListItems = []
        progressCallback(text='Updating open positions list...', value=0, maxValue=len(positions))
        for position in positions:
            netCurrency = position.currencyProfitLoss()
            netBase = position.baseProfitLoss()
            positionText = "{0} {1}/{2}: {3:+.8f} {2}, {4:+.8f} {1}\n".format(
                    position.exchange, position.baseCurrency,
                    position.currency, netCurrency, netBase)
            if netCurrency > 0:
                if netBase < 0:
                    positionText += "sell above {:.8f} {}".format(
                            abs(netBase / netCurrency), position.baseCurrency)
                else:
                    positionText += "in profit"
            elif netCurrency == 0:
                if netBase < 0:
                    positionText += "in loss"
                elif netBase > 0:
                    positionText += "in profit"
            else:
                if netBase <= 0:
                    positionText += "in loss"
                else:
                    positionText += "buy below {:.8f} {}".format(
                            abs(netBase / netCurrency), position.baseCurrency)
            positionListItems.append(PositionListItem(uiClass=Button, text=positionText, id=position.id))
            progressCallback()
        session.close()
        self._updatePositionList(self.openPositionsTable, positionListItems, progressCallback)

    @mainthread
    def _updatePositionList(self, positionList, positionItems, progressCallback):
        """Refresh a position list in the GUI."""

        positionList.clear_widgets()
        for item in positionItems:
            uiItem = item.uiClass(text=item.text, halign='left', padding=(4, 4), size_hint_y=None)
            if item.uiClass == Button:
                uiItem.positionId = item.id
                uiItem.bind(on_release=self._editPosition)
            uiItem.bind(texture_size=uiItem.setter('size'))
            uiItem.bind(size=uiItem.setter('text_size'))
            positionList.add_widget(uiItem)
        progressCallback(text='Finished updating positions list.')

    def _updateClosedPositionData(self, progressCallback):
        session = Session()
        positions = self._currentPortfolio(session).getClosedPositions(session)
        positionItems = []
        numPositions = positions.count()
        progressCallback(text='Updating closed positions list...', value=0, maxValue=numPositions)
        lastExchange = ""
        lastBaseCurrency = ""
        lastCurrency = ""
        for position in positions:
            if position.exchange != lastExchange:
                positionItems.append(PositionListItem(uiClass=Label, text=position.exchange))
                lastExchange = position.exchange
            if position.baseCurrency != lastBaseCurrency:
                positionItems.append(PositionListItem(uiClass=Label, text="    " + position.baseCurrency))
                lastBaseCurrency = position.baseCurrency
            if position.currency != lastCurrency:
                positionItems.append(PositionListItem(uiClass=Label, text="        " + position.currency))
                lastCurrency = position.currency

            closedDate = position.closedDate
            if not closedDate:
                try:
                    closedDate = (session.query(Order.closedDate)
                            .filter(Order.position == position)
                            .order_by(Order.closedDate.desc())
                            .first()[0])
                    position.closedDate = closedDate
                except TypeError:
                    Logger.error("Position %d has no orders.", position.id)
                    closedDate = "no date"
            netCurrency = position.currencyProfitLoss()
            netBase = position.baseProfitLoss()
            positionText = "{}: {:+.8f} {}, {:+.8f} {} ({:+.2f}%)".format(
                    str(closedDate).rsplit('.')[0], netCurrency, position.currency, netBase,
                    position.baseCurrency, position.baseProfitPercent())
            positionItems.append(PositionListItem(uiClass=Button, text=positionText, id=position.id))
            progressCallback()
        session.commit()
        session.close()
        self._updatePositionList(self.closedPositionsTable, positionItems, progressCallback)

    @mainthread
    def doneImport(self):
        """Start a background thread to calculate positions that can be closed."""

        offerThread = threading.Thread(target=self._createClosedPositionOffers, kwargs={
                'progressCallback': self.updateProgress,
                'callback': self.showNextOffer})
        offerThread.start()

    def _createClosedPositionOffers(self, progressCallback, callback):
        """Calculate positions that can be closed.

        Determine if any consecutive sequence of orders from the beginning
        of the position onwards results in a net currency of zero, indicating
        that profit can be calculated on this group of orders.
        """

        progressCallback(text='Determining positions that can be closed...', value=0, maxValue=100)
        session = Session()
        offers = self._currentPortfolio(session).createClosedPositionOffers()
        for offer in offers:
            position = session.query(Position).get(offer['positionId'])
            ordersToMove = (session.query(Order)
                    .filter(Order.id.in_(offer['orderIds']))
                    .order_by(Order.closedDate).all())
            firstOrder = ordersToMove[0]
            lastOrder = ordersToMove[-1]
            offer['text1'] = "Close zero-net-currency position in {} {}/{} using {} orders?".format(
                    position.exchange, position.baseCurrency,
                    position.currency, len(offer['orderIds']))
            offer['text2'] = "Open {}, close {}, profit {} {}".format(
                    str(firstOrder.closedDate).rsplit('.')[0], lastOrder.closedDate,
                    offer['netBase'], position.baseCurrency)
            self.closedPositionOffers.append(offer)
        session.close()
        progressCallback(text='Done.')
        callback()

    @mainthread
    def showNextOffer(self, view=None, lastPositionId=None, lastOrderIds=None):
        """Display positions that can be closed fully or partially."""

        self.importProgressView.dismiss()
        self.updateProgress(text="")
        if lastPositionId and lastOrderIds:
            threading.Thread(target=self._closePosition, kwargs={
                    'positionId': lastPositionId,
                    'orderIds': lastOrderIds,
                    'callback': self.doneClosePosition}).start()
        if view:
            view.dismiss()
        if len(self.closedPositionOffers) > 0:
            offer = self.closedPositionOffers.pop(0)
            layout = StackLayout()
            layout.add_widget(Label(text=offer['text1'], size_hint=(1, 0.35)))
            layout.add_widget(Label(text=offer['text2'], size_hint=(1, 0.35)))
            layout.add_widget(Button(
                    text="No",
                    on_release=lambda _: self.showNextOffer(view),
                    size_hint=(0.5, 0.3)))
            layout.add_widget(Button(
                    text="Yes",
                    on_release=lambda _: self.showNextOffer(
                            view,
                            offer['positionId'],
                            offer['orderIds']),
                    size_hint=(0.5, 0.3)))
            view = ModalView(auto_dismiss=False, size_hint=(0.8, 0.2))
            view.add_widget(layout)
            view.open()
        else:
            self._updateOpenPositionData(self.updateProgress)
            self._updateClosedPositionData(self.updateProgress)

    def _editPosition(self, instance):
        """Display the order list for a position.

        Selected orders can be used to fully or partially close an open position.
        """

        session = Session()
        data = []
        for col, header in enumerate(self.HEADER_LABELS):
            data += [{'text': header, 'orderId': None, 'col': col}]
        position = session.query(Position).get(instance.positionId)
        for o in position.getOrders():
            values = [
                    str(o.closedDate).rsplit('.')[0], o.exchange, o.orderType, o.currency,
                    o.baseCurrency, "{:.8f}".format(o.quantity), "{:.8f}".format(o.averagePrice()),
                    "{:.8f}".format(o.subtotal), "{:.8f}".format(o.netCurrency),
                    "{:.8f}".format(o.netBase)]
            data += [{'text': value, 'orderId': o.id, 'col': col} for col, value in enumerate(values)]

        view = PositionOrderListDialog(instance.positionId, position.isOpen, data, self._closePositionFromOrderList)
        view.open()
        session.close()

    def _currentPortfolio(self, session):
        """Obtain the most recent portfolio from the database."""

        return session.query(Portfolio).get(self.portfolioId)

    def _closePosition(self, positionId, orderIds, callback):
        """Close the position using the selected orders.

        If not all orders in the position are selected, the selected orders
        will be moved to a new position which is immediately closed.
        """
        session = Session()
        position = session.query(Position).get(positionId)
        ordersToMove = session.query(Order).filter(Order.id.in_(orderIds)).all()
        closingWholePosition = sorted(orderIds) == sorted(position.getOrderIds())
        if closingWholePosition:
            self._currentPortfolio(session).closePosition(position)
        else:
            position = self._currentPortfolio(session).moveOrdersToNewClosedPosition(position, ordersToMove)
        session.commit()
        session.close()

        callback()

    @mainthread
    def doneClosePosition(self):
        """Start a background thread to refresh"""

        threading.Thread(target=self._updateAllDisplays, kwargs={
                'progressCallback': self.updateProgress,
                'callback': self.importProgressView.dismiss}).start()

    def _closePositionFromOrderList(self, button):
        """Start a background thread to close the position."""

        selectedOrderIds = button.orderListView.getSelectedOrderIds()
        if len(selectedOrderIds) > 0:
            threading.Thread(target=self._closePosition, kwargs={
                    'positionId': button.positionId,
                    'orderIds': selectedOrderIds,
                    'callback': self.doneClosePosition}).start()
            button.viewToDismiss.dismiss()

    def _pollBittrex(self, _):
        """Start a background thread to query the Bittrex API for order history."""

        try:
            key = KEYS['bittrex']['key']
            secret = KEYS['bittrex']['secret']
            bittrex = BittrexPoller(key, secret)
            threading.Thread(target=bittrex.getOrders, kwargs={
                    'progressCallback': self.updateProgress,
                    'callback': self.doneParseHistory}).start()
            self.openImportProgressView()
        except:
            Logger.error("Could not refresh from Bittrex. Check keys.py.")

    def _pollGemini(self, _):
        """Start a background thread to query the Gemini API for order history."""

        try:
            key = KEYS['gemini']['key']
            secret = KEYS['gemini']['secret']
            gemini = GeminiPoller(key, secret)
            threading.Thread(target=gemini.getOrders, kwargs={
                    'progressCallback': self.updateProgress,
                    'callback': self.doneParseHistory}).start()
            self.openImportProgressView()
        except:
            Logger.error("Could not refresh from Gemini. Check keys.py.")

    def build(self):
        """Create the main GUI."""

        layout = BoxLayout(orientation='horizontal')
        layout.add_widget(self._createLeftPanel())
        layout.add_widget(self._createMainPanel())

        self._createImportProgressView()

        session = Session()
        if session.query(Portfolio).count() < 1:
            session.add(Portfolio())
            session.commit()
        self.portfolioId = session.query(Portfolio.id).first()
        session.close()

        threading.Thread(target=self._updateAllDisplays, kwargs={
                'progressCallback': self.updateProgress,
                'callback': self.importProgressView.dismiss}).start()

        return layout

    def _createLeftPanel(self):
        """Create the left panel of the main window."""

        self.importDialog = ImportDialog(okCallback=self._parseHistory)

        importButton = Button(text='Import History', size_hint_y=0.1)
        importButton.bind(on_release=self.importDialog.open)

        pollBittrexButton = Button(text='Refresh from Bittrex', size_hint_y=0.1)
        pollBittrexButton.bind(on_release=self._pollBittrex)

        pollGeminiButton = Button(text='Refresh from Gemini', size_hint_y=0.1)
        pollGeminiButton.bind(on_release=self._pollGemini)

        leftPanel = BoxLayout(orientation='vertical', size_hint=(0.2, 1))
        leftPanel.add_widget(importButton)
        leftPanel.add_widget(pollBittrexButton)
        leftPanel.add_widget(pollGeminiButton)
        leftPanel.add_widget(Label(size_hint_y=1))
        return leftPanel

    def _createImportProgressView(self):
        """Create the import progress GUI elements."""

        self.importProgressView = Popup(
                title='Progress',
                auto_dismiss=False,
                size_hint=(None, None),
                size=(350, 150))

        self.progressBarLabel = Label()
        self.progressBar = ProgressBar(max=100)

        progressLayout = BoxLayout(orientation='vertical')
        progressLayout.add_widget(self.progressBarLabel)
        progressLayout.add_widget(self.progressBar)
        progressLayout.add_widget(Button(text='OK', on_release=self.importProgressView.dismiss))

        self.importProgressView.content = progressLayout

    def _createMainPanel(self):
        """Create the tabbed panel making up most of the interface."""

        self.ordersTable = OrderListView()
        data = [{'text': header, 'orderId': None} for header in self.HEADER_LABELS]
        self.ordersTable.data = data

        ordersTab = BoxLayout(orientation='vertical')
        ordersTab.add_widget(self.ordersTable)

        self.openPositionsTable = BoxLayout(orientation='vertical', size_hint=(1, None))
        self.openPositionsTable.bind(minimum_height=self.openPositionsTable.setter('height'))

        openPositionsTab = ScrollView(size_hint=(1, 1))
        openPositionsTab.add_widget(self.openPositionsTable)

        self.closedPositionsTable = BoxLayout(orientation='vertical', size_hint=(1, None))
        self.closedPositionsTable.bind(minimum_height=self.closedPositionsTable.setter('height'))

        closedPositionsTab = ScrollView(size_hint=(1, 1))
        closedPositionsTab.add_widget(self.closedPositionsTable)

        tabbedPanel = TabbedPanel(size_hint=(0.8, 1))
        tabbedPanel.bind(width=lambda obj, w:
                tabbedPanel.setter('tab_width')(obj, w / len(tabbedPanel.tab_list)))
        tabbedPanel.default_tab_text = 'Orders'
        tabbedPanel.default_tab_content = ordersTab
        tabbedPanel.add_widget(TabbedPanelItem(text='Open Positions', content=openPositionsTab))
        tabbedPanel.add_widget(TabbedPanelItem(text='Closed Positions', content=closedPositionsTab))
        return tabbedPanel

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "debug":
            Logger.setLevel(LOG_LEVELS['debug'])
    TrackerApp().run()
