from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from ui.order_list_view import SelectableOrderListView

Builder.load_string('''
<PositionOrderListDialog@Popup>:
    id: view
    title: ''
    content: layout
    auto_dismiss: False
    size_hint: None, None
    size: 700, 400
    BoxLayout:
        id: layout
        orientation: 'vertical'
        size: self.minimum_size
        SelectableOrderListView:
            id: orderListView
        BoxLayout:
            id: buttonLayout
            orientation: 'horizontal'
            size_hint: 1, None
            size: self.minimum_size
            Button:
                id: cancelButton
                text: 'Cancel'
                on_release: view.dismiss()
                size_hint: 0.5, None
                size: self.texture_size
                padding: 8, 8
''')

class PositionOrderListDialog(Popup):
    def __init__(self, positionId, positionIsOpen, data, okCallback):
        super(PositionOrderListDialog, self).__init__()
        self.ids.orderListView.data = data
        self.ids.orderListView.selectionObservers.append(self)
        if positionIsOpen:
            self.title = 'Select orders to use in closed position.'
            self.closePositionButton = Button(
                    text='New Closed Position from Selected Orders',
                    on_release=okCallback,
                    disabled=True,
                    size_hint=(0.5, None),
                    padding=(8, 8))
            self.closePositionButton.bind(texture_size=self.closePositionButton.setter('size'))
            self.closePositionButton.viewToDismiss = self
            self.closePositionButton.positionId = positionId
            self.closePositionButton.orderListView = self.ids.orderListView
            self.ids.buttonLayout.add_widget(self.closePositionButton)

    def notify(self):
        if hasattr(self, 'closePositionButton'):
            self.closePositionButton.disabled = (len(self.ids.orderListView.getSelectedOrderIds()) < 1)
